/// 终端输出过滤器 — 中英文双支持

use regex::Regex;

/// 过滤结果
pub struct FilterResult {
    pub filtered: String,
    pub original_lines: u64,
    pub filtered_lines: u64,
    pub original_tokens: u64,
    pub filtered_tokens: u64,
}

/// 日志级别
enum LogLevel {
    Error,
    Warn,
    Info,
    Debug,
    Unknown,
}

fn classify_line(line: &str) -> LogLevel {
    let lower = line.to_lowercase();
    if lower.contains("[error]") || lower.contains("error:") || lower.starts_with("error") {
        LogLevel::Error
    } else if lower.contains("[warn]") || lower.contains("warning:") || lower.starts_with("warning") {
        LogLevel::Warn
    } else if lower.contains("[info]") || lower.contains("[pass]") || lower.contains("[fail]") {
        LogLevel::Info
    } else if lower.contains("[debug]") || lower.contains("debug:") {
        LogLevel::Debug
    } else {
        LogLevel::Unknown
    }
}

/// 判断是否为需要折叠的冗余行
fn is_foldable(line: &str) -> bool {
    let fold_patterns = [
        // node_modules / npm 相关
        Regex::new(r"node_modules/").unwrap(),
        Regex::new(r"npm (WARN|notice|http) ").unwrap(),
        Regex::new(r"added \d+ packages").unwrap(),
        Regex::new(r"packages? audited").unwrap(),
        Regex::new(r"found \d+ (vulnerabilit|severity)").unwrap(),
        // 国内镜像
        Regex::new(r"mirrors\.(aliyun|tencent|huawei|tuna|ustc|npmmirror)").unwrap(),
        // pip
        Regex::new(r"Requirement already satisfied").unwrap(),
        Regex::new(r"Using cached").unwrap(),
        Regex::new(r"Collecting").unwrap(),
        Regex::new(r"Downloading").unwrap(),
        Regex::new(r"Installing collected packages").unwrap(),
        // docker
        Regex::new(r"Step \d+/\d+ :").unwrap(),
        Regex::new(r" ---> [a-f0-9]+").unwrap(),
        Regex::new(r"Removing intermediate container").unwrap(),
        // 通用进度
        Regex::new(r"^\[?\d+%\]").unwrap(),
        Regex::new(r"^\d+/\d+ \|").unwrap(),
    ];
    fold_patterns.iter().any(|p| p.is_match(line))
}

/// 过滤终端输出
pub fn filter_log(text: &str) -> FilterResult {
    let lines: Vec<&str> = text.lines().collect();
    let total_lines = lines.len() as u64;

    let mut output_lines = Vec::new();

    for line in &lines {
        let level = classify_line(line);
        match level {
            LogLevel::Error => output_lines.push(line.to_string()),
            LogLevel::Warn => output_lines.push(line.to_string()),
            LogLevel::Info | LogLevel::Unknown => {
                if !is_foldable(line) {
                    output_lines.push(line.to_string());
                }
            }
            LogLevel::Debug => {} // debug 行默认过滤
        }
    }

    let filtered = output_lines.join("\n");

    FilterResult {
        filtered,
        original_lines: total_lines,
        filtered_lines: output_lines.len() as u64,
        original_tokens: 0,   // 简化版不计算 token
        filtered_tokens: 0,
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_keep_errors() {
        let r = filter_log("[ERROR] crash\n[INFO] done\n");
        assert!(r.filtered.contains("crash"));
    }

    #[test]
    fn test_fold_node_modules() {
        let r = filter_log("node_modules/package/index.js\n[ERROR] real error\n");
        assert!(!r.filtered.contains("node_modules"));
        assert!(r.filtered.contains("real error"));
    }

    #[test]
    fn test_chinese_error() {
        let r = filter_log("[ERROR] 连接数据库失败\n[INFO] 处理中\n");
        assert!(r.filtered.contains("连接数据库失败"));
    }

    #[test]
    fn test_empty_input() {
        let r = filter_log("");
        assert_eq!(r.filtered, "");
    }
}
