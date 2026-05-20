"""CoT 冗余模式检测器。"""

import re
from typing import List


class RedundancyMatch:
    """单次冗余匹配。"""
    __slots__ = ("start", "end", "reason", "confidence")

    def __init__(self, start: int, end: int, reason: str, confidence: float):
        self.start = start
        self.end = end
        self.reason = reason
        self.confidence = confidence

    def __repr__(self):
        return f"Redundancy({self.start}:{self.end}, {self.reason}, conf={self.confidence:.2f})"


class Scanner:
    """扫描 CoT 文本中的冗余模式。"""

    # 填充短语模式（中英文）
    # 原则：宁可少杀，不可误杀。只移除确凿的过渡废话。
    FILLER_PHRASES = re.compile(
        r"(?i)(?:"
        r"let me (?:think|consider|check|verify|re-?evaluate) (?:about |on |this |that )?(?:step by step|carefully)?"
        r"|i (?:need to|should|must|will|could|would like to) (?:think about|consider|check|verify|analyze|look at|start by)"
        r"|let's (?:think|consider|work through|break down|go through)"
        r"|ok(?:ay)?,? (?:let|so|here)"
        r"|hmm,? (?:let|that|this)"
        r"|now,? let"
        r"|so,? let"
        r"|actually,? let"
        r"|wait,? let"
        r"|alright,? let"
        r"|as i (?:mentioned|said|noted)"
        # 中文填充
        r"|让我(?:再?[想想看]+|[来再](?:想想|看看|梳理一下|整理一下))"
        r"|首先,?我(?:们)?(?:先)?"
        r"|好了,?我(?:们)?"
        r"|好的,?我(?:们)?"
        r"|嗯,?我"
        r"|等等,?让我"
        r")"
    )

    # 死胡同模式（中英文）
    DEAD_END_PATTERNS = re.compile(
        r"(?i)(?:"
        r"(?:that|this|the (?:above|previous|first)) (?:approach|method|way|path|idea|thought|option|direction) "
        r"(?:doesn't|didn't|won't|wouldn't) (?:work|make sense|fit|apply|help)"
        r"|let me (?:re-?approach|re-?try|re-?start|try again|try a different|take a different)"
        r"|scratch that"
        r"|disregard (?:that|the above|the previous)"
        # 中文死胡同
        r"|(?:方法[一二三四五六七八九十]?|思路[一二三四五六七八九十]?|方案[一二三四五六七八九十]?|方式)"
        r"(?:"
        r"(?:不太|不|并不|可能|也)?(?:可行|适用|正确|合适|好|对|行|妥当)"
        r"|有问题|有局限|有不足|有缺陷"
        r")"
        r"|换个(?:思路|方法|方向|方案)"
        r"|仔细想想,?(?:这个|这种|以上)?(?:方式?|方法|思路|方案)(?:不太|不|可能)?(?:对|妥|好|行|合适)"
        r"|算[了啦],?(?:这个|这条|这种方法|这个方案)?(?:放弃|不行|算了)"
        r")"
    )

    def scan_all(self, text: str) -> List[RedundancyMatch]:
        """对文本执行全部扫描模式。"""
        matches: List[RedundancyMatch] = []

        matches.extend(self._scan_fillers(text))
        matches.extend(self._scan_dead_ends(text))

        # 排序去重
        matches.sort(key=lambda m: m.start)
        return self._deduplicate(matches)

    def _scan_fillers(self, text: str) -> List[RedundancyMatch]:
        matches = []
        for m in self.FILLER_PHRASES.finditer(text):
            matches.append(RedundancyMatch(m.start(), m.end(), "filler", 0.85))
        return matches

    def _scan_dead_ends(self, text: str) -> List[RedundancyMatch]:
        matches = []
        for m in self.DEAD_END_PATTERNS.finditer(text):
            sent_start = text.rfind("\n", 0, m.start())
            if sent_start == -1:
                sent_start = 0
            sent_end = text.find("\n", m.end())
            if sent_end == -1:
                sent_end = len(text)
            matches.append(
                RedundancyMatch(sent_start, sent_end, "dead_end", 0.8)
            )
        return matches

    def _deduplicate(self, matches: List[RedundancyMatch]) -> List[RedundancyMatch]:
        """合并/去重重叠区间。"""
        if not matches:
            return []

        cleaned: List[RedundancyMatch] = [matches[0]]
        for m in matches[1:]:
            prev = cleaned[-1]
            if m.start >= prev.start and m.end <= prev.end:
                continue
            if m.start < prev.end:
                merged = RedundancyMatch(
                    prev.start, max(prev.end, m.end),
                    f"{prev.reason}+{m.reason}",
                    max(prev.confidence, m.confidence),
                )
                cleaned[-1] = merged
            else:
                cleaned.append(m)

        return cleaned
