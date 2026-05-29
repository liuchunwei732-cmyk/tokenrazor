"""配置文件支持。

支持三级配置合并（优先级从高到低）：
1. 命令行参数
2. 项目级配置 (.tokenrazor.yaml)
3. 用户级配置 (~/.tokenrazor.yaml)
"""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from pydantic import BaseModel, Field


class PruneConfig(BaseModel):
    """剪枝命令默认配置。"""
    strategies: List[str] = Field(default=["filler", "dead_end", "parallel_enum"])
    model: str = "gpt-4o"
    strict: bool = True
    score: bool = False


class FilterConfig(BaseModel):
    """过滤命令默认配置。"""
    toolchain: Optional[str] = None
    stats: bool = True
    project: str = "auto"


class Config(BaseModel):
    """TokenRazor 配置。"""
    version: str = "1.0"
    prune: PruneConfig = PruneConfig()
    filter: FilterConfig = FilterConfig()
    ignored_patterns: List[str] = Field(default_factory=list)
    extra_fold_patterns: List[str] = Field(default_factory=list)


# 配置文件搜索路径
CONFIG_FILENAMES = [".tokenrazor.yaml", ".tokenrazor.yml", ".tokenrazor.json"]
USER_CONFIG_PATH = Path.home() / ".tokenrazor.yaml"


def find_project_config(start_dir: str = ".") -> Optional[Path]:
    """从当前目录向上搜索项目级配置文件。"""
    current = Path(start_dir).resolve()
    for _ in range(10):  # 最多向上 10 层
        for name in CONFIG_FILENAMES:
            config_path = current / name
            if config_path.is_file():
                return config_path
        parent = current.parent
        if parent == current:
            break
        current = parent
    return None


def load_config(project_dir: str = ".", cli_overrides: Optional[Dict[str, Any]] = None) -> Config:
    """加载并合并配置。

    合并顺序：默认值 ← 用户配置 ← 项目配置 ← CLI 参数
    """
    config = Config()

    # 1. 加载用户级配置
    if USER_CONFIG_PATH.is_file():
        try:
            with open(USER_CONFIG_PATH, "r", encoding="utf-8") as f:
                raw = yaml.safe_load(f)
            if raw:
                user_config = Config.model_validate(raw)
                config = _merge_config(config, user_config)
        except Exception:
            pass

    # 2. 加载项目级配置
    project_config_path = find_project_config(project_dir)
    if project_config_path:
        try:
            with open(project_config_path, "r", encoding="utf-8") as f:
                raw = yaml.safe_load(f)
            if raw:
                proj_config = Config.model_validate(raw)
                config = _merge_config(config, proj_config)
        except Exception:
            pass

    # 3. 应用 CLI 覆盖
    if cli_overrides:
        config = _apply_overrides(config, cli_overrides)

    return config


def _merge_config(base: Config, override: Config) -> Config:
    """合并两个配置，override 优先。"""
    result = base.model_copy(deep=True)

    # 合并 prune 配置
    if override.prune.strategies != PruneConfig().strategies:
        result.prune.strategies = override.prune.strategies
    if override.prune.model != PruneConfig().model:
        result.prune.model = override.prune.model
    if override.prune.strict != PruneConfig().strict:
        result.prune.strict = override.prune.strict
    if override.prune.score != PruneConfig().score:
        result.prune.score = override.prune.score

    # 合并 filter 配置
    if override.filter.toolchain is not None:
        result.filter.toolchain = override.filter.toolchain
    if override.filter.stats != FilterConfig().stats:
        result.filter.stats = override.filter.stats

    # 合并忽略/折叠规则
    if override.ignored_patterns:
        result.ignored_patterns = list(set(result.ignored_patterns + override.ignored_patterns))
    if override.extra_fold_patterns:
        result.extra_fold_patterns = list(set(result.extra_fold_patterns + override.extra_fold_patterns))

    return result


def _apply_overrides(config: Config, overrides: Dict[str, Any]) -> Config:
    """应用 CLI 参数覆盖。"""
    result = config.model_copy(deep=True)

    if "model" in overrides and overrides["model"]:
        result.prune.model = overrides["model"]
    if "strategy" in overrides and overrides["strategy"]:
        result.prune.strategies = list(overrides["strategy"])
    if "no_strict" in overrides and overrides["no_strict"]:
        result.prune.strict = False
    if "score" in overrides and overrides["score"]:
        result.prune.score = True

    return result


def generate_default_config() -> str:
    """生成默认配置文件内容。"""
    return """# TokenRazor 配置文件
# 放在项目根目录 (.tokenrazor.yaml) 或用户目录 (~/.tokenrazor.yaml)

version: "1.0"

# 剪枝命令默认配置
prune:
  strategies:
    - filler
    - dead_end
    - parallel_enum
  model: "gpt-4o"        # 默认模型（用于费用估算）
  strict: true            # 严格模式（answer 不变才放行）
  score: false            # 默认是否显示质量评分

# 过滤命令默认配置
filter:
  toolchain: null         # 指定工具链（null = 自动检测）
  stats: true             # 默认显示统计
  project: "auto"         # 项目类型（auto = 自动检测）

# 额外忽略模式（追加到内置列表）
ignored_patterns: []

# 额外折叠模式
extra_fold_patterns: []
"""
