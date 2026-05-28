/// 报告生成 — 文本和 JSON 格式

use serde::Serialize;

use crate::pruner::PruneResult;
use crate::pricing;

/// 剪枝统计
#[derive(Debug, Clone, Serialize)]
pub struct PruneStats {
    pub original_tokens: u64,
    pub pruned_tokens: u64,
    pub saved_tokens: u64,
    pub saved_percent: f64,
}

/// 费用信息
#[derive(Debug, Clone, Serialize)]
pub struct CostInfo {
    pub original_cost: f64,
    pub pruned_cost: f64,
    pub saved_cost: f64,
    pub saved_percent: f64,
    pub model: String,
    pub price_per_1m: f64,
    pub currency: String,
}

/// JSON 报告
#[derive(Debug, Clone, Serialize)]
pub struct JsonReport {
    pub compression: PruneStats,
    pub cost: CostInfo,
    pub removed_spans: Vec<crate::scanner::RedundancyMatch>,
    pub pruned_text: String,
    pub original_text: String,
}

/// 生成 JSON 格式报告
pub fn json_report(result: &PruneResult, model: &str) -> JsonReport {
    let cost = pricing::cost_report(result.original_tokens, result.pruned_tokens, model);

    JsonReport {
        compression: PruneStats {
            original_tokens: result.original_tokens,
            pruned_tokens: result.pruned_tokens,
            saved_tokens: result.saved_tokens(),
            saved_percent: result.saved_percent(),
        },
        cost: CostInfo {
            original_cost: cost.original_cost,
            pruned_cost: cost.pruned_cost,
            saved_cost: cost.saved_cost,
            saved_percent: cost.saved_percent,
            model: cost.model,
            price_per_1m: cost.price_per_1m,
            currency: cost.currency,
        },
        removed_spans: result.removed_spans.clone(),
        pruned_text: result.pruned.clone(),
        original_text: result.original.clone(),
    }
}

/// 生成文本格式报告
pub fn text_report(result: &PruneResult, model: &str) -> String {
    let cost = pricing::cost_report(result.original_tokens, result.pruned_tokens, model);
    let bar = filled_bar(result.saved_percent());

    let mut lines = Vec::new();
    lines.push("╔════════════════════════════════════════╗".to_string());
    lines.push("║        TokenRazor 剪枝报告            ║".to_string());
    lines.push("╚════════════════════════════════════════╝".to_string());
    lines.push(String::new());

    // Token 统计
    lines.push("  📊 Token 统计".to_string());
    lines.push("  ┌─────────────────────────────────────┐".to_string());
    lines.push(format!("  │ 原始 Tokens  {:>8}       │", result.original_tokens));
    lines.push(format!("  │ 剪后 Tokens  {:>8}       │", result.pruned_tokens));
    lines.push(format!("  │ 节约 Tokens  {:>8}       │", result.saved_tokens()));
    lines.push(format!("  │ 压缩率      {:>7.1}%       │", result.saved_percent()));
    lines.push("  └─────────────────────────────────────┘".to_string());
    lines.push(String::new());

    // 进度条
    lines.push(format!("  [{}] {:.1}% 压缩", bar, result.saved_percent()));
    lines.push(String::new());

    // 费用节省
    lines.push(format!("  💰 费用节省（{} @ ${:.2}/1M tokens）",
        cost.model, cost.price_per_1m));
    lines.push("  ┌─────────────────────────────────────┐".to_string());
    lines.push(format!("  │ 原始费用     {:>12}        │", pricing::format_cost(cost.original_cost)));
    lines.push(format!("  │ 剪后费用     {:>12}        │", pricing::format_cost(cost.pruned_cost)));
    lines.push(format!("  │ 本次节省     {:>12}        │", pricing::format_cost(cost.saved_cost)));
    lines.push("  └─────────────────────────────────────┘".to_string());
    lines.push(String::new());

    // 移除统计
    if !result.removed_spans.is_empty() {
        use std::collections::HashMap;
        let mut reasons: HashMap<&str, u32> = HashMap::new();
        for s in &result.removed_spans {
            *reasons.entry(&s.reason).or_insert(0) += 1;
        }
        lines.push(format!("  移除冗余段: {} 处", result.removed_spans.len()));
        for (reason, _count) in &reasons {
            let conf = &result.removed_spans.iter()
                .find(|s| s.reason == *reason)
                .map(|s| s.confidence)
                .unwrap_or(0.0);
            lines.push(format!("    · {:<15} (置信度 {:>2}%)", reason, (conf * 100.0) as u32));
        }
    } else {
        lines.push("  未发现显著冗余。".to_string());
    }
    lines.push(String::new());

    lines.join("\n")
}

/// 填充进度条
fn filled_bar(percent: f64) -> String {
    let width = 40;
    let filled = ((percent / 100.0) * width as f64).round() as usize;
    let filled = filled.min(width);
    let empty = width - filled;
    format!("{}░{}",
        "█".repeat(filled),
        "░".repeat(empty))
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::pruner::Pruner;

    #[test]
    fn test_text_report_basic() {
        let p = Pruner::new(&["filler"]);
        let r = p.prune("让我想想。答案：42");
        let report = text_report(&r, "gpt-4o");
        assert!(report.contains("TokenRazor"));
        assert!(report.contains("Token"));
    }

    #[test]
    fn test_json_report_structure() {
        let p = Pruner::new(&["filler"]);
        let r = p.prune("让我想想。答案：42");
        let j = json_report(&r, "gpt-4o");
        assert!(j.compression.saved_tokens > 0 || j.compression.original_tokens > 0);
        assert_eq!(j.cost.model, "gpt-4o");
    }

    #[test]
    fn test_bar_100_percent() {
        let bar = filled_bar(100.0);
        assert!(bar.contains('█'));
        assert!(!bar.starts_with('░'));
    }

    #[test]
    fn test_bar_0_percent() {
        let bar = filled_bar(0.0);
        assert!(bar.contains('░'));
        assert!(!bar.contains('█'));
    }
}
