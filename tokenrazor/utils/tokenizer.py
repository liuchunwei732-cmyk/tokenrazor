"""Token 计数工具。

使用 tiktoken 进行计算。支持多种模型编码：
- cl100k_base: GPT-4, GPT-3.5-turbo
- o200k_base: GPT-4o, o1, o3
- 通用兜底: cl100k_base
"""

from typing import Optional

import tiktoken


# 全局缓存，避免重复加载
_ENCODING_CACHE: dict = {}


def get_encoding(model: Optional[str] = None):
    """获取指定模型的 tokenizer 编码。"""
    # 用模型名做缓存键
    cache_key = model or "__default__"
    if cache_key in _ENCODING_CACHE:
        return _ENCODING_CACHE[cache_key]

    encoding_name = None
    if model:
        try:
            encoding_name = tiktoken.encoding_for_model(model)
        except KeyError:
            pass

    if encoding_name is None:
        encoding_name = "cl100k_base"

    # encoding_name 可能是字符串或 Encoding 对象
    if isinstance(encoding_name, str):
        enc = tiktoken.get_encoding(encoding_name)
    else:
        enc = encoding_name

    _ENCODING_CACHE[cache_key] = enc
    return enc


def count_tokens(text: str, model: Optional[str] = None) -> int:
    """统计文本的 token 数。

    Args:
        text: 输入文本
        model: 模型名（可选），影响 tokenizer 选择

    Returns:
        token 数量
    """
    if not text:
        return 0
    enc = get_encoding(model)
    return len(enc.encode(text))
