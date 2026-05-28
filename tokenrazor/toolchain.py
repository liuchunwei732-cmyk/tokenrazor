"""工具链规则库 — 中文生态深度适配的全栈工具链模式库。

为 npm、vue-cli、flutter、spring-boot、docker 等工具提供：
1. 中英文日志模式识别
2. 智能降噪规则（保留关键报错、折叠冗余）
3. 报错严重等级判断
"""

import re
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Pattern, Tuple


@dataclass
class ToolchainRule:
    """单条工具链规则。"""
    name: str
    patterns: List[Pattern]
    action: str  # "keep" | "fold" | "strip" | "summarize"
    priority: int = 0  # 优先级，越高越优先匹配
    description: str = ""


@dataclass
class ToolchainConfig:
    """各工具链的过滤配置。"""
    name: str
    display_name: str
    rules: List[ToolchainRule] = field(default_factory=list)
    version_commands: List[str] = field(default_factory=list)
    error_markers: List[str] = field(default_factory=list)

    def add_rule(self, rule: ToolchainRule):
        self.rules.append(rule)

    def match(self, line: str) -> Optional[str]:
        """匹配单行日志，返回建议动作或 None。"""
        for rule in sorted(self.rules, key=lambda r: -r.priority):
            for pat in rule.patterns:
                if pat.search(line):
                    return rule.action
        return None


# ============================================================
# 前端工具链
# ============================================================

NPM_CONFIG = ToolchainConfig(
    name="npm",
    display_name="npm / yarn / pnpm",
    version_commands=["npm --version", "yarn --version", "pnpm --version"],
    error_markers=["ERR!", "error", "Error", "ERROR", "Failed", "failed"],
)

NPM_CONFIG.add_rule(ToolchainRule(
    "npm_error_header", [
        re.compile(r"npm\s+ERR!", re.IGNORECASE),
    ], "keep", priority=100, description="保留 npm 错误头",
))
NPM_CONFIG.add_rule(ToolchainRule(
    "npm_error_body", [
        re.compile(r"npm\s+ERR!\s+[A-Za-z]"),
    ], "keep", priority=80, description="保留 npm 错误详情",
))
NPM_CONFIG.add_rule(ToolchainRule(
    "npm_warn", [
        re.compile(r"npm\s+WARN", re.IGNORECASE),
        re.compile(r"warning", re.IGNORECASE),
    ], "fold", priority=50, description="折叠 npm 警告",
))
NPM_CONFIG.add_rule(ToolchainRule(
    "npm_verbose", [
        re.compile(r"npm\s+(VERBOSE|TIMING|INFO|HTTP|SILLY)", re.IGNORECASE),
        re.compile(r"npm notice"),
    ], "strip", priority=40, description="移除 npm 啰嗦日志",
))
NPM_CONFIG.add_rule(ToolchainRule(
    "npm_timing", [
        re.compile(r"timing\s+npm"),
        re.compile(r"\d+ms$"),
        re.compile(r"completed in \d+"),
    ], "strip", priority=30, description="移除耗时统计",
))
NPM_CONFIG.add_rule(ToolchainRule(
    "npm_deprecation", [
        re.compile(r"deprecated", re.IGNORECASE),
    ], "fold", priority=50, description="折叠弃用警告",
))
NPM_CONFIG.add_rule(ToolchainRule(
    "npm_audit", [
        re.compile(r"audit\s+(\d+)\s+vulnerabilit"),
        re.compile(r"Run\s+npm\s+audit"),
    ], "summarize", priority=60, description="聚合安全审计信息",
))

# yarn
YARN_CONFIG = ToolchainConfig(
    name="yarn",
    display_name="yarn",
    version_commands=["yarn --version"],
    error_markers=["ERR!", "error", "UNMET"],
)
YARN_CONFIG.add_rule(ToolchainRule(
    "yarn_error", [
        re.compile(r"yarn\s+error", re.IGNORECASE),
        re.compile(r"error\s+Command\s+failed"),
        re.compile(r"UNMET\s+PEER\s+DEPENDENCY"),
    ], "keep", priority=100,
))
YARN_CONFIG.add_rule(ToolchainRule(
    "yarn_warn", [
        re.compile(r"yarn\s+warn", re.IGNORECASE),
    ], "fold", priority=50,
))
YARN_CONFIG.add_rule(ToolchainRule(
    "yarn_verbose", [
        re.compile(r"\[[\d/]+\]\s+\d+:\d+:\d+"),
        re.compile(r"yarn\s+info"),
    ], "strip", priority=30,
))

