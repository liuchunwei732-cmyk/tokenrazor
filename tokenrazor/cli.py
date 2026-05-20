"""TokenRazor 命令行接口。"""

import json
import sys
from typing import Optional

import click

from .core import Pruner, Report
from .utils.tokenizer import count_tokens


@click.group()
@click.version_option(version="0.1.0", prog_name="tokenrazor")
def main():
    """TokenRazor — LLM CoT 逻辑剪枝工具。

    对 AI 推理模型的思维链（Chain of Thought）进行应用层脱水，
    去除冗余、填充和死胡同推理，保留准确答案。
    """


@main.command()
@click.argument("text_file", type=click.Path(exists=True), required=False)
@click.option("-t", "--text", help="直接传入文本")
@click.option("-s", "--strategy", multiple=True,
              type=click.Choice(["filler", "dead_end"]),
              default=["filler", "dead_end"],
              help="剪枝策略（可多次指定）")
@click.option("--no-strict", is_flag=True, help="关闭严格验证模式")
@click.option("--diff", is_flag=True, help="显示剪枝前后对比")
@click.option("--json", "json_output", is_flag=True, help="JSON 格式输出")
@click.option("-o", "--output", type=click.Path(), help="输出到文件")
def prune(text_file, text, strategy, no_strict, diff, json_output, output):
    """对 LLM 输出执行 CoT 剪枝。

    从文件或 --text 参数读取 LLM 原始输出，自动识别 CoT 区域，
    执行指定策略的冗余剪枝，输出压缩后文本和统计报告。
    """
    # 读取输入
    if text:
        content = text
    elif text_file:
        with open(text_file, "r", encoding="utf-8") as f:
            content = f.read()
    else:
        content = sys.stdin.read()
        if not content.strip():
            click.echo("错误：请通过文件、--text 参数或管道提供输入。", err=True)
            sys.exit(1)

    # 执行剪枝
    pruner = Pruner(strategies=list(strategy))
    result = pruner.prune(content, strict=not no_strict)

    # 输出
    if json_output:
        output_data = Report.json(result)
        output_str = json.dumps(output_data, ensure_ascii=False, indent=2)
    else:
        output_str = Report.text(result, show_diff=diff)

    if output:
        with open(output, "w", encoding="utf-8") as f:
            f.write(output_str)
        click.echo(f"结果已写入: {output}")
    else:
        click.echo(output_str)

    # 在非 JSON 模式下额外打印剪后文本
    if not json_output:
        click.echo("")
        click.echo("─" * 50)
        click.echo(result.pruned)


@main.command()
@click.argument("text_file", type=click.Path(exists=True), required=False)
@click.option("-t", "--text", help="直接传入文本")
def tokens(text_file, text):
    """统计文本的 token 数量。"""
    if text:
        content = text
    elif text_file:
        with open(text_file, "r", encoding="utf-8") as f:
            content = f.read()
    else:
        content = sys.stdin.read()

    n = count_tokens(content)
    click.echo(f"Tokens: {n}")


if __name__ == "__main__":
    main()
