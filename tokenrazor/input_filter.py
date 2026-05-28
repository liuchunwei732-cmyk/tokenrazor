"""终端输出过滤器 — 上游 Token 优化（输入侧）。

自动识别终端输出中的工具链类型，基于项目上下文
智能降噪，保留关键报错，折叠冗余信息。

用法：
    # 从管道读取终端输出
    filtered = TerminalFilter().filter(raw_output)

    # 指定目标工具链
    filtered = TerminalFilter().filter(output, toolchain="npm")

    # 带项目感知
    from tokenrazor.context import detect_project
    ctx = detect_project(".")
    filtered = TerminalFilter(ctx=ctx).filter(output)
"""

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set

from .context import ProjectContext
from .toolchain import (
    CHINESE_ERROR_KEYWORDS,
    TOOLCHAIN_ALIASES,
    ToolchainConfig,
    detect_toolchain,
    get_config,
)

from .utils.tokenizer import count_tokens


@dataclass
class FilterSpan:
    """一次过滤操作的记录。"""
    original: str
    action: str  # "kept" | "folded" | "stripped" | "summarized"
    reason: str = ""
    char_count: int = 0


@dataclass
class FilterResult:
    """过滤结果。"""
    filtered: str
    original: str
    spans: List[FilterSpan] = field(default_factory=list)
    stats: dict = field(default_factory=dict)


class TerminalFilter:
    """终端输出过滤器。

    Args:
        ctx: 项目上下文（可选），提供项目感知的过滤策略
    """

    # 通用的冗余行模式（不依赖特定工具链）
    GENERIC_REDUNDANT = [
        re.compile(r"^\s*$"),                    # 空行
        re.compile(r"^[-=*]{10,}$"),              # 分隔线
        re.compile(r"^\d+\.\d+[ms]*$"),           # 纯时间戳
        re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}"),  # ISO 时间戳
        re.compile(r"^\s{4,}at\s+.*\("),          # Java / JS 堆栈内部
    ]

    def __init__(self, ctx: Optional[ProjectContext] = None):
        self.ctx = ctx

    def filter(
        self,
        output: str,
        toolchain: Optional[str] = None,
        project_type: Optional[str] = None,
    ) -> FilterResult:
        """对终端输出执行过滤。

        Args:
            output: 原始终端输出文本
            toolchain: 指定工具链（自动检测时传 None）
            project_type: 指定项目类型（覆盖自动检测）

        Returns:
            FilterResult
        """
        if not output or not output.strip():
            return FilterResult(
                filtered=output or "",
                original=output or "",
                stats=self._compute_stats(output or "", output or ""),
            )

        # 1. 自动检测工具链
        resolved_toolchain = toolchain or detect_toolchain(output)
        config = get_config(resolved_toolchain) if resolved_toolchain else None

        # 2. 按行过滤
        lines = output.split("\n")
        filtered_lines: List[str] = []
        spans: List[FilterSpan] = []
        node_modules_mode = False

        for line in lines:
            stripped = line.strip()

            # --- 跳过空行和分隔线 ---
            if not stripped:
                continue
            if re.match(r"^[-=*]{10,}$", stripped):
                spans.append(FilterSpan(line, "stripped", "分隔线", len(line)))
                continue

            # --- 智能检测 node_modules 堆栈 ---
            if "node_modules" in line and ("at " in line or "/" in line):
                if not node_modules_mode:
                    # 第一次遇到，折叠为一行摘要
                    filtered_lines.append("  ... (node_modules stack, folded)")
                    node_modules_mode = True
                spans.append(FilterSpan(line, "folded", "node_modules 内部堆栈", len(line)))
                continue
            elif node_modules_mode and not stripped.startswith("Error"):
                node_modules_mode = False

            # --- 工具链规则匹配 ---
            if config:
                action = config.match(stripped)
                if action == "keep":
                    filtered_lines.append(line)
                    spans.append(FilterSpan(line, "kept", f"{config.name} 关键信息", len(line)))
                elif action == "fold":
                    spans.append(FilterSpan(line, "folded", f"{config.name} 冗余信息", len(line)))
                elif action == "strip":
                    spans.append(FilterSpan(line, "stripped", f"{config.name} 啰嗦日志", len(line)))
                elif action == "summarize":
                    spans.append(FilterSpan(line, "summarized", f"{config.name} 摘要信息", len(line)))
                    filtered_lines.append(line)
                else:
                    filtered_lines.append(line)
                    spans.append(FilterSpan(line, "kept", "其他", len(line)))
            else:
                # --- 通用过滤（无工具链匹配时） ---
                # 保留明显是关键信息的行
                if self._is_critical(stripped):
                    filtered_lines.append(line)
                    spans.append(FilterSpan(line, "kept", "关键信息", len(line)))
                elif self._is_redundant(line):
                    spans.append(FilterSpan(line, "folded", "通用冗余", len(line)))
                else:
                    # 保留可疑行（宁可多留，不可误删）
                    filtered_lines.append(line)
                    spans.append(FilterSpan(line, "kept", "未知", len(line)))

        filtered_text = "\n".join(filtered_lines)

        # 3. 计算统计
        stats = self._compute_stats(output, filtered_text, spans)

        return FilterResult(
            filtered=filtered_text,
            original=output,
            spans=spans,
            stats=stats,
        )

    def _is_critical(self, line: str) -> bool:
        """判断一行是否可能是关键信息。"""
        # 错误关键字
        critical_keywords = [
            "error", "Error", "ERROR",
            "ERR!", "failure", "FAILURE",
            "failed", "Failed", "FAILED",
            "exception", "Exception", "EXCEPTION",
            "warning", "WARNING",
            "Module not found", "Cannot find",
            "not found", "Not Found",
            "syntax error", "SyntaxError",
            "TypeError", "ReferenceError",
            "Uncaught", "Unhandled",
            "exit code", "Exit code",
            "killed", "Killed",
            "segmentation", "Segmentation",
            "timeout", "Timeout",
        ]
        for kw in critical_keywords:
            if kw in line:
                return True

        # 中文错误关键词
        for pat in CHINESE_ERROR_KEYWORDS:
            if pat.search(line):
                return True

        return False

    def _is_redundant(self, line: str) -> bool:
        """判断一行是否为通用冗余信息。"""
        for pat in self.GENERIC_REDUNDANT:
            if pat.search(line):
                return True
        return False

    def _compute_stats(self, original: str, filtered: str, spans: Optional[List[FilterSpan]] = None) -> dict:
        """计算过滤统计。"""
        orig_tokens = count_tokens(original)
        filt_tokens = count_tokens(filtered)

        folded_chars = sum(s.char_count for s in (spans or []))
        folded_lines = len([s for s in (spans or []) if s.action != "kept"])

        return {
            "original_chars": len(original),
            "filtered_chars": len(filtered),
            "original_lines": len(original.split("\n")),
            "filtered_lines": len(filtered.split("\n")),
            "original_tokens": orig_tokens,
            "filtered_tokens": filt_tokens,
            "saved_tokens": orig_tokens - filt_tokens,
            "saved_percent": round(100 * (1 - filt_tokens / orig_tokens), 1) if orig_tokens else 0,
            "folded_chars": folded_chars,
            "folded_lines": folded_lines,
        }
