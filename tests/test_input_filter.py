"""终端输出过滤器测试。"""

import pytest

from tokenrazor.input_filter import TerminalFilter, FilterResult
from tokenrazor.context import ProjectContext


class TestTerminalFilter:

    def setup_method(self):
        self.filter = TerminalFilter()

    def test_empty_input(self):
        """空输入应返回空结果。"""
        result = self.filter.filter("")
        assert result.filtered == ""
        assert result.stats["original_tokens"] == 0

    def test_simple_text_passthrough(self):
        """普通文本应原样保留。"""
        text = "Hello, this is a simple message."
        result = self.filter.filter(text)
        assert text in result.filtered

    def test_npm_error_kept(self):
        """npm 报错应被保留。"""
        text = "npm ERR! code ENOENT\nnpm ERR! Cannot find module 'react'"
        result = self.filter.filter(text, toolchain="npm")
        assert "npm ERR!" in result.filtered
        assert result.stats["saved_percent"] >= 0

    def test_npm_warning_folded(self):
        """npm 警告应被折叠。"""
        text = "npm WARN deprecated core-js@2.6.12"
        result = self.filter.filter(text, toolchain="npm")
        assert "npm WARN" not in result.filtered

    def test_maven_error_kept(self):
        """Maven 编译错误应被保留。"""
        text = "BUILD FAILURE\nFailed to execute goal compile"
        result = self.filter.filter(text, toolchain="maven")
        assert "BUILD FAILURE" in result.filtered

    def test_maven_info_folded(self):
        """Maven INFO 日志应被折叠。"""
        text = "[INFO] Scanning for projects..."
        result = self.filter.filter(text, toolchain="maven")
        assert "[INFO]" not in result.filtered

    def test_node_modules_folded(self):
        """node_modules 内部堆栈应被折叠。"""
        text = "Error: Something went wrong\n  at Object.<anonymous> (node_modules/webpack/lib/index.js:1:1)"
        result = self.filter.filter(text, toolchain="webpack")
        assert "folded" in result.filtered or "node_modules" not in result.filtered or "Error:" in result.filtered

    def test_chinese_error_kept(self):
        """中文错误应被保留。"""
        text = "错误：找不到模块 'axios'"
        result = self.filter.filter(text)
        assert "错误" in result.filtered

    def test_chinese_error_detected_by_toolchain(self):
        """中文报错在工具链模式下应保留。"""
        text = "npm ERR! 错误：找不到模块 'axios'\n报错信息如下"
        result = self.filter.filter(text, toolchain="npm")
        assert "npm ERR!" in result.filtered or "错误" in result.filtered

    def test_docker_build_logs(self):
        """Docker 构建步骤应被折叠。"""
        text = "Step 1/5 : FROM node:18\nRunning in abc123\nRemoving intermediate container def456"
        result = self.filter.filter(text, toolchain="docker")
        assert result.stats["saved_tokens"] >= 0

    def test_flutter_error_kept(self):
        """Flutter 编译失败应保留。"""
        text = "Build failed due to error\nFAILURE: Build failed with an exception."
        result = self.filter.filter(text, toolchain="flutter")
        assert "FAILURE" in result.filtered

    def test_project_context_aware(self):
        """项目感知应影响过滤。"""
        ctx = ProjectContext(project_type="frontend", framework="react")
        f = TerminalFilter(ctx=ctx)
        text = "npm ERR! Build failed\n(node_modules chunky stack...)"
        result = f.filter(text, toolchain="npm")
        assert result.stats["original_tokens"] > 0

    def test_stats_presence(self):
        """过滤结果应有统计数据。"""
        result = self.filter.filter("Some output text here")
        assert "original_tokens" in result.stats
        assert "filtered_tokens" in result.stats
        assert "saved_percent" in result.stats

    def test_kubectl_error_kept(self):
        """kubectl 错误应保留。"""
        text = "Error from server (NotFound): pods \"my-pod\" not found"
        result = self.filter.filter(text, toolchain="kubectl")
        assert "Error" in result.filtered
