#!/bin/bash
# TokenRazor 商业级验证脚本
# 其他 AI 助手可直接运行此脚本验证项目是否完善
# 用法: cd tokenrazor/ && bash verify.sh

PASS=0
FAIL=0

green() { echo "✅ $1"; ((PASS++)); }
red() { echo "❌ $1"; ((FAIL++)); }
check_cmd() { eval "$1" && green "$2" || red "$3"; }

echo "═══════════════════════════════════════════"
echo "  TokenRazor v0.5.0 商业级验证"
echo "═══════════════════════════════════════════"
echo ""

# 1. 安装验证
echo "── 1. 安装 ──"
if python3 -c "from tokenrazor import __version__; print(f'  版本: {__version__}')" 2>/dev/null; then
    green "包可导入"
else
    red "包导入失败"
fi

VER=$(python3 -m tokenrazor --version 2>&1)
if echo "$VER" | grep -q "0.5"; then
    green "版本号正确 (0.5.0)"
else
    red "版本号错误 (输出: $VER)"
fi

# 2. CLI 命令验证
echo ""
echo "── 2. CLI 命令 ──"
HELP=$(python3 -m tokenrazor --help 2>&1)
echo "$HELP" | grep -q "prune"    && green "prune 命令可用"    || red "prune 命令缺失"
echo "$HELP" | grep -q "filter"   && green "filter 命令可用"   || red "filter 命令缺失"
echo "$HELP" | grep -q "demo"     && green "demo 命令可用"     || red "demo 命令缺失"
echo "$HELP" | grep -q "integrate" && green "integrate 命令可用" || red "integrate 命令缺失"

# 3. 核心功能验证
echo ""
echo "── 3. 核心功能 ──"
RESULT=$(echo '让我想想。答案：42' | python3 -m tokenrazor prune --model gpt-4o 2>&1 || true)
echo "$RESULT" | grep -q "TokenRazor" && green "prune 管道输入正常" || red "prune 管道输入失败"
echo "$RESULT" | grep -q "节省" && green "费用显示正常" || red "费用显示缺失"

DEMO=$(python3 -m tokenrazor demo 2>&1 || true)
echo "$DEMO" | grep -q "统计" && green "demo 命令正常" || red "demo 命令失败"

# 4. 测试验证
echo ""
echo "── 4. 测试 ──"
TEST_OUT=$(python3 -m pytest tests/ -q --tb=short 2>&1 || true)
TEST_COUNT=$(echo "$TEST_OUT" | grep -oE '^[0-9]+ passed' | grep -oE '^[0-9]+' || echo "0")
echo "  通过测试: $TEST_COUNT"
[ "$TEST_COUNT" -ge 100 ] 2>/dev/null && green "测试覆盖达标 (≥100)" || red "测试数量不足 (<100)"

COV_OUT=$(python3 -m pytest tests/ --cov=tokenrazor --cov-report=term 2>&1 || true)
COV_PCT=$(echo "$COV_OUT" | grep TOTAL | awk '{print $4}' | tr -d '%')
echo "  代码覆盖率: ${COV_PCT}%"
[ "${COV_PCT:-0}" -ge 85 ] 2>/dev/null && green "覆盖率达标 (≥85%)" || red "覆盖率不足 (<85%)"

# 5. 文件完整性验证
echo ""
echo "── 5. 文件完整性 ──"
[ -f "README.md" ]      && green "README.md 存在"      || red "README.md 缺失"
[ -f "LICENSE" ]        && green "LICENSE 存在 (MIT)"  || red "LICENSE 缺失"
[ -f "CHANGELOG.md" ]   && green "CHANGELOG.md 存在"   || red "CHANGELOG.md 缺失"
grep -q "0.5.0" pyproject.toml 2>/dev/null && green "pyproject.toml 版本正确" || red "pyproject.toml 版本错误"
[ -f ".github/workflows/ci.yml" ] && green "CI/CD 配置存在" || red "CI/CD 配置缺失"
[ -f ".gitignore" ]     && green ".gitignore 存在"      || red ".gitignore 缺失"

# 6. PyPI 构建验证
echo ""
echo "── 6. PyPI 构建 ──"
BUILD_OUT=$(python3 -m build 2>&1 || true)
echo "$BUILD_OUT" | tail -1 | grep -q "Successfully" && green "PyPI 构建成功" || red "PyPI 构建失败"

echo ""
echo "═══════════════════════════════════════════"
echo "  结果: $PASS 通过 / $FAIL 失败 / $((PASS+FAIL)) 总计"
echo "═══════════════════════════════════════════"
[ "$FAIL" -eq 0 ] && echo "🎉 全部通过，商业级就绪" || echo "⚠️ 存在 $FAIL 个问题需要修复"
exit $FAIL