# vite
VITE_CONFIG = ToolchainConfig(
    name="vite",
    display_name="Vite",
    version_commands=["vite --version"],
    error_markers=["error", "[vite]", "Error"],
)
VITE_CONFIG.add_rule(ToolchainRule(
    "vite_error", [
        re.compile(r"\[vite\]", re.IGNORECASE),
        re.compile(r"✗|×|failed", re.IGNORECASE),
    ], "keep", priority=100,
))
VITE_CONFIG.add_rule(ToolchainRule(
    "vite_build", [
        re.compile(r"vite\s+(v\d+\.\d+\.\d+)"),
        re.compile(r"building\s+for\s+production"),
        re.compile(r"✓|\u2713"),
    ], "fold", priority=50,
))

# webpack
WEBPACK_CONFIG = ToolchainConfig(
    name="webpack",
    display_name="Webpack",
    version_commands=[],
    error_markers=["ERROR", "Module not found", "Failed to compile"],
)
WEBPACK_CONFIG.add_rule(ToolchainRule(
    "webpack_error_header", [
        re.compile(r"ERROR\s+in", re.IGNORECASE),
        re.compile(r"Module\s+not\s+found", re.IGNORECASE),
        re.compile(r"Failed\s+to\s+compile", re.IGNORECASE),
        re.compile(r"Compilation\s+failed", re.IGNORECASE),
    ], "keep", priority=100,
))
WEBPACK_CONFIG.add_rule(ToolchainRule(
    "webpack_stats", [
        re.compile(r"^\s+at\s+.*node_modules"),
        re.compile(r"webpack\s+\d+\.\d+\.\d+"),
        re.compile(r"Hash:"),
        re.compile(r"Time:\s+\d+"),
        re.compile(r"Built\s+at:"),
    ], "fold", priority=50,
))

# ============================================================
# 后端工具链
# ============================================================

MAVEN_CONFIG = ToolchainConfig(
    name="maven",
    display_name="Maven",
    version_commands=["mvn --version"],
    error_markers=["ERROR", "BUILD FAILURE", "Failed to execute"],
)
MAVEN_CONFIG.add_rule(ToolchainRule(
    "maven_error", [
        re.compile(r"BUILD\s+FAILURE", re.IGNORECASE),
        re.compile(r"Failed\s+to\s+execute\s+goal", re.IGNORECASE),
        re.compile(r"ERROR:", re.IGNORECASE),
        re.compile(r"COMPILATION\s+ERROR", re.IGNORECASE),
    ], "keep", priority=100,
))
MAVEN_CONFIG.add_rule(ToolchainRule(
    "maven_fold", [
        re.compile(r"Download(ing|ed)\s+from"),
        re.compile(r"Progress\s+\(|[\=\>]+\s+\d+%"),
        re.compile(r"^\[INFO\]\s+---"),
        re.compile(r"^\[INFO\]\s+Scanning"),
        re.compile(r"^\[INFO\]\s+Reactor"),
    ], "fold", priority=50,
))
MAVEN_CONFIG.add_rule(ToolchainRule(
    "maven_strip", [
        re.compile(r"^\[DEBUG\]"),
        re.compile(r"^\[TRACE\]"),
    ], "strip", priority=30,
))
MAVEN_CONFIG.add_rule(ToolchainRule(
    "maven_success", [
        re.compile(r"BUILD\s+SUCCESS", re.IGNORECASE),
    ], "fold", priority=60,
))

GRADLE_CONFIG = ToolchainConfig(
    name="gradle",
    display_name="Gradle",
    version_commands=["gradle --version"],
    error_markers=["FAILURE", "error", "Could not"],
)
GRADLE_CONFIG.add_rule(ToolchainRule(
    "gradle_error", [
        re.compile(r"Build\s+FAILED", re.IGNORECASE),
        re.compile(r"FAILURE:", re.IGNORECASE),
        re.compile(r"Could\s+not\s+(find|resolve|determine)", re.IGNORECASE),
    ], "keep", priority=100,
))
GRADLE_CONFIG.add_rule(ToolchainRule(
    "gradle_cache", [
        re.compile(r"Using\s+(local|directory)\s+cache"),
        re.compile(r"Resolving\s+dependencies"),
        re.compile(r"Downloading"),
    ], "fold", priority=50,
))
GRADLE_CONFIG.add_rule(ToolchainRule(
    "gradle_daemon", [
        re.compile(r"Starting\s+a\s+Gradle\s+Daemon"),
        re.compile(r"Daemon\s+will\s+be\s+stopped"),
        re.compile(r"Daemon\s+started"),
    ], "strip", priority=40,
))

