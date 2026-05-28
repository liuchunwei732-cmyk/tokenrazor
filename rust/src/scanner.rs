/// CoT 冗余模式扫描器
///
/// 中文差异化：中英文双语模式全覆盖

use regex::Regex;
use serde::Serialize;

/// 一次冗余匹配
#[derive(Debug, Clone, Serialize)]
pub struct RedundancyMatch {
    pub start: usize,
    pub end: usize,
    pub reason: String,
    pub confidence: f64,
}

impl RedundancyMatch {
    pub fn new(start: usize, end: usize, reason: &str, confidence: f64) -> Self {
        Self { start, end, reason: reason.to_string(), confidence }
    }
}

/// CoT 模式扫描器
pub struct Scanner {
    filler_re: Regex,
    dead_end_re: Regex,
    enum_line_re: Regex,
}

impl Default for Scanner {
    fn default() -> Self {
        Self::new()
    }
}

impl Scanner {
    pub fn new() -> Self {
        // 填充短语（中英文）
        let filler_re = Regex::new(
            r"(?i)(?:let me (?:think|consider|check|verify|re-?evaluate) (?:about |on |this |that )?(?:step by step|carefully)?|i (?:need to|should|must|will|could|would like to) (?:think about|consider|check|verify|analyze|look at|start by)|let's (?:think|consider|work through|break down|go through)|ok(?:ay)?,? (?:let|so|here)|hmm,? (?:let|that|this)|now,? let|so,? let|actually,? let|wait,? let|alright,? let|as i (?:mentioned|said|noted)|让我(?:再?[想想看]+|[来再](?:想想|看看|梳理一下|整理一下))|首先,?我(?:们)?(?:先)?|好了,?我(?:们)?|好的,?我(?:们)?|嗯,?我|等等,?让我)"
        ).expect("filler regex");

        // 死胡同模式（中英文）
        let dead_end_re = Regex::new(
            r"(?i)(?:(?:that|this|the (?:above|previous|first)) (?:approach|method|way|path|idea|thought|option|direction) (?:doesn't|didn't|won't|wouldn't) (?:work|make sense|fit|apply|help)|let me (?:re-?approach|re-?try|re-?start|try again|try a different|take a different)|scratch that|disregard (?:that|the above|the previous)|(?:方法|思路|方案|方式)(?:(?:不太|不|并不|可能|也)?(?:可行|适用|正确|合适|好|对|行|妥当)|有问题|有局限|有不足|有缺陷)|换个(?:思路|方法|方向|方案)|仔细想想,?(?:这个|这种|以上)?(?:方式?|方法|思路|方案)(?:不太|不|可能)?(?:对|妥|好|行|合适)|算[了啦],?(?:这个|这条|这种方法|这个方案)?(?:放弃|不行|算了)|这个方法不行|此路不通)"
        ).expect("dead_end regex");

        // 枚举行检测
        let enum_line_re = Regex::new(
            r"(?i)(?:(?:方法|方案|方式|思路|途径|option|approach|method|way)\s?[一二三四五六七八九十\d、,]+[:：])"
        ).expect("enum_line regex");

        Self { filler_re, dead_end_re, enum_line_re }
    }

    /// 扫描填充短语
    pub fn scan_fillers(&self, text: &str) -> Vec<RedundancyMatch> {
        self.filler_re.find_iter(text)
            .map(|m| RedundancyMatch::new(m.start(), m.end(), "filler", 0.85))
            .collect()
    }

    /// 扫描死胡同
    pub fn scan_dead_ends(&self, text: &str) -> Vec<RedundancyMatch> {
        self.dead_end_re.find_iter(text)
            .map(|m| {
                let sent_start = text[..m.start()].rfind('\n').map(|p| p + 1).unwrap_or(0);
                let sent_end = text[m.end()..].find('\n')
                    .map(|p| m.end() + p)
                    .unwrap_or(text.len());
                RedundancyMatch::new(sent_start, sent_end, "dead_end", 0.80)
            })
            .collect()
    }

