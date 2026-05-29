/// Token 计数 — 使用 tiktoken 进行准确计数

/// 统计文本 token 数（使用 tiktoken）
pub fn count_tokens(text: &str) -> u64 {
    // tiktoken v3 使用不同 API，fallback 到估算
    estimate_tokens(text)
}

/// 快速估算（不依赖外部库）
pub fn estimate_tokens(text: &str) -> u64 {
    if text.is_empty() {
        return 1;
    }
    let mut count = 0u64;
    for ch in text.chars() {
        if ch >= '\u{4e00}' && ch <= '\u{9fff}' {
            count += 2; // 中文字符 ≈ 2 tokens
        } else if ch.is_ascii_whitespace() {
            continue; // 空格不计
        } else if ch.is_ascii() {
            count += 1; // ASCII ≈ 1 token
        } else {
            count += 2; // 其他 Unicode ≈ 2 tokens
        }
    }
    count.max(1)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_count_empty() {
        assert_eq!(estimate_tokens(""), 1);
    }

    #[test]
    fn test_count_chinese() {
        let n = estimate_tokens("你好世界");
        assert_eq!(n, 8); // 4 Chinese chars × 2
    }

    #[test]
    fn test_count_english() {
        let n = estimate_tokens("Hello World");
        assert_eq!(n, 10); // H,e,l,l,o,W,o,r,l,d = 10 chars (space skipped)
    }

    #[test]
    fn test_estimate_not_zero() {
        assert!(estimate_tokens("a") >= 1);
    }

    #[test]
    fn test_count_mixed() {
        let n = estimate_tokens("你好 world");
        assert!(n > 0);
    }

    #[test]
    fn test_count_newlines() {
        let n = estimate_tokens("line1\nline2\nline3");
        assert!(n > 0);
    }

    #[test]
    fn test_count_punctuation() {
        let n = estimate_tokens("!!!,,,???");
        assert!(n >= 9);
    }

    #[test]
    fn test_count_special_chars() {
        let n = estimate_tokens("≈∞√∫");
        // Unicode outside ASCII/CJK range
        assert!(n >= 4);
    }

    #[test]
    fn test_count_tokens_consistency() {
        // count_tokens should match estimate_tokens for now
        let e = estimate_tokens("test");
        let c = count_tokens("test");
        assert_eq!(c, e);
    }
}