# Spring Boot
SPRINGBOOT_CONFIG = ToolchainConfig(
    name="springboot",
    display_name="Spring Boot",
    version_commands=[],
    error_markers=["Exception", "Error", "FAILED", "Failed"],
)
SPRINGBOOT_CONFIG.add_rule(ToolchainRule(
    "springboot_error", [
        re.compile(r"Exception\s+in\s+thread", re.IGNORECASE),
        re.compile(r"APPLICATION\s+FAILED\s+TO\s+START", re.IGNORECASE),
        re.compile(r"UnsatisfiedDependencyError", re.IGNORECASE),
        re.compile(r"BeanCreationException", re.IGNORECASE),
        re.compile(r"Error\s+starting\s+ApplicationContext", re.IGNORECASE),
    ], "keep", priority=100,
))
SPRINGBOOT_CONFIG.add_rule(ToolchainRule(
    "springboot_health", [
        re.compile(r"Started\s+Application\s+in"),
        re.compile(r"Tomcat\s+started\s+on\s+port"),
        re.compile(r"o\.s\.b\.w\.e\.t\.TomcatWebServer\s+:"),
        re.compile(r"o\.s\.b\.w\.f\.ConditionEvaluationReportLoggingListener"),
    ], "fold", priority=50,
))
SPRINGBOOT_CONFIG.add_rule(ToolchainRule(
    "springboot_debug", [
        re.compile(r"DEBUG\s+\d+"),
        re.compile(r"TRACE\s+\d+"),
        re.compile(r"o\.s\.\w+\.\w+\s*:"),
        re.compile(r"\[[\w,\-]+\]\s+\w+\.\w+\.\w+\s*:"),
    ], "fold", priority=30,
))

# ============================================================
# 移动端工具链
# ============================================================

FLUTTER_CONFIG = ToolchainConfig(
    name="flutter",
    display_name="Flutter",
    version_commands=["flutter --version"],
    error_markers=["Error", "error", "Failed"],
)
FLUTTER_CONFIG.add_rule(ToolchainRule(
    "flutter_error", [
        re.compile(r"Error\s+output", re.IGNORECASE),
        re.compile(r"FAILURE:", re.IGNORECASE),
        re.compile(r"Build\s+failed", re.IGNORECASE),
        re.compile(r"exit code \d+", re.IGNORECASE),
    ], "keep", priority=100,
))
FLUTTER_CONFIG.add_rule(ToolchainRule(
    "flutter_fold", [
        re.compile(r"Running\s+\"(flutter|pub)\""),
        re.compile(r"Resolving\s+dependencies"),
        re.compile(r"Downloading\s+packages"),
        re.compile(r"^\d+\.\d+s$"),
    ], "fold", priority=50,
))
FLUTTER_CONFIG.add_rule(ToolchainRule(
    "flutter_build_info", [
        re.compile(r"Flutter\s+run\s+key"),
        re.compile(r"Using\s+hardware\s+rendering"),
        re.compile(r"Syncing\s+files"),
        re.compile(r"Flutter\s+assets"),
    ], "strip", priority=40,
))

# ============================================================
# 运维工具链
# ============================================================

DOCKER_CONFIG = ToolchainConfig(
    name="docker",
    display_name="Docker",
    version_commands=["docker --version"],
    error_markers=["Error", "error", "failed", "denied"],
)
DOCKER_CONFIG.add_rule(ToolchainRule(
    "docker_error", [
        re.compile(r"Error\s+response\s+from\s+daemon", re.IGNORECASE),
        re.compile(r"docker:\s+Error", re.IGNORECASE),
        re.compile(r"denied:", re.IGNORECASE),
        re.compile(r"failed\s+to\s+(build|push|pull)", re.IGNORECASE),
    ], "keep", priority=100,
))
DOCKER_CONFIG.add_rule(ToolchainRule(
    "docker_build_logs", [
        re.compile(r"Step\s+\d+/\d+\s+:"),
        re.compile(r"Running\s+in\s+[\da-f]+"),
        re.compile(r"Removing\s+intermediate\s+container"),
        re.compile(r"^\s*[-]+>\s+[\da-f]+$"),
    ], "fold", priority=50,
))
DOCKER_CONFIG.add_rule(ToolchainRule(
    "docker_layer_caching", [
        re.compile(r"Using\s+cache", re.IGNORECASE),
        re.compile(r"CACHED", re.IGNORECASE),
    ], "strip", priority=40,
))

