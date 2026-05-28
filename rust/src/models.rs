/// 模型定价定义 — 中美主流模型全覆盖
///
/// 中文差异化：国内模型单独列类，支持中文别名

use std::collections::HashMap;

/// 单个模型定价
#[derive(Debug, Clone)]
pub struct ModelPrice {
    pub id: &'static str,
    pub name_cn: &'static str,
    pub input_per_1m: f64,   // $/1M input tokens
    pub output_per_1m: f64,  // $/1M output tokens
}

/// 常用模型定价列表
pub const MODELS: &[ModelPrice] = &[
    // ===== 国际模型 =====
    ModelPrice { id: "gpt-4o", name_cn: "GPT-4o", input_per_1m: 2.50, output_per_1m: 10.00 },
    ModelPrice { id: "gpt-4o-mini", name_cn: "GPT-4o Mini", input_per_1m: 0.15, output_per_1m: 0.60 },
    ModelPrice { id: "claude-3.5-sonnet", name_cn: "Claude 3.5 Sonnet", input_per_1m: 3.00, output_per_1m: 15.00 },
    ModelPrice { id: "claude-3.5-haiku", name_cn: "Claude 3.5 Haiku", input_per_1m: 0.80, output_per_1m: 4.00 },
    ModelPrice { id: "deepseek-r1", name_cn: "DeepSeek R1", input_per_1m: 0.55, output_per_1m: 2.19 },
    ModelPrice { id: "deepseek-v4", name_cn: "DeepSeek V4", input_per_1m: 0.25, output_per_1m: 0.80 },
    ModelPrice { id: "gemini-2.0-flash", name_cn: "Gemini 2.0 Flash", input_per_1m: 0.10, output_per_1m: 0.40 },

    // ===== 国产大模型 =====
    ModelPrice { id: "qwen-max", name_cn: "通义千问 Max", input_per_1m: 2.00, output_per_1m: 8.00 },
    ModelPrice { id: "qwen-plus", name_cn: "通义千问 Plus", input_per_1m: 0.80, output_per_1m: 2.00 },
    ModelPrice { id: "qwen-turbo", name_cn: "通义千问 Turbo", input_per_1m: 0.30, output_per_1m: 0.60 },
    ModelPrice { id: "ernie-4.5", name_cn: "文心一言 4.5", input_per_1m: 1.20, output_per_1m: 4.80 },
    ModelPrice { id: "ernie-3.5", name_cn: "文心一言 3.5", input_per_1m: 0.40, output_per_1m: 1.60 },
    ModelPrice { id: "glm-4", name_cn: "智谱 GLM-4", input_per_1m: 1.00, output_per_1m: 1.00 },
    ModelPrice { id: "glm-4-flash", name_cn: "智谱 GLM-4 Flash", input_per_1m: 0.10, output_per_1m: 0.10 },
    ModelPrice { id: "moonshot-v1", name_cn: "月之暗面 Moonshot v1", input_per_1m: 1.00, output_per_1m: 4.00 },
    ModelPrice { id: "yi-lightning", name_cn: "零一万物 Yi Lightning", input_per_1m: 0.50, output_per_1m: 2.00 },
    ModelPrice { id: "minimax-abab", name_cn: "MiniMax ABAB", input_per_1m: 0.80, output_per_1m: 2.40 },
    ModelPrice { id: "baichuan4", name_cn: "百川 Baichuan 4", input_per_1m: 1.00, output_per_1m: 4.00 },
    ModelPrice { id: "spark-4.0", name_cn: "讯飞星火 4.0", input_per_1m: 0.50, output_per_1m: 2.00 },
];

