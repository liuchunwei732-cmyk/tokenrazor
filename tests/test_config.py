"""配置和 Hook 模块测试。"""

import tempfile
import yaml
from pathlib import Path

from tokenrazor.config import Config, load_config, generate_default_config, find_project_config


class TestConfig:
    def test_default_config(self):
        """默认配置应有合理的默认值。"""
        cfg = Config()
        assert cfg.version == "1.0"
        assert "filler" in cfg.prune.strategies
        assert "dead_end" in cfg.prune.strategies
        assert cfg.prune.strict is True

    def test_generate_default_config(self):
        """生成的配置文件应是有效 YAML。"""
        content = generate_default_config()
        data = yaml.safe_load(content)
        assert data["version"] == "1.0"
        assert "prune" in data
        assert "filter" in data

    def test_load_config_from_yaml(self, tmp_path):
        """从 YAML 加载配置。"""
        config_file = tmp_path / ".tokenrazor.yaml"
        config_file.write_text("prune:\n  model: deepseek-r1\n  score: true\n")

        cfg = load_config(str(tmp_path))
        assert cfg.prune.model == "deepseek-r1"
        assert cfg.prune.score is True

    def test_find_project_config(self, tmp_path):
        """应在当前目录找到配置文件。"""
        config_file = tmp_path / ".tokenrazor.yaml"
        config_file.write_text("prune:\n  model: test\n")

        found = find_project_config(str(tmp_path))
        assert found is not None
        assert found.name == ".tokenrazor.yaml"

    def test_find_project_config_not_found(self, tmp_path):
        """无配置文件时应返回 None。"""
        found = find_project_config(str(tmp_path))
        assert found is None


class TestHook:
    def test_generate_pre_commit_config(self):
        """生成的 pre-commit 配置应包含 hook 定义。"""
        from tokenrazor.hook import generate_pre_commit_config
        config = generate_pre_commit_config()
        assert "tokenrazor-prune" in config
        assert "tokenrazor prune" in config

    def test_generate_hook_script(self):
        """生成的 hook 脚本应包含 bash shebang。"""
        from tokenrazor.hook import generate_hook_script
        script = generate_hook_script()
        assert script.startswith("#!/bin/bash")
        assert "tokenrazor" in script
