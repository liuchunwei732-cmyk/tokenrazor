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

from .core import Pruner, Report, cost_report, format_cost
from .input_filter import TerminalFilter
from .context import ProjectContext, detect_project
from .utils.tokenizer import count_tokens


@click.group()
@click.version_option(version="0.5.0", prog_name="tokenrazor")
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


# ============================================================
# demo — 内置演示
# ============================================================

@main.command()
@click.option("--model", default="gpt-4o", help="模型名（用于费用估算）")
def demo(model):
    """运行内置演示，展示 TokenRazor 的实际节省效果。"""
    # 模拟 DeepSeek R1 / Claude 的 verbose CoT 输出
    demo_text = """好的，我来分析这个需求并给出实现方案。

首先让我想想这个功能的核心逻辑是什么。
ok，这个功能需要处理用户上传的 CSV 文件，解析后存入数据库。

让我再梳理一下数据流向。
嗯，用户上传 → 文件校验 → 格式转换 → 数据清洗 → 批量插入 → 结果返回。

好的，现在我来考虑实现细节。首先考虑方案一。

方案一：同步处理。
用户上传后等待处理完成。
优点：实现简单，逻辑清晰。
缺点：大文件会阻塞请求。耗时较长。

好的，再来看方案二：异步处理。
上传后立即返回，后台 Task 处理。
优点：用户体验好，支持大文件。
等等，缺点呢？需要消息队列，实现复杂。

现在考虑方案三：混合方案。
小文件同步，大文件异步。
优点：兼顾简单和体验。
等等让我想想阈值怎么定。嗯，10MB 作为分界比较合理。

让我总结对比一下三个方案。
方案一最简单但阻塞，方案二体验好但复杂，方案三平衡了二者。
好的我选择方案三作为最终方案，因为它平衡了实现成本和用户体验。

让我再想想有没有遗漏的边界情况。
嗯，如果是空文件怎么办？需要校验。
如果 CSV 格式不对呢？需要友好提示。
如果数据库连接失败呢？需要重试机制。等等，重试几次合适？3 次吧。

好的，这些边界都考虑到了。

现在我来实现代码。
先定义文件处理函数，明确输入输出。
然后写上传接口，处理多文件并发。
最后加测试，覆盖边界情况。

等等让我再确认一下库的选择，
使用 Pandas 处理 CSV，
使用 Celery 进行异步处理。
好了开始写代码。
"""

    click.echo()
    click.echo("╔══════════════════════════════════════════════════╗")
    click.echo("║       TokenRazor 实时演示                      ║")
    click.echo("║       模拟 Cursor/Claude Code 真实对话场景      ║")
    click.echo("╚══════════════════════════════════════════════════╝")
    click.echo()

    # 展示原始文本（摘要）
    click.echo("📥 原始 AI 输出（截取前 200 字）：")
    click.echo("─" * 50)
    click.echo(demo_text[:200] + "...")
    click.echo()

    # 执行剪枝
    pruner = Pruner()
    result = pruner.prune(demo_text, strict=True)

    # 展示结果
    click.echo("📤 剪枝后输出：")
    click.echo("─" * 50)
    click.echo(result.pruned[:300])
    click.echo()

    # 展示统计
    stats = result.stats
    cost = cost_report(stats["original_tokens"], stats["pruned_tokens"], model=model)

    click.echo("═" * 50)
    click.echo(f"  📊 本次演示统计")
    click.echo(f"  {'原始 Token':>20}: {stats['original_tokens']}")
    click.echo(f"  {'剪后 Token':>20}: {stats['pruned_tokens']}")
    click.echo(f"  {'节约 Token':>20}: {stats['saved_tokens']}")
    click.echo(f"  {'压缩率':>20}: {stats['saved_percent']}%")
    click.echo(f"  {'本次节省费用':>20}: {format_cost(cost['saved_cost'])}")
    click.echo(f"  {'移除冗余段':>20}: {len(result.removed_spans)} 处")
    click.echo("═" * 50)
    click.echo()
    click.echo("💡 用法: command | tokenrazor prune --model gpt-4o")
    click.echo()


# ============================================================
# integrate — 生成集成脚本
# ============================================================

INTEGRATE_SH = r'''# ═══════════════════════════════════════════════════
# TokenRazor 日常使用集成脚本
# 来源: tokenrazor integrate
# 用法: source ~/.tokenrazor.sh
# ═══════════════════════════════════════════════════

alias rzprune="tokenrazor prune"
alias rzfilter="tokenrazor filter"
alias rztokens="tokenrazor tokens"
alias rzdemo="tokenrazor demo"

# 管道剪枝: pipe AI output through TokenRazor
# 用法: ai_command | rzp
# 例如: cat ai_output.txt | rzp
alias rzp="tokenrazor prune --model gpt-4o"

# 管道过滤: pipe terminal output through TokenRazor
# 用法: make 2>&1 | rzf
alias rzf="tokenrazor filter"

# 带统计的过滤
# 用法: npm run build 2>&1 | rzfs
alias rzfs="tokenrazor filter --stats"

# 打印统计摘要
# 用法: cat file.txt | rzs
alias rzs="tokenrazor tokens"

# ═══════════════════════════════════════════════════
# 高级用法: 结合模型参数
# ═══════════════════════════════════════════════════

# 按 DeepSeek R1 定价统计
# 用法: ai_output | rzp-r1
alias rzp-r1="tokenrazor prune --model deepseek-r1"

# 按 Claude Sonnet 定价统计
# 用法: ai_output | rzp-claude
alias rzp-claude="tokenrazor prune --model claude-3.5-sonnet"
'''


@main.command()
@click.option("--shell", type=click.Choice(["bash", "zsh"]), default="bash",
              help="Shell 类型")
@click.option("-o", "--output", type=click.Path(),
              help="输出到文件（默认打印到终端）")
def integrate(shell, output):
    """生成 shell 集成脚本，方便日常使用。

    输出一组 alias，让 TokenRazor 可以直接在终端里管道使用。
    推荐: tokenrazor integrate -o ~/.tokenrazor.sh
          然后 echo 'source ~/.tokenrazor.sh' >> ~/.zshrc
    """
    content = INTEGRATE_SH

    if output:
        with open(output, "w", encoding="utf-8") as f:
            f.write(content)
        click.echo(f"集成脚本已写入: {output}")
        click.echo(f"请执行: source {output}")
        click.echo(f"或添加到 shell 配置: echo 'source {output}' >> ~/.zshrc")
    else:
        click.echo(content)
        click.echo()
        click.echo("─" * 50)
        click.echo("保存到文件后 source 即可使用:")
        click.echo("  tokenrazor integrate -o ~/.tokenrazor.sh")
        click.echo("  source ~/.tokenrazor.sh")
