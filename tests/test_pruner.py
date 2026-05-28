"""剪枝器测试。"""

from tokenrazor.core.pruner import Pruner
from tests.fixtures.samples import (
    DEEPSEEK_R1_SAMPLE,
    FILLER_AND_DEADEND_SAMPLE,
    DEAD_END_SAMPLE,
    OPENAI_O1_SAMPLE,
    PLAIN_TEXT_SAMPLE,
)


class TestPruner:

    def setup_method(self):
        self.pruner = Pruner()

    def test_deepseek_r1_pruning(self):
        """对 DeepSeek-R1 输出执行剪枝。"""
        result = self.pruner.prune(DEEPSEEK_R1_SAMPLE)
        assert result.stats["original_tokens"] > 0
        assert result.stats["saved_percent"] >= 0
        # Answer 必须保留
        assert "Hello, World" in result.pruned
        assert "最终答案" in result.pruned

    def test_filler_and_deadend_pruning(self):
        """带填充和死胡同的输出。"""
        result = self.pruner.prune(FILLER_AND_DEADEND_SAMPLE)
        assert result.compression_ratio < 1.0  # 应该有压缩
        assert "391" in result.pruned  # 答案保留

    def test_dead_end_detection(self):
        """死胡同模式应该被检测到并修剪。"""
        result = self.pruner.prune(DEAD_END_SAMPLE)
        assert result.compression_ratio <= 0.95  # 至少剪掉一点
        assert len(result.removed_spans) > 0
        # parallel_enum 也可能合并包含 dead_end 的文本
        # 只要文本被移除了就证明检测生效
        has_dead_or_enum = [
            m for m in result.removed_spans
            if "dead_end" in m.reason or "parallel_enum" in m.reason
        ]
        assert len(has_dead_or_enum) > 0

    def test_strict_mode_preserves_answer(self):
        """严格模式下 answer 必须不变。"""
        result = self.pruner.prune(DEEPSEEK_R1_SAMPLE, strict=True)
        _, original_answer = split_cot_answer_bruteforce(DEEPSEEK_R1_SAMPLE)
        _, pruned_answer = split_cot_answer_bruteforce(result.pruned)
        assert original_answer == pruned_answer

    def test_plain_text_passthrough(self):
        """纯文本应该原样通过。"""
        result = self.pruner.prune(PLAIN_TEXT_SAMPLE)
        assert result.original == result.pruned
        assert result.compression_ratio == 1.0

    def test_filler_strategy_only(self):
        """仅使用 filler 策略。"""
        p = Pruner(strategies=["filler"])
        result = p.prune(FILLER_AND_DEADEND_SAMPLE)
        # 应该只有 filler 类型的移除
        fillers = [m for m in result.removed_spans if "filler" in m.reason]
        non_fillers = [m for m in result.removed_spans if "filler" not in m.reason]
        assert non_fillers == []

    def test_token_counting(self):
        """token 计数应该合理。"""
        result = self.pruner.prune(DEEPSEEK_R1_SAMPLE)
        s = result.stats
        assert s["original_tokens"] > 10  # 至少十几个 token
        assert s["pruned_tokens"] <= s["original_tokens"]
        assert s["saved_tokens"] == s["original_tokens"] - s["pruned_tokens"]


def split_cot_answer_bruteforce(text):
    """简化版分句器，用于测试验证。"""
    from tokenrazor.core.splitter import split_cot_answer
    return split_cot_answer(text)
