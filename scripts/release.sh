#!/bin/bash
# TokenRazor PyPI 发布脚本
# 用法: bash scripts/release.sh
# 前置条件: 在 GitHub 仓库设置 PYPI_API_TOKEN

set -e

VERSION=$(python3 -c "from tokenrazor import __version__; print(__version__)")
echo "📦 准备发布 TokenRazor v$VERSION"

# 1. 确认测试通过
echo ""
echo "── 1. 运行测试 ──"
python3 -m pytest tests/ -q --tb=short || { echo "❌ 测试失败"; exit 1; }
echo "✅ 测试通过"

# 2. 构建包
echo ""
echo "── 2. 构建 ──"
python3 -m build
echo "✅ 构建成功"

# 3. 检查包内容
echo ""
echo "── 3. 检查 ──"
python3 -m twine check dist/* 2>/dev/null || echo "⚠️ twine 未安装，跳过检查"

# 4. 发布说明
echo ""
echo "── 4. 发布准备 ──"
echo ""
echo "  执行以下步骤发布到 PyPI:"
echo ""
echo "  a) 在 GitHub 仓库设置:"
echo "     Settings → Secrets and variables → Actions"
echo "     添加 PYPI_API_TOKEN"
echo ""
echo "  b) 创建并推送标签:"
echo "     git tag v$VERSION"
echo "     git push origin v$VERSION"
echo ""
echo "  c) CI/CD 会自动发布到 PyPI"
echo "     同时 GitHub Release 会自动创建"
echo ""
echo "  或者在本地发布:"
echo "     pip install twine"
echo "     twine upload dist/tokenrazor-$VERSION*"
echo ""
echo "🎉 准备工作就绪"