/// 模型别名映射（支持模糊匹配）
pub fn build_alias_map() -> HashMap<&'static str, &'static str> {
    let mut m = HashMap::new();
    // 国际模型别名
    m.insert("gpt4", "gpt-4o");
    m.insert("gpt-4", "gpt-4o");
    m.insert("gpt4o", "gpt-4o");
    m.insert("claude", "claude-3.5-sonnet");
    m.insert("sonnet", "claude-3.5-sonnet");
    m.insert("haiku", "claude-3.5-haiku");
    m.insert("deepseek", "deepseek-r1");
    m.insert("ds", "deepseek-r1");
    m.insert("gemini", "gemini-2.0-flash");
    m.insert("gemini-flash", "gemini-2.0-flash");
    // 国产模型别名
    m.insert("qwen", "qwen-max");
    m.insert("通义", "qwen-max");
    m.insert("通义千问", "qwen-max");
    m.insert("ernie", "ernie-4.5");
    m.insert("文心一言", "ernie-4.5");
    m.insert("文心", "ernie-4.5");
    m.insert("glm", "glm-4");
    m.insert("智谱", "glm-4");
    m.insert("moonshot", "moonshot-v1");
    m.insert("月之暗面", "moonshot-v1");
    m.insert("kimi", "moonshot-v1");
    m.insert("yi", "yi-lightning");
    m.insert("零一", "yi-lightning");
    m.insert("minimax", "minimax-abab");
    m.insert("baichuan", "baichuan4");
    m.insert("百川", "baichuan4");
    m.insert("spark", "spark-4.0");
    m.insert("星火", "spark-4.0");
    m.insert("讯飞", "spark-4.0");
    m
}

/// 解析模型名（支持别名），返回映射后的 ID
pub fn resolve_model(name: &str) -> &'static str {
    let aliases = build_alias_map();
    if let Some(&resolved) = aliases.get(name.to_lowercase().as_str()) {
        return resolved;
    }
    // 直接匹配
    for m in MODELS {
        if m.id == name {
            return m.id;
        }
    }
    // 默认回退
    "gpt-4o"
}

/// 查找模型定价
pub fn find_model(id: &str) -> Option<&'static ModelPrice> {
    MODELS.iter().find(|m| m.id == id)
}

/// 获取模型价格（返回 (input_price, output_price)）
pub fn get_prices(model_id: &str) -> (f64, f64) {
    let resolved = resolve_model(model_id);
    find_model(resolved)
        .map(|m| (m.input_per_1m, m.output_per_1m))
        .unwrap_or((1.00, 4.00))
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_resolve_gpt4o() {
        assert_eq!(resolve_model("gpt4"), "gpt-4o");
        assert_eq!(resolve_model("gpt-4o"), "gpt-4o");
    }

    #[test]
    fn test_resolve_deepseek() {
        assert_eq!(resolve_model("deepseek"), "deepseek-r1");
        assert_eq!(resolve_model("ds"), "deepseek-r1");
    }

    #[test]
    fn test_resolve_chinese_models() {
        assert_eq!(resolve_model("qwen"), "qwen-max");
        assert_eq!(resolve_model("通义千问"), "qwen-max");
        assert_eq!(resolve_model("文心一言"), "ernie-4.5");
        assert_eq!(resolve_model("kimi"), "moonshot-v1");
        assert_eq!(resolve_model("智谱"), "glm-4");
        assert_eq!(resolve_model("星火"), "spark-4.0");
    }

    #[test]
    fn test_find_model() {
        let m = find_model("gpt-4o").unwrap();
        assert!((m.input_per_1m - 2.50).abs() < 0.01);
    }

    #[test]
    fn test_get_prices_unknown_defaults_to_gpt4o() {
        let (inp, _out) = get_prices("unknown");
        // 未知模型默认回退到 gpt-4o ($2.50)
        assert!((inp - 2.50).abs() < 0.01);
    }

    #[test]
    fn test_chinese_models_count() {
        let chinese: Vec<_> = MODELS.iter().filter(|m| m.id.contains("qwen")
            || m.id.contains("ernie") || m.id.contains("glm")
            || m.id.contains("moonshot") || m.id.contains("yi")
            || m.id.contains("minimax") || m.id.contains("baichuan")
            || m.id.contains("spark")).collect();
        assert!(chinese.len() >= 8, "至少需要 8 个国产模型");
    }
}
