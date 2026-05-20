"""核心剪枝引擎。"""

import re
from typing import List, Optional

from .scanner import RedundancyMatch, Scanner
from .splitter import split_cot_answer, strip_cot_markers


def _clean_text(text: str) -> str:
    """清理剪枝后的文本残留。"""
    # 移除开头的逗号、空格、句号
    text = re.sub(r"^[,，\s。、；;]+", "", text)
    # 移除连续空行
    text = re.sub(r"\n{3,}", "\n\n", text)
    # 清理孤立的标点符号
    text = re.sub(r"[,，]{2,}", "，", text)
    return text.strip()


class PruneResult:
    """一次剪枝操作的结果。"""

    def __init__(
        self,
        original: str,
        pruned: str,
        removed_spans: List[RedundancyMatch],
        stats: dict,
    ):
        self.original = original
        self.pruned = pruned
        self.removed_spans = removed_spans
        self.stats = stats

    @property
    def compression_ratio(self) -> float:
        """压缩率：1.0 = 无压缩，0.5 = 剪掉一半。"""
        orig = self.stats.get("original_tokens", 0)
        pruned = self.stats.get("pruned_tokens", 0)
        if orig == 0:
            return 1.0
        return pruned / orig


class Pruner:
    """CoT 剪枝器。负责编排扫描→剪枝→验证流程。"""

    def __init__(self, strategies: Optional[List[str]] = None):
        self.scanner = Scanner()
        self.strategies = strategies or ["filler", "dead_end"]

    def prune(self, text: str, strict: bool = True) -> PruneResult:
        """对 LLM 输出执行剪枝。

        Args:
            text: LLM 原始输出（含 CoT）
            strict: 严格模式，确保 Answer 部分 100% 不变

        Returns:
            PruneResult
        """
        # 1. 分离 CoT 和 Answer
        cot, answer = split_cot_answer(text)

        if not cot:
            # 无法分离 CoT，保底返回
            return PruneResult(
                original=text,
                pruned=text,
                removed_spans=[],
                stats=self._compute_stats(text, text),
            )

        # 2. 去除 CoT 标记标签，保留内容
        cot_clean = strip_cot_markers(cot)

        # 3. 扫描冗余
        matches = self.scanner.scan_all(cot_clean)

        # 4. 按策略过滤
        matches = [m for m in matches if m.reason.split("+")[0] in self.strategies]

        if not matches:
            return PruneResult(
                original=text,
                pruned=text,
                removed_spans=[],
                stats=self._compute_stats(text, text),
            )

        # 5. 执行剪枝（从后往前删，不影响下标）
        pruned_cot = cot_clean
        removed_spans = []
        for m in reversed(matches):
            pruned_cot = pruned_cot[:m.start] + pruned_cot[m.end:]
            removed_spans.append(m)
        removed_spans.reverse()

        # 6. 清理文本残留
        pruned_cot = _clean_text(pruned_cot)

        # 7. 重建输出
        if answer:
            pruned_text = pruned_cot + "\n\n" + answer
        else:
            pruned_text = pruned_cot

        # 8. 严格模式验证：直接检查 answer 字符串是否完整出现在剪后文本中
        if strict and answer:
            if answer.strip() not in pruned_text:
                # Answer 丢失了，回退到原始
                return PruneResult(
                    original=text,
                    pruned=text,
                    removed_spans=[],
                    stats=self._compute_stats(text, text),
                )

        # 9. 统计
        stats = self._compute_stats(text, pruned_text)

        return PruneResult(
            original=text,
            pruned=pruned_text,
            removed_spans=removed_spans,
            stats=stats,
        )

    def _compute_stats(self, original: str, pruned: str) -> dict:
        from tokenrazor.utils.tokenizer import count_tokens
        orig_tokens = count_tokens(original)
        pruned_tokens = count_tokens(pruned)
        return {
            "original_chars": len(original),
            "pruned_chars": len(pruned),
            "original_tokens": orig_tokens,
            "pruned_tokens": pruned_tokens,
            "saved_tokens": orig_tokens - pruned_tokens,
            "saved_percent": round(100 * (1 - pruned_tokens / orig_tokens), 1) if orig_tokens else 0,
        }
