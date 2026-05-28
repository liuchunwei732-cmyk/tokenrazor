"""Reporter 报告生成测试。"""

from tokenrazor.core.reporter import Report
from tokenrazor.core.pruner import Pruner


class TestReportText:
    """文本报告格式测试。"""

    def test_text_basic(self):
        """text() 应包含关键字段。"""
        pruner = Pruner(strategies=["filler"])
        result = pruner.prune("让我想想。答案：42", strict=False)
        text = Report.text(result)
        assert "TokenRazor" in text
        assert "Token" in text
        assert "原始" in text or "Original" in text

    def test_text_with_model(self):
        """指定 model 应显示费用。"""
        pruner = Pruner(strategies=["filler"])
        result = pruner.prune("让我想想。方法一。方法二。方法三。选三。答案：C", strict=False)
        text = Report.text(result, model="claude-3.5-sonnet")
        assert "$3.00" in text or "$" in text

    def test_text_with_diff(self):
        """show_diff=True 应显示对比信息。"""
        pruner = Pruner(strategies=["filler"])
        result = pruner.prune("让我想想。答案：42", strict=False)
        text = Report.text(result, show_diff=True)
        assert "让我想想" in text or "diff" in text.lower()

    def test_text_no_pruning(self):
        """无修剪时应显示无冗余提示。"""
        from tokenrazor.core.pruner import PruneResult
        from tokenrazor.core.scanner import RedundancyMatch
        result = PruneResult(
            original="plain text no CoT",
            pruned="plain text no CoT",
            removed_spans=[],
            stats={
                "original_chars": 18,
                "pruned_chars": 18,
                "original_tokens": 8,
                "pruned_tokens": 8,
                "saved_tokens": 0,
                "saved_percent": 0.0,
            },
        )
        text = Report.text(result)
        assert "未发现显著冗余" in text


class TestReportJson:
    """JSON 报告格式测试。"""

    def test_json_basic(self):
        """JSON 应包含所有必要字段。"""
        pruner = Pruner(strategies=["filler"])
        result = pruner.prune("让我想想。答案：42", strict=False)
        data = Report.json(result)
        assert "compression" in data
        assert "pruned_text" in data
        assert "removed_spans" in data
        assert data["compression"]["saved_tokens"] >= 0

    def test_json_with_cost(self):
        """JSON 应包含费用数据。"""
        pruner = Pruner(strategies=["filler"])
        result = pruner.prune("让我想想。方法一。方法二。方法三。选三。答案：最后一个", strict=False)
        data = Report.json(result, model="deepseek-r1")
        assert "cost" in data
        assert "model" in data["cost"]
        assert data["cost"]["model"] == "deepseek-r1"

    def test_json_empty_removed(self):
        """无修剪时 removed_spans 应空。"""
        from tokenrazor.core.pruner import PruneResult
        from tokenrazor.core.scanner import RedundancyMatch
        result = PruneResult(
            original="hello",
            pruned="hello",
            removed_spans=[],
            stats={
                "original_chars": 5,
                "pruned_chars": 5,
                "original_tokens": 2,
                "pruned_tokens": 2,
                "saved_tokens": 0,
                "saved_percent": 0.0,
            },
        )
        data = Report.json(result)
        assert len(data["removed_spans"]) == 0


class TestReportEdgeCases:
    """报告边界情况。"""

    def test_empty_input(self):
        """空输入应正常处理。"""
        from tokenrazor.core.pruner import PruneResult
        from tokenrazor.core.scanner import RedundancyMatch
        result = PruneResult(
            original="",
            pruned="",
            removed_spans=[],
            stats={
                "original_chars": 0,
                "pruned_chars": 0,
                "original_tokens": 0,
                "pruned_tokens": 0,
                "saved_tokens": 0,
                "saved_percent": 0.0,
            },
        )
        text = Report.text(result)
        assert "TokenRazor" in text
        data = Report.json(result)
        assert data["compression"]["original_tokens"] == 0

    def test_high_compression(self):
        """高压缩率应正确显示。"""
        from tokenrazor.core.pruner import PruneResult
        from tokenrazor.core.scanner import RedundancyMatch
        result = PruneResult(
            original="aaa bbb ccc ddd eee fff ggg",
            pruned="aaa",
            removed_spans=[RedundancyMatch(1, 29, "test", 0.9)],
            stats={
                "original_chars": 29,
                "pruned_chars": 3,
                "original_tokens": 7,
                "pruned_tokens": 1,
                "saved_tokens": 6,
                "saved_percent": 85.7,
            },
        )
        text = Report.text(result)
        assert "85.7" in text
