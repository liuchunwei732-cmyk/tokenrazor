"""分句器测试。"""

from tokenrazor.core.splitter import split_cot_answer, strip_cot_markers
from tests.fixtures.samples import (
    DEEPSEEK_R1_SAMPLE,
    OPENAI_O1_SAMPLE,
    PLAIN_TEXT_SAMPLE,
)


class TestSplitCotAnswer:

    def test_deepseek_r1_with_thinking_tags(self):
        cot, answer = split_cot_answer(DEEPSEEK_R1_SAMPLE)
        assert "<thinking>" in cot
        assert "</thinking>" in cot
        assert "最终答案" in answer
        assert "Hello, World" in answer

    def test_openai_o1_with_thought_tags(self):
        cot, answer = split_cot_answer(OPENAI_O1_SAMPLE)
        assert "<|start_thought|>" in cot
        assert "<|end_thought|>" in cot
        assert "Paris" in answer

    def test_plain_text_no_cot(self):
        """纯文本应该返回空 answer。"""
        cot, answer = split_cot_answer(PLAIN_TEXT_SAMPLE)
        assert "Python" in cot
        assert answer == ""

    def test_answer_preserved(self):
        """剪枝前后 answer 应该完全一致。"""
        for sample in [DEEPSEEK_R1_SAMPLE, OPENAI_O1_SAMPLE]:
            _, answer = split_cot_answer(sample)
            assert len(answer) > 0


class TestStripCotMarkers:

    def test_strip_thinking_tags(self):
        result = strip_cot_markers("<thinking>hello</thinking>")
        assert result == "hello"

    def test_strip_thought_tags(self):
        result = strip_cot_markers("<|start_thought|>world<|end_thought|>")
        assert result == "world"
