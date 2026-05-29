/// Token 费用计算 — 支持所有已注册模型

use crate::models;

/// 费用报告
#[derive(Debug, Clone, serde::Serialize)]
pub struct CostReport {
    pub original_cost: f64,
    pub pruned_cost: f64,
    pub saved_cost: f64,
    pub saved_percent: f64,
    pub model: String,
    pub price_per_1m: f64,
    pub currency: String,
}

/// 计算 token 费用
pub fn calculate_cost(tokens: u64, price_per_1m: f64) -> f64 {
    (tokens as f64) * price_per_1m / 1_000_000.0
}

/// 生成费用报告
pub fn cost_report(original_tokens: u64, pruned_tokens: u64, model: &str) -> CostReport {
    let model_id = models::resolve_model(model);
    let (input_price, _) = models::get_prices(model_id);

    let original_cost = calculate_cost(original_tokens, input_price);
    let pruned_cost = calculate_cost(pruned_tokens, input_price);
    let saved_cost = original_cost - pruned_cost;
    let saved_percent = if original_cost > 0.0 {
        (saved_cost / original_cost) * 100.0
    } else {
        0.0
    };

    CostReport {
        original_cost,
        pruned_cost,
        saved_cost,
        saved_percent,
        model: model_id.to_string(),
        price_per_1m: input_price,
        currency: "USD".to_string(),
    }
}

/// 格式化金额显示
pub fn format_cost(cost: f64) -> String {
    if cost < 0.01 {
        format!("${:.4}", cost)
    } else if cost < 100.0 {
        format!("${:.2}", cost)
    } else {
        format!("${:.0}", cost)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_calculate_cost_basic() {
        let c = calculate_cost(1000, 2.50);
        assert!((c - 0.0025).abs() < 1e-10);
    }

    #[test]
    fn test_calculate_cost_zero() {
        assert_eq!(calculate_cost(0, 2.50), 0.0);
    }

    #[test]
    fn test_calculate_cost_large() {
        let c = calculate_cost(1_000_000, 2.50);
        assert!((c - 2.50).abs() < 0.001);
    }

    #[test]
    fn test_cost_report_savings() {
        let r = cost_report(100000, 50000, "gpt-4o");
        assert!(r.saved_cost > 0.0);
        assert!((r.saved_percent - 50.0).abs() < 0.1);
    }

    #[test]
    fn test_cost_report_no_savings() {
        let r = cost_report(0, 0, "gpt-4o");
        assert_eq!(r.saved_percent, 0.0);
        assert_eq!(r.saved_cost, 0.0);
    }

    #[test]
    fn test_cost_report_chinese_model() {
        let r = cost_report(1000, 500, "qwen-max");
        assert_eq!(r.model, "qwen-max");
        assert!(r.saved_cost > 0.0);
    }

    #[test]
    fn test_cost_report_alias() {
        let r = cost_report(1000, 500, "通义千问");
        assert_eq!(r.model, "qwen-max");
    }

    #[test]
    fn test_format_cost_small() {
        let s = format_cost(0.0025);
        assert!(s.contains("0.0025"));
    }

    #[test]
    fn test_format_cost_medium() {
        let s = format_cost(1.50);
        assert!(s.contains("1.50"));
    }

    #[test]
    fn test_format_cost_large() {
        let s = format_cost(200.0);
        assert!(s.contains("200"));
    }

    #[test]
    fn test_format_cost_zero() {
        let s = format_cost(0.0);
        assert!(s.contains("0"));
    }

    #[test]
    fn test_cost_report_deepseek() {
        let r = cost_report(100000, 70000, "deepseek-r1");
        assert_eq!(r.model, "deepseek-r1");
        assert!((r.saved_percent - 30.0).abs() < 0.1);
    }
}
