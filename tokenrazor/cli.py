"""TokenRazor 命令行接口。

命令：
    prune   — 剪枝 AI 输出（CoT 脱水）
    filter  — 过滤终端输出（输入降噪）
    scan    — 项目感知扫描
    snapshot — 生成项目快照
    tokens  — 统计 Token
"""

import json
import sys
from pathlib import Path
from typing import Optional

import click

from .core import Pruner, Report
from .input_filter import TerminalFilter
from .context import ProjectContext, detect_project
from .utils.tokenizer import count_tokens


@click.group()
@click.version_option(version="0.2.0", prog_name="tokenrazor")
def main():
    """🧹 TokenRazor — AI 编程的上下文智能编排层

    不只省 Token，更让 AI 看懂你的项目。

    命令：
        prune     剪枝 AI 输出（CoT 脱水）
        filter    过滤终端输出（输入降噪）
        scan      项目感知扫描
        snapshot  生成项目快照
        tokens    统计 Token
    """


# ============================================================
# prune — 剪枝 AI 输出
# ============================================================

@main.command()
@click.argument("text_file", type=click.Path(exists=True), required=False)
@click.option("-t", "--text", help="直接传入文本")
@click.option("-s", "--strategy", multiple=True,
              type=click.Choice(["filler", "dead_end", "parallel_enum"]),
              default=["filler", "dead_end", "parallel_enum"],
              help="剪枝策略（可多次指定）")
@click.option("--model", default="gpt-4o",
              help="模型名（用于费用估算，默认 gpt-4o）")
@click.option("--no-strict", is_flag=True, help="关闭严格验证模式")
@click.option("--diff", is_flag=True, help="显示剪枝前后对比")
@click.option("--json", "json_output", is_flag=True, help="JSON 格式输出")
@click.option("-o", "--output", type=click.Path(), help="输出到文件")
def prune(text_file, text, strategy, model, no_strict, diff, json_output, output):
    """对 LLM 输出执行 CoT 剪枝。

    从文件或 --text 参数读取 LLM 原始输出，自动识别 CoT 区域，
    执行指定策略的冗余剪枝，输出压缩后文本和统计报告。
    """
    content = _read_input(text_file, text)
    if content is None:
        return

    pruner = Pruner(strategies=list(strategy))
    result = pruner.prune(content, strict=not no_strict)

    _output_result(result, json_output, output, diff, model=model)


# ============================================================
# filter — 过滤终端输出
# ============================================================

@main.command(name="filter")
@click.argument("log_file", type=click.Path(exists=True), required=False)
@click.option("-t", "--text", help="直接传入文本")
@click.option("-p", "--project", default="auto",
              help="项目类型 (auto / react / vue / springboot / flutter 等)")
@click.option("--toolchain", default=None,
              help="工具链 (npm / maven / docker 等，自动检测时省略)")
@click.option("-s", "--stats", "show_stats", is_flag=True, help="显示过滤统计")
@click.option("--diff", is_flag=True, help="显示过滤前后对比")
@click.option("--json", "json_output", is_flag=True, help="JSON 格式输出")
@click.option("-o", "--output", type=click.Path(), help="输出到文件")
def filter_command(log_file, text, project, toolchain, show_stats, diff, json_output, output):
    """过滤终端输出，去除冗余信息。

    从文件或管道读取终端输出，自动识别工具链和项目类型，
    保留关键报错信息，折叠无关日志。
    """
    content = _read_input(log_file, text)
    if content is None:
        return

    # 项目感知
    ctx = None
    if project and project != "auto":
        ctx = ProjectContext(project_type=project)
    elif project == "auto":
        try:
            ctx = detect_project(".")
        except Exception:
            pass

    filter_ = TerminalFilter(ctx=ctx)
    result = filter_.filter(content, toolchain=toolchain)

    if json_output:
        output_data = {
            "filtered_text": result.filtered,
            "stats": result.stats,
            "spans": [
                {"action": s.action, "reason": s.reason, "chars": s.char_count}
                for s in result.spans
            ],
        }
        output_str = json.dumps(output_data, ensure_ascii=False, indent=2)
    else:
        output_str = result.filtered
        if show_stats:
            s = result.stats
            lines = [
                "",
                "─" * 50,
                f"  【过滤统计】",
                f"  原始: {s['original_lines']} 行 / {s['original_tokens']} tokens",
                f"  过滤后: {s['filtered_lines']} 行 / {s['filtered_tokens']} tokens",
                f"  节约: {s['saved_percent']}% ({s['saved_tokens']} tokens)",
                "─" * 50,
            ]
            output_str += "\n" + "\n".join(lines)

    if output:
        with open(output, "w", encoding="utf-8") as f:
            f.write(output_str)
        click.echo(f"结果已写入: {output}")
    else:
        click.echo(output_str)


