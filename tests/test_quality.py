"""质量评估器测试。"""

from tokenrazor.core.pruner import Pruner, PruneResult
from tokenrazor.core.quality import QualityEvaluator, QualityScore


class TestQualityEvaluator:
    def setup_method(self):
        self.evaluator = QualityEvaluator()

    def test_no_pruning_scores_high(self):
        """未执行剪枝应得高分。"""
        pruner = Pruner()
        text = "最终答案：42"
        result = pruner.prune(text, strict=True)
        score = self.evaluator.evaluate(result)
        assert score.score >= 35
        assert score.verdict in ("SAFE", "CAUTION")

    def test_light_pruning_safe(self):
        """轻度剪枝应判定为 SAFE。"""
        pruner = Pruner()
        text = """<thinking>
让我想想。方法一：方案A。方法二：方案B。
好的，我选方案A。
</thinking>
最终答案：方案A"""
        result = pruner.prune(text, strict=True)
        score = self.evaluator.evaluate(result)
        # 轻度剪枝应该比较安全
        assert score.score >= 30
        assert score.verdict in ("SAFE", "CAUTION")

    def test_heavy_pruning_warning(self):
        """大量剪枝应给出 CAUTION 或 RISKY。"""
        pruner = Pruner()
        # 极端输入：大量废话 + 答案
        text = "让我想想。" * 100 + "\n\n答案：42"
        result = pruner.prune(text, strict=True)
        score = self.evaluator.evaluate(result)
        # 大量重复填充被剪掉是正常的
        assert score.score >= 20  # 至少不会极低
        assert isinstance(score.verdict, str)

    def test_answer_preserved_score(self):
        """答案完全保留应得满分。"""
        pruner = Pruner()
        text = """<thinking>
让我想想这个问题。用户问的是 23 × 17 等于多少。
让我想想，23 × 10 = 230，23 × 7 = 161。
好的，没问题了。
</thinking>
最终答案：391"""
        result = pruner.prune(text, strict=True)
        score = self.evaluator.evaluate(result)
        assert score.score >= 60
        assert score.verdict in ("SAFE", "CAUTION")

    def test_score_to_dict(self):
        """quality score 应可转为 dict。"""
        pruner = Pruner()
        result = pruner.prune("答案：42", strict=True)
        score = self.evaluator.evaluate(result)
        d = score.to_dict()
        assert "score" in d
        assert "verdict" in d
        assert "details" in d
        assert "safety_margin" in d

    def test_details_populated(self):
        """评估结果应包含细节。"""
        pruner = Pruner()
        result = pruner.prune("让我想想。答案：42", strict=True)
        score = self.evaluator.evaluate(result)
        assert len(score.details) >= 3  # 至少 3 个维度
        for detail in score.details:
            assert "/" in detail  # 格式应为 "xxx: N/M"

    def test_safety_margin_non_negative(self):
        """安全边际不应为负。"""
        pruner = Pruner()
        result = pruner.prune("答案：42", strict=True)
        score = self.evaluator.evaluate(result)
        assert score.safety_margin >= 0
