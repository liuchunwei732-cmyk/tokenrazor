/// 项目上下文检测 — 自动识别项目类型/框架/工具链

use serde::Serialize;
use std::collections::HashSet;
use std::path::Path;

/// 项目上下文
#[derive(Debug, Clone, Serialize)]
pub struct ProjectContext {
    pub project_type: String,
    pub framework: String,
    pub build_tool: String,
    pub language: String,
    pub root: String,
    pub features: Vec<String>,
}

/// 检测项目类型
pub fn detect_project(dir: &str) -> ProjectContext {
    let path = Path::new(dir);
    let root = path.to_string_lossy().to_string();

    let features = scan_features(dir);

    let (project_type, framework, build_tool, language) = classify_project(&features);

    ProjectContext {
        project_type,
        framework,
        build_tool,
        language,
        root,
        features,
    }
}

/// 扫描特征文件
fn scan_features(dir: &str) -> Vec<String> {
    let mut features = Vec::new();
    let entries = match std::fs::read_dir(dir) {
        Ok(e) => e,
        Err(_) => return features,
    };

    for entry in entries.flatten() {
        if let Some(name) = entry.file_name().to_str() {
            let name_lower = name.to_lowercase();
            features.push(name_lower);
        }
    }
    features
}

/// 根据特征文件分类项目
fn classify_project(features: &[String]) -> (String, String, String, String) {
    let set: HashSet<&str> = features.iter().map(|s| s.as_str()).collect();

    // Node.js / 前端
    if set.contains("package.json") {
        if has_any(&set, &["vite.config.ts", "vite.config.js"]) {
            return ("frontend".to_string(), "Vue/React".to_string(), "Vite".to_string(), "TypeScript".to_string());
        }
        if has_any(&set, &["next.config.js", "next.config.ts"]) {
            return ("frontend".to_string(), "Next.js".to_string(), "Next".to_string(), "TypeScript".to_string());
        }
        if has_any(&set, &["vue.config.js"]) {
            return ("frontend".to_string(), "Vue".to_string(), "Webpack".to_string(), "JavaScript".to_string());
        }
        if has_any(&set, &["tsconfig.json"]) {
            return ("frontend".to_string(), "React/Node".to_string(), "npm".to_string(), "TypeScript".to_string());
        }
        if has_any(&set, &["index.html", "src/", "public/"]) {
            return ("frontend".to_string(), "Node.js".to_string(), "npm".to_string(), "JavaScript".to_string());
        }
        return ("node".to_string(), "Node.js".to_string(), "npm".to_string(), "JavaScript".to_string());
    }

    // Java
    if set.contains("pom.xml") {
        return ("backend".to_string(), "Spring Boot".to_string(), "Maven".to_string(), "Java".to_string());
    }
    if set.contains("build.gradle") || set.contains("build.gradle.kts") {
        return ("backend".to_string(), "Spring Boot".to_string(), "Gradle".to_string(), "Kotlin".to_string());
    }

    // Python
    if has_any(&set, &["requirements.txt", "setup.py", "pyproject.toml", "Pipfile"]) {
        let framework = if set.contains("django") || has_any(&set, &["django", "manage.py"]) {
            "Django".to_string()
        } else if set.contains("fastapi") || has_any(&set, &["fastapi"]) {
            "FastAPI".to_string()
        } else if set.contains("flask") || has_any(&set, &["flask"]) {
            "Flask".to_string()
        } else {
            "Python".to_string()
        };
        return ("backend".to_string(), framework, "pip".to_string(), "Python".to_string());
    }

    // Rust
    if set.contains("cargo.toml") {
        return ("backend".to_string(), "Rust".to_string(), "Cargo".to_string(), "Rust".to_string());
    }

    // Go
    if has_any(&set, &["go.mod", "go.sum"]) {
        return ("backend".to_string(), "Go".to_string(), "Go Modules".to_string(), "Go".to_string());
    }

    // Flutter / Dart
    if has_any(&set, &["pubspec.yaml", "pubspec.yml"]) {
        return ("mobile".to_string(), "Flutter".to_string(), "pub".to_string(), "Dart".to_string());
    }

    // Docker
    if set.contains("dockerfile") || set.contains("docker-compose.yml") {
        return ("ops".to_string(), "Docker".to_string(), "Docker Compose".to_string(), "YAML".to_string());
    }

    // 无法识别
    ("unknown".to_string(), "Unknown".to_string(), "Unknown".to_string(), "Unknown".to_string())
}

fn has_any(set: &HashSet<&str>, items: &[&str]) -> bool {
    items.iter().any(|i| set.contains(i))
}

/// 生成项目快照（文本摘要）
pub fn generate_snapshot(dir: &str, max_depth: usize) -> String {
    let ctx = detect_project(dir);
    let mut lines = Vec::new();

    lines.push(format!("# 项目: {}", ctx.root));
    lines.push(String::new());
    lines.push(format!("- 类型: {}", ctx.project_type));
    lines.push(format!("- 框架: {}", ctx.framework));
    lines.push(format!("- 构建工具: {}", ctx.build_tool));
    lines.push(format!("- 语言: {}", ctx.language));
    lines.push(String::new());
    lines.push("## 项目结构".to_string());
    lines.push(String::new());

    // 简单目录树
    if let Ok(entries) = std::fs::read_dir(dir) {
        for entry in entries.flatten() {
            if let Ok(ft) = entry.file_type() {
                let name = entry.file_name().to_string_lossy().to_string();
                if name.starts_with('.') || name == "node_modules" || name == "target" || name == ".git" {
                    continue;
                }
                let prefix = if ft.is_dir() { "📁" } else { "📄" };
                lines.push(format!("{} {}", prefix, name));
            }
        }
    }

    lines.join("\n")
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_detect_unknown_dir() {
        let ctx = detect_project("/nonexistent");
        assert_eq!(ctx.project_type, "unknown");
    }

    #[test]
    fn test_scan_features_empty_dir() {
        let f = scan_features("/nonexistent");
        assert!(f.is_empty());
    }

    #[test]
    fn test_classify_package_json() {
        let f = vec!["package.json".to_string()];
        let (t, _, _, _) = classify_project(&f);
        assert_eq!(t, "node");
    }

    #[test]
    fn test_classify_pom_xml() {
        let f = vec!["pom.xml".to_string()];
        let result = classify_project(&f);
        assert_eq!(result.0, "backend");
        assert!(result.1.contains("Spring"));
        assert_eq!(result.2, "Maven");
    }

    #[test]
    fn test_classify_python() {
        let f = vec!["requirements.txt".to_string()];
        let (t, _, _, l) = classify_project(&f);
        assert_eq!(t, "backend");
        assert_eq!(l, "Python");
    }

    #[test]
    fn test_classify_rust() {
        let f = vec!["cargo.toml".to_string()];
        let (t, _, _, l) = classify_project(&f);
        assert_eq!(t, "backend");
        assert_eq!(l, "Rust");
    }

    #[test]
    fn test_generate_snapshot() {
        let s = generate_snapshot("/tmp", 2);
        assert!(s.contains("项目"));
    }
}