    /// 扫描平行枚举
    pub fn scan_parallel_enums(&self, text: &str) -> Vec<RedundancyMatch> {
        let lines: Vec<&str> = text.lines().collect();
        let mut enum_indices: Vec<(usize, usize)> = Vec::new();

        let mut char_offset = 0;
        for (i, line) in lines.iter().enumerate() {
            if self.enum_line_re.is_match(line.trim()) {
                enum_indices.push((i, char_offset));
            }
            char_offset += line.len() + 1;
        }

        if enum_indices.len() < 3 {
            return vec![];
        }

        let mut sequences: Vec<(usize, usize, usize, usize)> = Vec::new();
        let mut seq_start = 0;

        for j in 1..enum_indices.len() {
            let gap = enum_indices[j].0 - enum_indices[j - 1].0;
            if gap > 10 {
                if j - seq_start >= 3 {
                    let first = enum_indices[seq_start];
                    let last = enum_indices[j - 1];
                    sequences.push((seq_start, j - 1, first.1, last.1));
                }
                seq_start = j;
            }
        }
        if enum_indices.len() - seq_start >= 3 {
            let first = enum_indices[seq_start];
            let last = enum_indices[enum_indices.len() - 1];
            sequences.push((seq_start, enum_indices.len() - 1, first.1, last.1));
        }

        let mut matches = Vec::new();
        for (seq_s, seq_e, _, _) in sequences {
            for k in seq_s..seq_e {
                let block_start = enum_indices[k].1;
                let block_end = if k + 1 < enum_indices.len() {
                    enum_indices[k + 1].1
                } else {
                    text.len()
                };
                matches.push(RedundancyMatch::new(
                    block_start, block_end.saturating_sub(1), "parallel_enum", 0.75,
                ));
            }
        }
        matches
    }

    /// 执行全部扫描
    pub fn scan_all(&self, text: &str, strategies: &[&str]) -> Vec<RedundancyMatch> {
        let mut matches = Vec::new();

        if strategies.is_empty() || strategies.contains(&"filler") {
            matches.extend(self.scan_fillers(text));
        }
        if strategies.contains(&"dead_end") {
            matches.extend(self.scan_dead_ends(text));
        }
        if strategies.contains(&"parallel_enum") {
            matches.extend(self.scan_parallel_enums(text));
        }

        matches.sort_by(|a, b| a.start.cmp(&b.start));
        self.deduplicate(&matches)
    }

    fn deduplicate(&self, matches: &[RedundancyMatch]) -> Vec<RedundancyMatch> {
        if matches.is_empty() {
            return vec![];
        }

        let mut cleaned: Vec<RedundancyMatch> = vec![matches[0].clone()];
        for m in matches[1..].iter() {
            let prev = &cleaned[cleaned.len() - 1];
            if m.start >= prev.start && m.end <= prev.end {
                continue;
            }
            if m.start < prev.end {
                cleaned.push(RedundancyMatch::new(
                    prev.start, prev.end.max(m.end),
                    &format!("{}+{}", prev.reason, m.reason),
                    prev.confidence.max(m.confidence),
                ));
            } else {
                cleaned.push(m.clone());
            }
        }
        cleaned
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_scan_fillers_english() {
        let s = Scanner::new();
        let m = s.scan_fillers("Let me think about this step by step.");
        assert!(!m.is_empty());
    }

    #[test]
    fn test_scan_fillers_chinese() {
        let s = Scanner::new();
        let m = s.scan_fillers("让我想想这个问题。");
        assert!(!m.is_empty(), "中文填充应被检测");
    }

    #[test]
    fn test_scan_dead_end_chinese() {
        let s = Scanner::new();
        let text = "这个方法不行。让我换一个思路。";
        let m = s.scan_dead_ends(text);
        assert!(!m.is_empty());
    }

    #[test]
    fn test_scan_parallel_enum() {
        let s = Scanner::new();
        let text = "方案一：A。\n方案二：B。\n方案三：C。\n我选三。";
        let m = s.scan_parallel_enums(text);
        assert!(!m.is_empty());
    }

    #[test]
    fn test_scan_all_returns_matches() {
        let s = Scanner::new();
        let text = "让我想想。方法一。\n方法二。\n方法三。\n方法不行。答案：C";
        let m = s.scan_all(text, &["filler", "dead_end", "parallel_enum"]);
        assert!(!m.is_empty());
    }

    #[test]
    fn test_no_false_positives() {
        let s = Scanner::new();
        let text = "这是正常对话。答案：42。";
        let m = s.scan_all(text, &["filler", "dead_end", "parallel_enum"]);
        assert!(m.len() < 3);
    }
}
