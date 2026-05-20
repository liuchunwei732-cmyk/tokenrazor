"""Token 计数测试。"""

from tokenrazor.utils.tokenizer import count_tokens


class TestTokenizer:

    def test_empty_string(self):
        assert count_tokens("") == 0

    def test_english_text(self):
        n = count_tokens("Hello, World!")
        assert n > 0
        assert n < 10

    def test_chinese_text(self):
        n = count_tokens("你好，世界！")
        assert n > 0

    def test_long_text(self):
        text = "Hello World " * 100
        n = count_tokens(text)
        assert n > 50

    def test_with_model_specification(self):
        n = count_tokens("Hello", model="gpt-4")
        assert n > 0
