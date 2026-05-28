"""TokenRazor CLI 集成测试。"""

import sys
import json
from pathlib import Path
from click.testing import CliRunner

from tokenrazor.cli import main

runner = CliRunner()


class TestCliPrune:
    """prune 命令测试。"""

    def test_prune_stdin(self):
        """管道输入应该正常工作。"""
        result = runner.invoke(main, ["prune"], input="让我想想。方法一。方法二。方法三。选三。答案：C")
        assert result.exit_code == 0
        assert "TokenRazor" in result.output
        assert "答案" in result.output

    def test_prune_with_text(self):
        """--text 参数应该正常工作。"""
        result = runner.invoke(main, ["prune", "--text", "让我想想。答案：42"])
        assert result.exit_code == 0
        assert "TokenRazor" in result.output

    def test_prune_with_model(self):
        """--model 参数应影响费用显示。"""
        result = runner.invoke(main, ["prune", "--text", "方法一。方法二。方法三。选三。答案：B", "--model", "deepseek-r1"])
        assert result.exit_code == 0
        assert "$0.55" in result.output  # DeepSeek R1 价格

    def test_prune_json_output(self):
        """--json 应输出 JSON。"""
        result = runner.invoke(main, ["prune", "--text", "答案：42", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "compression" in data
        assert "pruned_text" in data

    def test_prune_output_file(self):
        """-o 应写入文件。"""
        with runner.isolated_filesystem():
            result = runner.invoke(main, ["prune", "--text", "答案：42", "-o", "out.txt"])
            assert result.exit_code == 0
            assert Path("out.txt").exists()

    def test_prune_diff(self):
        """--diff 应显示差异。"""
        result = runner.invoke(main, ["prune", "--text", "让我想想。答案：42", "--diff"])
        assert result.exit_code == 0
        # diff 模式包含原始文本和剪后文本
        assert "让我想想" in result.output
        assert "答案：42" in result.output


class TestCliFilter:
    """filter 命令测试。"""

    def test_filter_stdin(self):
        """管道输入应该工作。"""
        result = runner.invoke(main, ["filter"], input="[INFO] processing\n[ERROR] crash\n")
        assert result.exit_code == 0
        assert "crash" in result.output  # ERROR 应保留

    def test_filter_stats(self):
        """--stats 应显示统计信息。"""
        result = runner.invoke(main, ["filter", "--stats"],
                               input="[INFO] step 1\n[INFO] step 2\n[WARN] deprecated\n[ERROR] fail\n")
        assert result.exit_code == 0
        assert "过滤统计" in result.output

    def test_filter_json(self):
        """--json 应输出 JSON。"""
        result = runner.invoke(main, ["filter", "--json"],
                               input="[ERROR] crash\n")
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "filtered_text" in data
        assert "stats" in data

    def test_filter_keeps_errors(self):
        """ERROR 行不应被过滤。"""
        result = runner.invoke(main, ["filter"], input="[ERROR] Fatal: out of memory\n[INFO] done\n")
        assert result.exit_code == 0
        assert "Fatal" in result.output  # ERROR 保留
        assert "done" in result.output   # INFO 也保留（只是折叠，不删除）


class TestCliDemo:
    """demo 命令测试。"""

    def test_demo_basic(self):
        """demo 应运行并显示统计。"""
        result = runner.invoke(main, ["demo"])
        assert result.exit_code == 0
        assert "TokenRazor" in result.output
        assert "Token" in result.output

    def test_demo_with_model(self):
        """demo 应支持 --model 参数。"""
        result = runner.invoke(main, ["demo", "--model", "claude-3.5-sonnet"])
        assert result.exit_code == 0
        assert "claude" in result.output.lower() or "Claude" in result.output


class TestCliTokens:
    """tokens 命令测试。"""

    def test_tokens_basic(self):
        """tokens 应该计数。"""
        result = runner.invoke(main, ["tokens", "--text", "Hello World"])
        assert result.exit_code == 0
        assert "Tokens" in result.output

    def test_tokens_chinese(self):
        """中文也应正确计数。"""
        result = runner.invoke(main, ["tokens", "--text", "你好世界"])
        assert result.exit_code == 0
        assert "Tokens" in result.output


class TestCliIntegrate:
    """integrate 命令测试。"""

    def test_integrate_print(self):
        """integrate 应打印 shell 脚本。"""
        result = runner.invoke(main, ["integrate"])
        assert result.exit_code == 0
        assert "alias rzprune" in result.output

    def test_integrate_output_file(self):
        """integrate -o 应写入文件。"""
        with runner.isolated_filesystem():
            result = runner.invoke(main, ["integrate", "-o", "razor.sh"])
            assert result.exit_code == 0
            assert Path("razor.sh").exists()
            content = Path("razor.sh").read_text()
            assert "alias rzprune" in content


class TestCliVersion:
    """版本命令测试。"""

    def test_version(self):
        result = runner.invoke(main, ["--version"])
        assert result.exit_code == 0
        assert "0.5.0" in result.output or "tokenrazor" in result.output


class TestCliHelp:
    """帮助命令测试。"""

    def test_help(self):
        result = runner.invoke(main, ["--help"])
        assert result.exit_code == 0
        assert "prune" in result.output
        assert "filter" in result.output

    def test_prune_help(self):
        result = runner.invoke(main, ["prune", "--help"])
        assert result.exit_code == 0
        assert "剪枝" in result.output or "Prune" in result.output


class TestCliScan:
    """scan 命令测试。"""

    def test_scan_current_dir(self):
        """scan 应扫描当前目录。"""
        result = runner.invoke(main, ["scan", "."])
        assert result.exit_code == 0
        assert "项目" in result.output or "scan" in result.output.lower()

    def test_scan_json(self):
        """scan --json 应输出 JSON。"""
        result = runner.invoke(main, ["scan", ".", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "project_type" in data