# ============================================================
# scan — 项目感知扫描
# ============================================================

@main.command()
@click.argument("project_dir", type=click.Path(exists=True), default=".")
@click.option("--recommend", is_flag=True, help="推荐过滤规则")
@click.option("--json", "json_output", is_flag=True, help="JSON 格式输出")
def scan(project_dir, recommend, json_output):
    """扫描项目，感知项目类型和上下文。

    自动检测项目类型（前端/后端/移动端/运维）、框架、构建工具，
    并推荐忽略/折叠规则。
    """
    ctx = detect_project(project_dir)

    if json_output:
        output_data = {
            "project_type": ctx.project_type,
            "framework": ctx.framework,
            "build_tool": ctx.build_tool,
            "language": ctx.language,
            "root": ctx.root,
            "features": ctx.features,
            "recommended_ignores": ctx.recommended_ignores,
            "recommended_folds": ctx.recommended_folds,
        }
        click.echo(json.dumps(output_data, ensure_ascii=False, indent=2))
    else:
        lines = [
            f"📁 项目扫描: {Path(project_dir).resolve().name}",
            f"",
            f"  类型:     {ctx.project_type}",
            f"  框架:     {ctx.framework}",
            f"  构建工具: {ctx.build_tool}",
            f"  语言:     {ctx.language}",
            f"  特征文件: {', '.join(ctx.features) if ctx.features else '(未检测到)'}",
        ]
        if recommend:
            lines.extend([
                "",
                f"  📋 推荐忽略规则:",
            ])
            for rule in ctx.recommended_ignores:
                lines.append(f"    - {rule}")
            if ctx.recommended_folds:
                lines.extend([
                    "",
                    f"  📂 推荐折叠规则:",
                ])
                for rule in ctx.recommended_folds:
                    lines.append(f"    - {rule}")

        click.echo("\n".join(lines))


# ============================================================
# snapshot — 生成项目快照
# ============================================================

@main.command()
@click.argument("source_dir", type=click.Path(exists=True), default=".")
@click.option("-f", "--format", "output_format", type=click.Choice(["markdown", "json"]),
              default="markdown", help="输出格式")
@click.option("-o", "--output", type=click.Path(), help="输出到文件")
@click.option("--max-depth", type=int, default=3, help="最大目录深度")
def snapshot(source_dir, output_format, output, max_depth):
    """生成项目快照。

    生成项目结构的有序摘要，方便 AI 理解项目上下文。
    """
    ctx = detect_project(source_dir)

    if output_format == "json":
        output_data = {
            "name": Path(source_dir).resolve().name,
            "project_type": ctx.project_type,
            "framework": ctx.framework,
            "build_tool": ctx.build_tool,
            "language": ctx.language,
            "recommended_ignores": ctx.recommended_ignores,
        }
        output_str = json.dumps(output_data, ensure_ascii=False, indent=2)
    else:
        output_str = ctx.generate_snapshot(max_depth=max_depth)

    if output:
        with open(output, "w", encoding="utf-8") as f:
            f.write(output_str)
        click.echo(f"项目快照已写入: {output}")
    else:
        click.echo(output_str)


# ============================================================
# tokens — 统计 Token
# ============================================================

@main.command()
@click.argument("text_file", type=click.Path(exists=True), required=False)
@click.option("-t", "--text", help="直接传入文本")
def tokens(text_file, text):
    """统计文本的 token 数量。"""
    content = _read_input(text_file, text)
    if content is None:
        return

    n = count_tokens(content)
    click.echo(f"Tokens: {n}")


# ============================================================
# 辅助函数
# ============================================================

def _read_input(text_file: Optional[str], text: Optional[str]) -> Optional[str]:
    """读取输入（文件 / --text / 管道）。"""
    if text:
        return text
    if text_file:
        with open(text_file, "r", encoding="utf-8") as f:
            return f.read()
    # 管道
    content = sys.stdin.read()
    if not content.strip():
        click.echo("错误：请通过文件、--text 参数或管道提供输入。", err=True)
        return None
    return content


def _output_result(result, json_output: bool, output: Optional[str], diff: bool,
                     model: Optional[str] = None):
    """输出剪枝结果。"""
    if json_output:
        output_data = Report.json(result, model=model)
        output_str = json.dumps(output_data, ensure_ascii=False, indent=2)
    else:
        output_str = Report.text(result, show_diff=diff, model=model)
        output_str += "\n"
        output_str += "─" * 50
        output_str += "\n"
        output_str += result.pruned

    if output:
        with open(output, "w", encoding="utf-8") as f:
            f.write(output_str)
        click.echo(f"结果已写入: {output}")
    else:
        click.echo(output_str)


if __name__ == "__main__":
    main()
