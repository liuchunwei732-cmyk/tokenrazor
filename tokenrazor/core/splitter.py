"""将 LLM 输出切分为 CoT 区域和 Answer 区域。"""

import re
from typing import Tuple


# 常见推理模型的 CoT 分界标记
# 使用 re.escape 帮助转义特殊字符，但对中文保持灵活性
COT_BOUNDARIES = [
    # DeepSeek-R1
    (re.compile(r"<thinking>", re.DOTALL), re.compile(r"</thinking>", re.DOTALL)),
    # OpenAI o1 / o3 (逐步推理)
    (re.compile(r"<\|start_thought\|>", re.DOTALL), re.compile(r"<\|end_thought\|>", re.DOTALL)),
    # Claude 思考块
    (re.compile(r"<thinking", re.DOTALL), re.compile(r"</thinking>", re.DOTALL)),
]

# 关键词分界（非成对标记）
KEYWORD_BOUNDARIES = [
    r"\n\n最终答案[：:]",
    r"\n\n答案[：:]",
    r"\n\n因此，",
    r"\n\nFinal Answer[：:]",
    r"\n\nAnswer[：:]",
    r"\n\nTherefore,",
]


def _find_boundary(text: str) -> Tuple[str, str, int, int]:
    """尝试所有分界模式，返回 (cot, answer, cot_end, answer_end)。"""
    # 1) 优先匹配成对标记
    for start_re, end_re in COT_BOUNDARIES:
        s = start_re.search(text)
        if s:
            e = end_re.search(text, s.end())
            if e:
                cot = text[s.start():e.end()].strip()
                answer = text[e.end():].strip()
                return cot, answer, s.start(), e.end()

    # 2) 关键词分界模式
    for pattern in KEYWORD_BOUNDARIES:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            cot = text[: m.start()].strip()
            answer = text[m.start():].strip()
            return cot, answer, m.start(), len(text)

    # 3) 无标记：启发式段落分割
    #   仅当最后一段显著短（<=15%总长）且不包含常见正文特征时，才认为是 answer
    paragraphs = [p for p in text.strip().split("\n\n") if p.strip()]
    if len(paragraphs) >= 3:
        cot_text = "\n\n".join(paragraphs[:-1])
        answer_text = paragraphs[-1]
        total_len = len(cot_text) + len(answer_text)
        ratio = len(answer_text) / max(total_len, 1)
        # 严格启发式：短于总长 15% 且不像是段落开头（无句号/换行续）
        if ratio <= 0.15 and len(answer_text) < 300:
            return cot_text, answer_text, len(cot_text), len(text)

    # 4) 退化为全都丢进 CoT
    return text, "", 0, len(text)


def split_cot_answer(text: str) -> Tuple[str, str]:
    """将 LLM 输出分为 CoT 和 Answer。

    Returns:
        (cot_block, answer_block)
    """
    cot, answer, _, _ = _find_boundary(text)
    return cot.strip(), answer.strip()


def strip_cot_markers(text: str) -> str:
    """去除 CoT 标记标签，保留内容。"""
    text = re.sub(r"</?thinking[^>]*>", "", text, flags=re.DOTALL)
    text = re.sub(r"<\|start_thought\|>|<\|end_thought\|>", "", text)
    return text.strip()
