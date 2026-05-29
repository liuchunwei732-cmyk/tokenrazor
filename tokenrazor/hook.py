"""Pre-commit hook 支持。

生成 `.pre-commit-config.yaml` 配置片段，
让 TokenRazor 自动剪枝 AI 生成的代码提交。
"""

PRE_COMMIT_CONFIG = """# TokenRazor pre-commit hook
# 添加到你的 .pre-commit-config.yaml 中
- repo: local
  hooks:
    - id: tokenrazor-prune
      name: TokenRazor - Prune AI output
      entry: tokenrazor prune --score --model gpt-4o
      language: system
      types: [text]
      pass_filenames: false
      always_run: true
"""

HOOK_SCRIPT = """#!/bin/bash
# TokenRazor pre-commit hook
# 自动剪枝 git diff 中的 AI 生成内容

set -e

# 获取暂存区的文本文件变更
CHANGED_FILES=$(git diff --cached --name-only --diff-filter=ACM | grep -E '\\.(py|js|ts|jsx|tsx|go|rs|java)$' || true)

if [ -z "$CHANGED_FILES" ]; then
    exit 0
fi

echo "🧹 TokenRazor: 检查 AI 生成内容..."

for file in $CHANGED_FILES; do
    if [ -f "$file" ]; then
        # 对每个文件执行剪枝（仅报告，不自动修改）
        PRUNED=$(tokenrazor prune --score --json < "$file" 2>/dev/null || true)
        if [ -n "$PRUNED" ]; then
            SAVED=$(echo "$PRUNED" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('compression',{}).get('saved_percent',0))" 2>/dev/null || echo "0")
            if [ "$SAVED" != "0" ]; then
                echo "  ⚠ $file: 可节省 ${SAVED}% tokens"
            fi
        fi
    fi
done

echo "✅ TokenRazor: 检查完成"
"""


def generate_pre_commit_config() -> str:
    """生成 pre-commit 配置片段。"""
    return PRE_COMMIT_CONFIG


def generate_hook_script() -> str:
    """生成 hook 脚本内容。"""
    return HOOK_SCRIPT


def install_hook(target_dir: str = ".") -> str:
    """在目标目录安装 pre-commit hook。"""
    from pathlib import Path

    target = Path(target_dir) / ".git" / "hooks" / "pre-commit"
    target.parent.mkdir(parents=True, exist_ok=True)

    script = f"""#!/bin/bash
# TokenRazor pre-commit hook
# Installed by: tokenrazor hook --install

{HOOK_SCRIPT}
"""

    target.write_text(script, encoding="utf-8")
    target.chmod(0o755)

    return str(target)
