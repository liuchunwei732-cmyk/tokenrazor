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

    # 平行枚举模式（中英文）
    # 检测 "方法一...方法二...方法三..." 这类枚举结构
    PARALLEL_ENUM_LINE = re.compile(
        r"(?i)^[\s]*"
        r"(?:"
        r"(?:方法|方案|方式|思路|途径|option|approach|method|way)"
        r"[\s]?"
        r"[一二三四五六七八九十1234567890、,]+[:：]"
        r"|[一二三四五六七八九十]+\.?[、.]?[\s]?[:：]?"
        r"|(?:option|approach|method|way)\s*[\s1234567890,:：]+"
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

    def scan_all(self, text: str, strategies: List[str] = None) -> List[RedundancyMatch]:
        """对文本执行全部扫描模式。

        Args:
            text: 待扫描文本
            strategies: 启用的策略列表，None 表示全部启用
        """
        matches: List[RedundancyMatch] = []

        if strategies is None or "filler" in strategies:
            matches.extend(self._scan_fillers(text))
        if strategies is None or "dead_end" in strategies:
            matches.extend(self._scan_dead_ends(text))
        if strategies is None or "parallel_enum" in strategies:
            matches.extend(self._scan_parallel_enums(text))

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

    def _scan_parallel_enums(self, text: str) -> List[RedundancyMatch]:
        """检测平行枚举分支并标记为可折叠。

        按行扫描，找到连续枚举条目（至少3个条目），
        标记前 N-1 个条目为冗余，保留最后一个（被选中的）。
        支持多行条目（描述、优缺点等）。
        """
        lines = text.split("\n")
        matches = []

        # 第一步：找出所有枚举头所在行
        enum_indices = []  # list of (line_index, char_start)
        char_offset = 0
        for i, line in enumerate(lines):
            stripped = line.strip()
            if self._enum_marker(stripped):
                enum_indices.append((i, char_offset))
            char_offset += len(line) + 1  # +1 for newline char

        if len(enum_indices) < 3:
            return []

        # 第二步：找连续枚举序列
        # 连续定义：相邻枚举头之间行数 <= 10（允许多行描述）
        sequences = []  # [(start_enum_index, end_enum_index, start_char, end_char)]
        seq_start = 0
        for j in range(1, len(enum_indices)):
            gap_lines = enum_indices[j][0] - enum_indices[j - 1][0]
            if gap_lines > 10:
                # 序列中断
                if j - seq_start >= 3:
                    first = enum_indices[seq_start]
                    last = enum_indices[j - 1]
                    sequences.append((seq_start, j - 1, first[1], last[1]))
                seq_start = j

        # 检查最后一个序列
        if len(enum_indices) - seq_start >= 3:
            first = enum_indices[seq_start]
            last = enum_indices[-1]
            sequences.append((seq_start, len(enum_indices) - 1, first[1], last[1]))

        # 第三步：计算每个枚举块的末尾位置
        for seq_start_idx, seq_end_idx, start_char, _ in sequences:
            last_block_start = enum_indices[seq_end_idx][1]
            last_block_end = (
                enum_indices[seq_end_idx + 1][1] if seq_end_idx + 1 < len(enum_indices)
                else len(text)
            )

            # 标记前 N-1 个枚举块为冗余
            for k in range(seq_start_idx, seq_end_idx):
                block_start = enum_indices[k][1]
                block_end = enum_indices[k + 1][1] if k + 1 < len(enum_indices) else len(text)
                matches.append(RedundancyMatch(
                    block_start, block_end - 1, "parallel_enum", 0.75,
                ))

        return matches

    @staticmethod
    def _enum_marker(line: str) -> bool:
        """判断一行是否包含枚举标记。"""
        # 匹配 "方案一/方法二/option 1" 等（允许在行内任意位置）
        if re.search(
            r"(?i)(?:"
            r"(?:方法|方案|方式|思路|途径|option|approach|method|way)"
            r"[\s]?[一二三四五六七八九十1234567890、,]+[:：]"
            r")",
            line,
        ):
            return True
        # 匹配 "第一，/第二、/第三、" 等（仅行首）
        if re.search(r"^(?:第一|第二|第三|第四)[，,、]", line):
            return True
        # 匹配 "1. 2. 3." 等（仅行首，且后面有空格和中文描述）
        if re.search(r"^[1234567890]+\.\s+[\u4e00-\u9fff]", line):
            return True
        return False

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
