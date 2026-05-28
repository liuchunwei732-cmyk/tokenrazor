"""ParallelEnum 策略测试。"""

from tokenrazor.core.pruner import Pruner


class TestParallelEnum:

    def setup_method(self):
        self.pruner = Pruner(strategies=["parallel_enum"])

    def test_chinese_enum_detected(self):
        """中文方法枚举应被检测到并压缩。"""
        text = """我需要解决这个问题。

方法一：直接计算法。用公式直接代入计算。这个方法比较直接。

方法二：分步求解法。先分解再合并。这个需要更多步骤。

方法三：近似估算法。牺牲精度换速度。但不够精确。

我选择方法一作为最终方案。

答案：42"""
        result = self.pruner.prune(text, strict=True)
        assert result.stats["saved_tokens"] > 0
        assert len(result.removed_spans) > 0
        # 答案应保留
        assert "答案：42" in result.pruned

    def test_english_enum_detected(self):
        """英文枚举也应被检测。"""
        text = """Need to calculate 15 * 12.

Option 1: Multiply directly. 15 * 12 = 180. This is simple.

Option 2: Break down. 15 * 10 = 150, 15 * 2 = 30. Total 180.

Option 3: Use calculator. But that's cheating.

I'll go with option 1.

Answer: 180"""
        result = self.pruner.prune(text, strict=True)
        assert result.stats["saved_tokens"] > 0
        assert "Answer: 180" in result.pruned

    def test_not_enough_enum(self):
        """少于3个枚举项不应触发。"""
        text = """方法一：直接计算。结果是对的。
我选方法一。

答案：OK"""
        result = self.pruner.prune(text)
        # 应该没有压缩（或者极小压缩）
        assert result.stats["saved_percent"] < 50

    def test_parallel_enum_in_cot(self):
        """带 CoT 标签的枚举应在剪枝范围内。"""
        text = """<thinking>
我需要判断哪个方案最优。

方案一：A方案。成本低但风险高。
方案二：B方案。成本适中，风险可控。
方案三：C方案。成本高但最安全。
方案四：D方案。折中方案。

综合考虑，方案二最优。
</thinking>
最终答案：B"""
        result = self.pruner.prune(text, strict=True)
        assert result.stats["saved_tokens"] > 0
        assert "最终答案：B" in result.pruned

    def test_combined_with_filler(self):
        """parallel_enum 应与 filler 协同工作。"""
        pruner = Pruner(strategies=["filler", "parallel_enum"])
        text = """让我思考一下这个问题。

方案一：直接法。效果不错。
方案二：间接法。需要更多时间。
方案三：混合法。综合两者优势。

让我再确认一下，方案三最合适。

答案：混合法"""
        result = pruner.prune(text, strict=True)
        assert result.stats["saved_tokens"] > 0
        assert len(result.removed_spans) > 0