KUBECTL_CONFIG = ToolchainConfig(
    name="kubectl",
    display_name="kubectl / helm",
    version_commands=["kubectl version --client", "helm version"],
    error_markers=["Error", "ErrImagePull", "CrashLoopBackOff"],
)
KUBECTL_CONFIG.add_rule(ToolchainRule(
    "kubectl_error", [
        re.compile(r"(Error|ErrImagePull|CrashLoopBackOff|ImagePullBackOff)", re.IGNORECASE),
    ], "keep", priority=100,
))
KUBECTL_CONFIG.add_rule(ToolchainRule(
    "kubectl_watch", [
        re.compile(r"STATUS\s+RESTARTS"),
        re.compile(r"Running\s+\d+"),
    ], "fold", priority=50,
))
KUBECTL_CONFIG.add_rule(ToolchainRule(
    "kubectl_success", [
        re.compile(r"deployment\.apps\/.+created"),
        re.compile(r"service\/.+created"),
        re.compile(r"deployment\.apps\/.+configured"),
    ], "fold", priority=60,
))

# ============================================================
# 全栈注册表
# ============================================================

# 所有支持的工具链
ALL_TOOLCHAINS: Dict[str, ToolchainConfig] = {
    "npm": NPM_CONFIG,
    "yarn": YARN_CONFIG,
    "vite": VITE_CONFIG,
    "webpack": WEBPACK_CONFIG,
    "maven": MAVEN_CONFIG,
    "gradle": GRADLE_CONFIG,
    "springboot": SPRINGBOOT_CONFIG,
    "flutter": FLUTTER_CONFIG,
    "docker": DOCKER_CONFIG,
    "kubectl": KUBECTL_CONFIG,
}

# 工具链别名映射
TOOLCHAIN_ALIASES: Dict[str, str] = {
    "pnpm": "npm",
    "yarnpkg": "yarn",
    "vue-cli": "vite",
    "vue": "vite",
    "next": "vite",
    "nuxt": "vite",
    "mvn": "maven",
    "gradlew": "gradle",
    "boot": "springboot",
    "k8s": "kubectl",
    "helm": "kubectl",
}

# 中文错误关键词（跨工具链）
CHINESE_ERROR_KEYWORDS = [
    re.compile(r"错误"),
    re.compile(r"失败"),
    re.compile(r"找不到"),
    re.compile(r"拒绝访问"),
    re.compile(r"权限不足"),
    re.compile(r"连接超时"),
    re.compile(r"超时"),
    re.compile(r"不兼容"),
    re.compile(r"冲突"),
    re.compile(r"无法解析"),
    re.compile(r"模块未找到"),
    re.compile(r"编译失败"),
    re.compile(r"部署失败"),
    re.compile(r"未找到"),
    re.compile(r"缺失"),
    re.compile(r"无效"),
    re.compile(r"异常"),
    re.compile(r"报错"),
]


def detect_toolchain(output: str) -> Optional[str]:
    """自动检测终端输出对应的工具链。

    通过识别输出中的特征命令名和错误模式来判断。
    """
    # 第一轮：检查命令启动标记
    patterns = {
        "npm": [r"npm\s+(install|run|build|start|test|publish|audit)"],
        "yarn": [r"yarn\s+(install|add|remove|build|start)"],
        "vite": [r"vite\s+(dev|build|preview)"],
        "webpack": [r"webpack\s+(--config|--mode)", r"npx\s+webpack"],
        "maven": [r"mvn\s+(clean|install|package|compile|test)"],
        "gradle": [r"gradle\s+(build|run|clean|test|assemble)"],
        "springboot": [r"spring-boot:run", r"java\s+-jar\s+.*\.jar", r"mvn\s+spring-boot"],
        "flutter": [r"flutter\s+(run|build|test|pub|analyze)"],
        "docker": [r"docker\s+(build|run|push|pull|compose)"],
        "kubectl": [r"kubectl\s+(get|apply|describe|logs|delete)"],
    }

    first_line = output.strip().split("\n")[0] if output else ""
    for tool, pats in patterns.items():
        for pat in pats:
            if re.search(pat, first_line, re.IGNORECASE):
                return tool

    # 第二轮：检查特征错误消息
    for tool, config in ALL_TOOLCHAINS.items():
        for marker in config.error_markers:
            if marker.lower() in output.lower():
                return tool

    return None


def get_config(name: str) -> Optional[ToolchainConfig]:
    """通过名称或别名获取工具链配置。"""
    resolved = TOOLCHAIN_ALIASES.get(name, name)
    return ALL_TOOLCHAINS.get(resolved)


def current_toolchains() -> List[str]:
    """返回当前支持的所有工具链名称列表。"""
    return list(ALL_TOOLCHAINS.keys())
