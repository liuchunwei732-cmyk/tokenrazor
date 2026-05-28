"""项目感知引擎 — 自动识别项目类型、框架和折叠策略。"""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import ClassVar, Dict, List, Optional, Set


@dataclass
class ProjectContext:
    """项目上下文，包含检测到的项目类型、框架、特征文件等。"""

    project_type: str = "unknown"  # frontend / backend / mobile / devops / data
    framework: str = "unknown"    # react / vue / next / springboot / flutter ...
    build_tool: str = "unknown"   # npm / maven / gradle / pub / cargo
    language: str = "unknown"    # javascript / typescript / python / java / go / rust
    root: str = ""               # 项目根目录
    features: List[str] = field(default_factory=list)  # 检测到的特征
    recommended_ignores: List[str] = field(default_factory=list)
    recommended_folds: List[str] = field(default_factory=list)

    # 各语言/框架的忽略和折叠规则（ClassVar：不在 __init__ 中，不作为实例字段）
    _IGNORE_RULES: ClassVar[Dict[str, List[str]]] = {        # --- 前端通用 ---
        "frontend_generic": [
            "node_modules", "dist", "build", "coverage",
            ".next", ".nuxt", ".output", "out",
            "pnpm-lock.yaml", "yarn.lock", "package-lock.json",
            "*.hot-update.*", "*.map",
        ],
        # --- 后端通用 ---
        "backend_generic": [
            "target", "build", "bin", "obj",
            "*.class", "*.jar", "*.war",
            ".gradle", "gradle/wrapper/gradle-wrapper.jar",
            "logs", "*.log", "tmp",
        ],
        # --- 移动端通用 ---
        "mobile_generic": [
            "Pods", "DerivedData", ".build",
            "*.xcworkspace", "*.xcuserstate",
            "android/app/build", "android/.gradle",
            ".symlinks", "build/ios", "build/android",
        ],
        # --- 运维通用 ---
        "devops_generic": [
            ".terraform", "terraform.tfstate*",
            ".kube/cache", "helm/charts/*.tgz",
        ],
        # --- 数据科学 ---
        "data_generic": [
            "__pycache__", "*.pyc", ".ipynb_checkpoints",
            "data/raw", "data/processed", "models/*.pkl",
            ".venv", "venv", "env",
        ],
    }

    # 项目类型检测规则（ClassVar）
    _DETECTION_RULES: ClassVar[List[tuple]] = [
        # (特征文件, 特征目录, 项目类型, 框架, 构建工具, 语言)
        # --- 前端 ---
        ("vite.config.ts", None, "frontend", "vite_react", "npm", "typescript"),
        ("vite.config.js", None, "frontend", "vite_react", "npm", "javascript"),
        ("next.config.js", None, "frontend", "next", "npm", "javascript"),
        ("next.config.ts", None, "frontend", "next", "npm", "typescript"),
        ("vue.config.js", None, "frontend", "vue", "npm", "javascript"),
        ("nuxt.config.ts", None, "frontend", "nuxt", "npm", "typescript"),
        ("angular.json", None, "frontend", "angular", "npm", "typescript"),
        ("svelte.config.js", None, "frontend", "svelte", "npm", "javascript"),
        ("uni-app.config.js", None, "frontend", "uniapp", "npm", "javascript"),
        ("taro.config.js", None, "frontend", "taro", "npm", "javascript"),
        ("package.json", None, "frontend", "node", "npm", "javascript"),
        # --- 后端 ---
        ("pom.xml", None, "backend", "springboot", "maven", "java"),
        ("build.gradle", None, "backend", "springboot", "gradle", "java"),
        ("build.gradle.kts", None, "backend", "springboot", "gradle", "kotlin"),
        ("Cargo.toml", None, "backend", "actix", "cargo", "rust"),
        ("go.mod", None, "backend", "gin", "go", "go"),
        ("requirements.txt", None, "backend", "flask", "pip", "python"),
        ("pyproject.toml", None, "backend", "fastapi", "pdm", "python"),
        ("Gemfile", None, "backend", "rails", "bundler", "ruby"),
        # --- 移动端 ---
        ("pubspec.yaml", None, "mobile", "flutter", "pub", "dart"),
        (None, "ios", "mobile", "swiftui", "xcodebuild", "swift"),
        (None, "android/app/src", "mobile", "android", "gradlew", "kotlin"),
        # --- 运维 ---
        ("Dockerfile", None, "devops", "docker", "docker", "dockerfile"),
        (None, "k8s", "devops", "kubernetes", "helm", "yaml"),
        (".terraform.lock.hcl", None, "devops", "terraform", "terraform", "hcl"),
        # --- 数据 ---
        ("requirements.txt", None, "data", "pytorch", "pip", "python"),
        ("environment.yml", None, "data", "conda", "conda", "python"),
    ]

    @classmethod
    def detect(cls, root: str = ".") -> "ProjectContext":
        """检测给定路径的项目上下文。"""
        root_path = Path(root).resolve()
        ctx = cls(root=str(root_path))

        for feature_file, feature_dir, ptype, framework, build_tool, lang in cls._DETECTION_RULES:
            found = False
            if feature_file:
                # 搜索特征文件（只搜索前3层）
                for f in root_path.rglob(feature_file):
                    if f.is_file() and cls._is_reasonable_depth(f, root_path, max_depth=3):
                        ctx.features.append(feature_file)
                        found = True
                        break
            if feature_dir and not found:
                check_path = root_path / feature_dir
                if check_path.exists() and check_path.is_dir():
                    ctx.features.append(feature_dir)
                    found = True

            if found:
                ctx.project_type = ptype
                ctx.framework = framework
                ctx.build_tool = build_tool
                ctx.language = lang
                break

        # 根据项目类型设置推荐忽略/折叠规则
        ctx._apply_recommended_rules()

        return ctx

    @staticmethod
    def _is_reasonable_depth(f: Path, root: Path, max_depth: int = 3) -> bool:
        """检查文件是否在合理的目录深度内。"""
        try:
            rel = f.relative_to(root)
            return len(rel.parts) <= max_depth
        except ValueError:
            return False

    def _apply_recommended_rules(self):
        """根据项目类型应用推荐规则。"""
        type_key = f"{self.project_type}_generic"
        base_rules = self._IGNORE_RULES.get(type_key, [])

        if self.project_type == "frontend":
            # 前端：加上特定框架的规则
            self.recommended_ignores = base_rules + [
                f".{self.framework}", f"{self.framework}-cache",
            ]
            self.recommended_folds = ["node_modules"]
        elif self.project_type == "backend":
            self.recommended_ignores = base_rules
            if self.build_tool == "maven":
                self.recommended_folds = ["target"]
            elif self.build_tool == "gradle":
                self.recommended_folds = ["build", ".gradle"]
        elif self.project_type == "mobile":
            self.recommended_ignores = base_rules
            if self.framework == "flutter":
                self.recommended_folds = [".dart_tool", "build"]
        elif self.project_type == "devops":
            self.recommended_ignores = base_rules
        elif self.project_type == "data":
            self.recommended_ignores = base_rules + ["__pycache__"]
        else:
            self.recommended_ignores = base_rules

    def generate_snapshot(self, max_depth: int = 3) -> str:
        """生成项目快照文本（给 AI 看的结构化摘要）。"""
        root_path = Path(self.root)
        lines = [
            f"# 项目快照: {root_path.name}",
            f"",
            f"- **类型**: {self.project_type}",
            f"- **框架**: {self.framework}",
            f"- **构建工具**: {self.build_tool}",
            f"- **语言**: {self.language}",
            f"- **根目录**: {self.root}",
            f"",
            f"## 目录结构",
        ]

        # 生成简化目录树
        self._walk_tree(root_path, lines, max_depth, "")

        lines.extend([
            "",
            "## 推荐忽略规则",
        ])
        for rule in self.recommended_ignores:
            lines.append(f"- `{rule}`")
        if self.recommended_folds:
            lines.extend([
                "",
                "## 推荐折叠规则",
            ])
            for rule in self.recommended_folds:
                lines.append(f"- `{rule}`")

        return "\n".join(lines)

    def _walk_tree(self, path: Path, lines: List[str], max_depth: int, prefix: str, depth: int = 0):
        """递归生成目录树。"""
        if depth > max_depth:
            return

        try:
            entries = sorted(
                [e for e in path.iterdir() if e.name not in self.recommended_ignores and not e.name.startswith('.')],
                key=lambda e: (not e.is_dir(), e.name.lower()),
            )
        except PermissionError:
            return

        for i, entry in enumerate(entries):
            is_last = i == len(entries) - 1
            connector = "└── " if is_last else "├── "
            next_prefix = "    " if is_last else "│   "

            if entry.is_dir():
                lines.append(f"{prefix}{connector}{entry.name}/")
                self._walk_tree(entry, lines, max_depth, prefix + next_prefix, depth + 1)
            else:
                size = entry.stat().st_size
                size_str = f"{size/1024:.1f} KB" if size >= 1024 else f"{size} B"
                lines.append(f"{prefix}{connector}{entry.name} ({size_str})")


def detect_project(root: str = ".") -> ProjectContext:
    """便捷函数：检测项目。"""
    return ProjectContext.detect(root)
