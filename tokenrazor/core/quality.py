"""质量评估器 — 评估剪枝是否伤及答案。

核心思路：通过检查剪枝前后答案区域的一致性，以及移除内容的置信度，
给出一个 0-100 的安全评分。分数越高表示剪枝越安全。
"""

import re
from typing import List, Optional

from .pruner import PruneResult
from .splitter import split_cot_answer
from .scanner import RedundancyMatch


class QualityScore:
    """单次剪枝的质量评分。"""

    def __init__(self, score: int, verdict: str, details: List[str], safety_margin: int):
        self.score = score        # 0-100
        self.verdict = verdict    # "SAFE" | "CAUTION" | "RISKY"
        self.details = details
        self.safety_margin = safety_margin  # 还能再剪多少 token 而不伤答案

    def __repr__(self):
        return f"QualityScore({self.score}, {self.verdict})"

    def to_dict(self) -> dict:
        return {
            "score": self.score,
            "verdict": self.verdict,
            "details": self.details,
            "safety_margin": self.safety_margin,
        }


class QualityEvaluator:
    """评估剪枝操作的质量。"""

    def evaluate(self, result: PruneResult) -> QualityScore:
        """评估一次剪枝操作。

        评分维度：
        1. 答案完整性 (0-40分)
        2. 移除内容置信度 (0-30分)
        3. 压缩合理性 (0-20分)
        4. 结构完整性 (0-10分)
        """
        details = []
        total = 0

        # 维度1: 答案完整性
        ans_score, ans_detail = self._check_answer_integrity(result)
        total += ans_score
        details.append(ans_detail)

        # 维度2: 移除内容置信度
        conf_score, conf_detail = self._check_removal_confidence(result)
        total += conf_score
        details.append(conf_detail)

        # 维度3: 压缩合理性
        comp_score, comp_detail = self._check_compression_reasonableness(result)
        total += comp_score
        details.append(comp_detail)

        # 维度4: 结构完整性
        struct_score, struct_detail = self._check_structure(result)
        total += struct_score
        details.append(struct_detail)

        # 判定等级
        if total >= 80:
            verdict = "SAFE"
        elif total >= 50:
            verdict = "CAUTION"
        else:
            verdict = "RISKY"

        # 安全边际：还能再剪多少百分比而不伤答案
        safety_margin = self._estimate_safety_margin(result)

        return QualityScore(total, verdict, details, safety_margin)

    def _check_answer_integrity(self, result: PruneResult) -> tuple:
        """检查答案区域是否完整。"""
        if not result.stats.get("saved_tokens", 0):
            return 40, "答案完整性: 40/40 (未执行剪枝，原样保留)"

        # 检查 answer 区块在剪枝前后是否一致
        orig_cot, orig_answer = split_cot_answer(result.original)
        pruned_cot, pruned_answer = split_cot_answer(result.pruned)

        if not orig_answer and not pruned_answer:
            # 无明确答案区 → 安全
            return 35, "答案完整性: 35/40 (无明确答案区，CoT 剪枝不影响回答)"

        if orig_answer and pruned_answer:
            # 有明确答案区 → 检查是否一致
            if orig_answer.strip() == pruned_answer.strip():
                return 40, "答案完整性: 40/40 (答案区域完全一致)"
            elif orig_answer.strip() in pruned_answer.strip():
                return 30, "答案完整性: 30/40 (答案被保留但上下文有变化)"
            else:
                # 答案区被改变 → 严重问题
                return 5, "答案完整性: 5/40 ⚠ 答案区域被修改！"

        return 20, "答案完整性: 20/40 (答案区可能受影响)"

    def _check_removal_confidence(self, result: PruneResult) -> tuple:
        """检查被移除内容的置信度。"""
        if not result.removed_spans:
            return 20, "移除置信度: 20/30 (未移除内容)"

        avg_conf = sum(m.confidence for m in result.removed_spans) / len(result.removed_spans)
        n = len(result.removed_spans)

        if avg_conf >= 0.8:
            score = min(30, int(20 + avg_conf * 10))
            return score, f"移除置信度: {score}/30 (平均 {avg_conf:.0%}, {n} 处高置信移除)"
        elif avg_conf >= 0.6:
            return 22, f"移除置信度: 22/30 (平均 {avg_conf:.0%}, {n} 处中置信移除)"
        else:
            return 10, f"移除置信度: 10/30 (平均 {avg_conf:.0%}, 低置信移除)"

    def _check_compression_reasonableness(self, result: PruneResult) -> tuple:
        """检查压缩率是否合理。"""
        saved = result.stats.get("saved_percent", 0)

        if saved == 0:
            return 15, "压缩合理性: 15/20 (未压缩)"
        elif saved <= 30:
            return 20, f"压缩合理性: 20/20 (适度压缩 {saved}%)"
        elif saved <= 50:
            return 18, f"压缩合理性: 18/20 (较激进压缩 {saved}%)"
        elif saved <= 70:
            return 12, f"压缩合理性: 12/20 ⚠ 激进压缩 {saved}%，建议人工检查"
        else:
            return 5, f"压缩合理性: 5/20 ⚠ 极端压缩 {saved}%，很可能伤到内容"

    def _check_structure(self, result: PruneResult) -> tuple:
        """检查剪枝后文本的结构完整性。"""
        pruned = result.pruned
        issues = []

        # 检查是否留下了空段落
        if re.search(r"\n{3,}", pruned):
            issues.append("连续空行")

        # 检查是否有孤立标点开头
        if re.match(r"^[，。、；：!!,.]+", pruned.lstrip()):
            issues.append("文本以标点开头")

        # 检查括号是否匹配
        for pair in [("(", ")"), ("(", ")"), ("[", "]"), ("{", "}")]:
            if pruned.count(pair[0]) > pruned.count(pair[1]) + 2:
                issues.append(f"括号 {pair[0]}{pair[1]} 不匹配")
                break

        if not issues:
            return 10, "结构完整性: 10/10 (结构完整)"
        elif len(issues) == 1:
            return 7, f"结构完整性: 7/10 ({issues[0]})"
        else:
            return 4, f"结构完整性: 4/10 ({', '.join(issues)})"

    def _estimate_safety_margin(self, result: PruneResult) -> int:
        """估算还能再剪多少百分比。"""
        saved = result.stats.get("saved_percent", 0)
        avg_conf = 0.8

        if result.removed_spans:
            avg_conf = sum(m.confidence for m in result.removed_spans) / len(result.removed_spans)

        if saved == 0:
            return 20  # 还没剪，预估可以再剪 20%
        elif saved < 20:
            return max(0, 20 - saved)
        elif saved < 40:
            return max(0, 10 - (saved - 20) // 2)
        else:
            return 0
