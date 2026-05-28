"""剪枝报告格式化输出。包含 Token 统计、费用节省一目了然。"""

from typing import Optional

from .pruner import PruneResult
from .pricing import calculate_cost, cost_report, format_cost


class Report:
    """生成人类可读的剪枝报告。"""

    BAR_WIDTH = 40

    @classmethod
    def text(cls, result: PruneResult, show_diff: bool = False,
             model: Optional[str] = None) -> str:
        """生成文本格式报告，包含费用节省。"""
        lines = []
        lines.append("╔════════════════════════════════════════╗")
        lines.append("║        TokenRazor 剪枝报告            ║")
        lines.append("╚════════════════════════════════════════╝")
        lines.append("")

        s = result.stats
        ratio = result.compression_ratio

        # Token 统计
        lines.append(f"  📊 Token 统计")
        lines.append(f"  ┌─────────────────────────────────────┐")
        lines.append(f"  │ 原始 Tokens    {s['original_tokens']:>10}       │")
        lines.append(f"  │ 剪后 Tokens    {s['pruned_tokens']:>10}       │")
        lines.append(f"  │ 节约 Tokens    {s['saved_tokens']:>10}       │")
        lines.append(f"  │ 压缩率         {s['saved_percent']:>9}%       │")
        lines.append(f"  └─────────────────────────────────────┘")
        lines.append("")

        # 可视化进度条
        saved_bar = int(cls.BAR_WIDTH * (1 - ratio))
        used_bar = cls.BAR_WIDTH - saved_bar
        bar = "█" * used_bar + "░" * saved_bar
        lines.append(f"  [{bar}] {s['saved_percent']}% 压缩")
        lines.append("")

        # 费用节省（商业价值核心）
        cost = cost_report(s['original_tokens'], s['pruned_tokens'], model=model)
        lines.append(f"  💰 费用节省（{cost['model']} @ ${cost['price_per_1m']}/1M tokens）")
        lines.append(f"  ┌─────────────────────────────────────┐")
        lines.append(f"  │ 原始费用      {format_cost(cost['original_cost']):>10}        │")
        lines.append(f"  │ 剪后费用      {format_cost(cost['pruned_cost']):>10}        │")
        lines.append(f"  │ 本次节省      {format_cost(cost['saved_cost']):>10}        │")
        lines.append(f"  └─────────────────────────────────────┘")
        lines.append("")

        # 冗余详情
        if result.removed_spans:
            lines.append(f"  移除冗余段: {len(result.removed_spans)} 处")
            for m in result.removed_spans:
                lines.append(f"    · {m.reason:<12} (置信度 {m.confidence:.0%})")
        else:
            lines.append("  未发现显著冗余。")
        lines.append("")

        if show_diff:
            lines.append("─" * 50)
            lines.append("  【原始文本】")
            lines.append(result.original[:500])
            lines.append("")
            lines.append("  【剪后文本】")
            lines.append(result.pruned[:500])
            lines.append("")

        return "\n".join(lines)

    @classmethod
    def markdown(cls, result: PruneResult, model: Optional[str] = None) -> str:
        """生成 Markdown 格式报告。"""
        s = result.stats
        cost = cost_report(s['original_tokens'], s['pruned_tokens'], model=model)
        saved = format_cost(cost['saved_cost'])
        lines = [
            "## TokenRazor 剪枝报告",
            "",
            "| 指标 | 值 |",
            "|---|---|",
            f"| 原始 Tokens | {s['original_tokens']} |",
            f"| 剪后 Tokens | {s['pruned_tokens']} |",
            f"| 节约 Tokens | {s['saved_tokens']} |",
            f"| 压缩率 | {s['saved_percent']}% |",
            f"| 节省费用 | {saved} |",
            "",
            f"共移除 {len(result.removed_spans)} 处冗余。",
            "",
        ]
        return "\n".join(lines)

    @classmethod
    def json(cls, result: PruneResult, model: Optional[str] = None) -> dict:
        """生成 JSON 格式报告，包含费用数据。"""
        cost = cost_report(
            result.stats['original_tokens'],
            result.stats['pruned_tokens'],
            model=model,
        )
        return {
            "compression": result.stats,
            "cost": cost,
            "removed_spans": [
                {
                    "reason": m.reason,
                    "confidence": m.confidence,
                    "start": m.start,
                    "end": m.end,
                }
                for m in result.removed_spans
            ],
            "pruned_text": result.pruned,
            "original_text": result.original,
        }
