/// 剪枝引擎 — 编排扫描→剪枝→验证流程

use crate::scanner::{Scanner, RedundancyMatch};
use crate::tokenizer;

/// 剪枝结果
#[derive(Debug, Clone)]
pub struct PruneResult {
    pub original: String,
    pub pruned: String,
    pub removed_spans: Vec<RedundancyMatch>,
    pub original_tokens: u64,
    pub pruned_tokens: u64,
}

impl PruneResult {
    /// 节省的 token 数
    pub fn saved_tokens(&self) -> u64 {
        self.original_tokens.saturating_sub(self.pruned_tokens)
    }

    /// 节省百分比
    pub fn saved_percent(&self) -> f64 {
        if self.original_tokens == 0 {
            return 0.0;
        }
        (1.0 - self.pruned_tokens as f64 / self.original_tokens as f64) * 100.0
    }
}

/// 剪枝器
pub struct Pruner {
    scanner: Scanner,
    strategies: Vec<String>,
}

impl Default for Pruner {
    fn default() -> Self {
        Self::new(&["filler", "dead_end", "parallel_enum"])
    }
}

impl Pruner {
    pub fn new(strategies: &[&str]) -> Self {
        Self {
            scanner: Scanner::new(),
            strategies: strategies.iter().map(|s| s.to_string()).collect(),
        }
    }

    /// 剪枝文本
    pub fn prune(&self, text: &str) -> PruneResult {
        let strategies: Vec<&str> = self.strategies.iter().map(|s| s.as_str()).collect();

        // 先尝试分离 CoT 和 Answer
        let (cot, answer) = self.split_cot_answer(text);

        if cot.is_empty() || self.scanner.scan_all(&cot, &strategies).is_empty() {
            let tok = tokenizer::count_tokens(text);
            return PruneResult {
                original: text.to_string(),
                pruned: text.to_string(),
                removed_spans: vec![],
                original_tokens: tok,
                pruned_tokens: tok,
            };
        }

        // 扫描冗余
        let matches = self.scanner.scan_all(&cot, &strategies);

        if matches.is_empty() {
            let tok = tokenizer::count_tokens(text);
            return PruneResult {
                original: text.to_string(),
                pruned: text.to_string(),
                removed_spans: vec![],
                original_tokens: tok,
                pruned_tokens: tok,
            };
        }

        // 执行剪枝（从后往前删）
        let mut pruned_cot = cot.to_string();
        let mut removed = Vec::new();
        for m in matches.iter().rev() {
            let new_cot = format!("{}{}", &pruned_cot[..m.start], &pruned_cot[m.end..]);
            pruned_cot = new_cot;
            removed.push(m.clone());
        }
        removed.reverse();

        // 清理文本
        pruned_cot = self.clean_text(&pruned_cot);

        // 重建输出
        let pruned_tok = tokenizer::count_tokens(&pruned_cot);
        let pruned = if answer.is_empty() {
            pruned_cot
        } else {
            format!("{}\n\n{}", pruned_cot, answer)
        };

        PruneResult {
            original: text.to_string(),
            pruned,
            removed_spans: removed,
            original_tokens: tokenizer::count_tokens(text),
            pruned_tokens: pruned_tok,
        }
    }

    /// 分离 CoT 和 Answer（简化版）
    fn split_cot_answer(&self, text: &str) -> (String, String) {
        // 尝试匹配 <thinking> 标签
        if let Some(start) = text.find("<thinking>") {
            if let Some(end) = text.find("</thinking>") {
                let cot = text[start..end + 12].to_string();
                let answer = text[end + 12..].trim().to_string();
                return (cot, answer);
            }
        }

        // 尝试匹配答案关键词
        for keyword in &["\n\n最终答案", "\n\n答案", "\n\nAnswer", "\n\nFinal Answer"] {
            if let Some(pos) = text.find(keyword) {
                let cot = text[..pos].to_string();
                let answer = text[pos..].trim().to_string();
                return (cot, answer);
            }
        }

        // 无标记，全当 CoT
        (text.to_string(), String::new())
    }

    /// 清理文本残留
    fn clean_text(&self, text: &str) -> String {
        let text = text.trim_start_matches(|c: char| c == ',' || c == '，' || c == '。' || c == ' ' || c == '\n');
        let text = text.trim();
        // 移除连续空行
        let re = regex::Regex::new(r"\n{3,}").unwrap();
        re.replace_all(text, "\n\n").to_string()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_prune_filler() {
        let p = Pruner::new(&["filler"]);
        let r = p.prune("让我想想。答案：42");
        assert!(r.saved_tokens() > 0 || r.pruned.len() < r.original.len());
    }

    #[test]
    fn test_prune_plain_text() {
        let p = Pruner::new(&["filler"]);
        let r = p.prune("这是正常的回答内容。");
        // 正常内容不应被修剪
        assert_eq!(r.pruned, r.original);
    }

    #[test]
    fn test_prune_with_thinking_tags() {
        let p = Pruner::new(&["filler", "dead_end"]);
        let text = "<thinking>让我想想。方法一不对。答案：42</thinking>\n最终答案：42";
        let r = p.prune(text);
        // 答案应保留
        assert!(r.pruned.contains("最终答案"));
    }

    #[test]
    fn test_prune_empty() {
        let p = Pruner::new(&["filler"]);
        let r = p.prune("");
        assert_eq!(r.pruned, "");
    }
}
