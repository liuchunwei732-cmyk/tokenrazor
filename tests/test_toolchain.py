"""工具链规则库测试。"""

import re

from tokenrazor.toolchain import (
    ALL_TOOLCHAINS,
    TOOLCHAIN_ALIASES,
    CHINESE_ERROR_KEYWORDS,
    ToolchainConfig,
    detect_toolchain,
    get_config,
    current_toolchains,
)


class TestToolchainConfig:

    def test_npm_has_rules(self):
        """npm 配置应有规则。"""
        npm = ALL_TOOLCHAINS.get("npm")
        assert npm is not None
        assert len(npm.rules) > 0

    def test_npm_detects_error(self):
        """npm 错误应匹配 keep 动作。"""
        npm = get_config("npm")
        action = npm.match("npm ERR! code ENOENT")
        assert action == "keep"

    def test_npm_warning_matches(self):
        """npm 警告应匹配 fold 动作。"""
        npm = get_config("npm")
        action = npm.match("npm WARN deprecated core-js@2.6.12")
        assert action == "fold"

    def test_maven_error_matches(self):
        """Maven 错误应匹配 keep。"""
        maven = get_config("maven")
        action = maven.match("BUILD FAILURE")
        assert action == "keep"

    def test_maven_info_matches(self):
        """Maven INFO 应匹配 fold。"""
        maven = get_config("maven")
        action = maven.match("[INFO] Scanning for projects...")
        assert action == "fold"

    def test_flutter_has_rules(self):
        """Flutter 应有规则。"""
        flutter = ALL_TOOLCHAINS.get("flutter")
        assert flutter is not None
        assert len(flutter.rules) > 0

    def test_docker_has_rules(self):
        """Docker 应有规则。"""
        docker = ALL_TOOLCHAINS.get("docker")
        assert docker is not None
        assert len(docker.rules) > 0

    def test_kubectl_has_rules(self):
        """kubectl 应有规则。"""
        kubectl = ALL_TOOLCHAINS.get("kubectl")
        assert kubectl is not None
        assert len(kubectl.rules) > 0

    def test_gradle_has_rules(self):
        """Gradle 应有规则。"""
        gradle = ALL_TOOLCHAINS.get("gradle")
        assert gradle is not None
        assert len(gradle.rules) > 0

    def test_springboot_has_rules(self):
        """Spring Boot 应有规则。"""
        sb = ALL_TOOLCHAINS.get("springboot")
        assert sb is not None
        assert len(sb.rules) > 0

    def test_vite_has_rules(self):
        """Vite 应有规则。"""
        vite = ALL_TOOLCHAINS.get("vite")
        assert vite is not None
        assert len(vite.rules) > 0

    def test_webpack_has_rules(self):
        """Webpack 应有规则。"""
        wp = ALL_TOOLCHAINS.get("webpack")
        assert wp is not None
        assert len(wp.rules) > 0

    def test_yarn_alias(self):
        """yarn 应能解析。"""
        config = get_config("yarn")
        assert config is not None
        assert config.name == "yarn"

    def test_pnpm_alias(self):
        """pnpm 应映射到 npm。"""
        config = get_config("pnpm")
        assert config is not None
        assert config.name == "npm"

    def test_mvn_alias(self):
        """mvn 应映射到 maven。"""
        config = get_config("mvn")
        assert config is not None
        assert config.name == "maven"


class TestDetectToolchain:

    def test_detect_npm_install(self):
        """npm install 应被检测为 npm。"""
        result = detect_toolchain("npm install react")
        assert result == "npm"

    def test_detect_npm_run(self):
        result = detect_toolchain("npm run build")
        assert result == "npm"

    def test_detect_mvn(self):
        result = detect_toolchain("mvn clean install")
        assert result == "maven"

    def test_detect_flutter(self):
        result = detect_toolchain("flutter build ios")
        assert result == "flutter"

    def test_detect_docker(self):
        result = detect_toolchain("docker build -t myapp .")
        assert result == "docker"

    def test_detect_kubectl(self):
        result = detect_toolchain("kubectl get pods")
        assert result == "kubectl"

    def test_detect_by_error_pattern(self):
        """即使没有命令头，有错误模式也应能检测。"""
        result = detect_toolchain("npm ERR! code ENOENT")
        assert result == "npm"

    def test_detect_unknown(self):
        """无法识别的输出应返回 None。"""
        result = detect_toolchain("Hello, world!")
        assert result is None


class TestChineseKeywords:

    def test_chinese_error_pattern(self):
        """中文错误关键词应能匹配。"""
        for pat in CHINESE_ERROR_KEYWORDS:
            if pat.search("错误：找不到模块"):
                break
        else:
            pytest.fail("没有匹配 '错误' 的中文关键词")

    def test_multiple_chinese_keywords(self):
        """多个中文关键词应都能匹配。"""
        test_cases = ["错误", "失败", "找不到", "超时", "异常", "报错", "缺失", "无效"]
        for case in test_cases:
            matched = any(pat.search(case) for pat in CHINESE_ERROR_KEYWORDS)
            assert matched, f"中文关键词 '{case}' 未被匹配"


class TestCurrentToolchains:

    def test_all_toolchains_listed(self):
        """工具链列表应包含主要工具。"""
        chains = current_toolchains()
        assert "npm" in chains
        assert "maven" in chains
        assert "flutter" in chains
        assert "docker" in chains
        assert len(chains) == len(ALL_TOOLCHAINS)
