/// 工具链规则 — 中英文全栈工具链过滤规则

use regex::Regex;

/// 工具链规则
pub struct ToolchainRule {
    pub patterns: Vec<Regex>,
    pub action: &'static str, // "keep" | "fold" | "strip"
}

/// 检测日志中的工具链
pub fn detect_toolchain(log: &str) -> Vec<&'static str> {
    let lower = log.to_lowercase();
    let mut detected = Vec::new();

    if lower.contains("npm") || lower.contains("node_modules") {
        detected.push("npm");
    }
    if lower.contains("yarn") {
        detected.push("yarn");
    }
    if lower.contains("mvn ") || lower.contains("maven") || (lower.contains("[info]") && lower.contains("scanning")) {
        detected.push("maven");
    }
    if lower.contains("gradle") {
        detected.push("gradle");
    }
    if lower.contains("flutter") || lower.contains("dart") {
        detected.push("flutter");
    }
    if lower.contains("docker") {
        detected.push("docker");
    }
    if lower.contains("kubectl") || lower.contains("helm") {
        detected.push("kubectl");
    }
    if lower.contains("pip") || lower.contains("pypi") || lower.contains("requirements.txt") {
        detected.push("pip");
    }
    if lower.contains("cnpm") || lower.contains("npmmirror") {
        detected.push("cnpm");
    }

    detected
}

/// 判断是否为工具链的冗余输出
pub fn is_toolchain_noise(line: &str) -> bool {
    let fold_patterns: &[&str] = &[
        // npm/pnpm/yarn
        "npm notice",
        "npm http",
        "npm warn", // 某些 npm warn 可折叠
        "added ",
        "packages audited",
        "found 0 vulnerabilities",
        "up to date",
        "node_modules/",
        // pip
        "requirement already satisfied",
        "using cached",
        "collecting",
        "downloading",
        "installing collected packages",
        // maven
        "downloading:",
        "downloaded:",
        "progress:",
        // docker
        "step ",
        " ---> ",
        "removing intermediate container",
        "successfully built",
        "successfully tagged",
        // 国内镜像
        "mirrors.aliyun.com",
        "mirrors.tencent.com",
        "mirrors.huaweicloud.com",
        "mirrors.tuna.tsinghua.edu.cn",
        "mirrors.ustc.edu.cn",
        "registry.npmmirror.com",
    ];

    let lower = line.to_lowercase();
    fold_patterns.iter().any(|p| lower.contains(p))
}

/// 应用工具链规则过滤日志
pub fn apply_toolchain_rules(lines: &[&str]) -> Vec<String> {
    let mut output = Vec::new();
    let detected = if lines.is_empty() { vec![] } else {
        detect_toolchain(lines[0])
    };

    for line in lines {
        let trimmed = line.trim();
        if trimmed.is_empty() {
            continue;
        }

        // 错误行永远保留
        let lower = trimmed.to_lowercase();
        if lower.starts_with("error") || lower.contains("[error]") || lower.contains("error:") {
            output.push(trimmed.to_string());
            continue;
        }

        // 检测是否可折叠
        if is_toolchain_noise(trimmed) {
            continue;
        }

        output.push(trimmed.to_string());
    }

    output
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_detect_npm() {
        let d = detect_toolchain("npm ERR! code ELIFECYCLE");
        assert!(d.contains(&"npm"));
    }

    #[test]
    fn test_detect_maven() {
        let d = detect_toolchain("[INFO] Scanning for projects...");
        assert!(d.contains(&"maven"));
    }

    #[test]
    fn test_detect_docker() {
        let d = detect_toolchain("docker build -t myapp .");
        assert!(d.contains(&"docker"));
    }

    #[test]
    fn test_detect_cnpm() {
        let d = detect_toolchain("cnpm install --save lodash");
        assert!(d.contains(&"cnpm"));
    }

    #[test]
    fn test_is_toolchain_noise_npm() {
        assert!(is_toolchain_noise("npm notice created a lockfile"));
    }

    #[test]
    fn test_is_toolchain_noise_docker() {
        assert!(is_toolchain_noise("Step 5/10 : RUN apt-get update"));
    }

    #[test]
    fn test_apply_rules_keeps_error() {
        let result = apply_toolchain_rules(&[
            "[INFO] starting build",
            "ERROR: compilation failed",
            "npm notice created lockfile",
        ]);
        assert!(result.iter().any(|l| l.contains("ERROR")));
        assert!(!result.iter().any(|l| l.contains("npm notice")));
    }

    #[test]
    fn test_apply_rules_empty() {
        let result = apply_toolchain_rules(&[]);
        assert!(result.is_empty());
    }
}
