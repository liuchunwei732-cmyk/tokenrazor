# TokenRazor 真实用户测试计划

## 测试目标

在真实开发场景中验证 TokenRazor 的 token 节省效果和用户体验。

## 测试角色

| 角色 | 用户画像 | 典型场景 |
|------|---------|---------|
| AI 编程重度用户 | 每天用 Cursor/Claude Code 4h+ | CoT 剪枝 |
| 全栈开发者 | 频繁 npm/maven 构建 | 终端日志过滤 |
| 中文开发者 | 国产模型用户 | 中文 CoT + 国内镜像 |

## 测试场景

### 场景 A：CoT 剪枝（核心场景）

```bash
# 1. 从 Cursor/Claude Code 复制一段 AI 输出
# 2. 管道送入 TokenRazor
cat ai_output.txt | tokenrazor prune --model gpt-4o > pruned.txt

# 3. 记录数据
echo "原始: $(wc -c < ai_output.txt) 字符"
echo "剪后: $(wc -c < pruned.txt) 字符"
```

**记录指标：**
- 压缩率（%）
- 内容是否保留关键信息
- 处理时间

### 场景 B：终端日志过滤

```bash
# 1. 执行一个真实构建
npm run build 2>&1 | tee build.log

# 2. 过滤日志
cat build.log | tokenrazor filter --stats > filtered.log

# 3. 对比
echo "原始行数: $(wc -l < build.log)"
echo "过滤后行数: $(wc -l < filtered.log)"
```

**记录指标：**
- 行数压缩率
- 关键错误是否保留
- 误过滤情况

### 场景 C：每日节省统计

```bash
# 记录每天的使用
# 方法 1: 在 ~/.zshrc 中添加统计
alias rzp="tokenrazor prune --model gpt-4o --json >> ~/.tokenrazor-usage.json"

# 方法 2: 手动记录
# 日期 | 场景 | 原始 token | 剪后 token | 节省
```

## 预期指标

| 指标 | 目标值 | 测量方式 |
|------|-------|---------|
| CoT 压缩率 | ≥20% | `prune --json` 的 stats |
| 终端过滤率 | ≥50% | `filter --stats` |
| 误删率 | ≤5% | 用户主观反馈 |
| 处理延迟 | <100ms | `time` 命令 |
| 安装成功率 | 100% | `pip install` |

## 反馈收集

使用 3 天后，收集以下反馈：

1. **功能满意度**（1-5）：剪枝效果满意吗？
2. **性能满意度**（1-5）：速度可以接受吗？
3. **最有用场景**：哪个场景省最多？
4. **最需要改进**：什么功能需要加？
5. **安装体验**：安装过程有遇到问题吗？

## 测试数据文件

所有测试数据保存在 `tests/fixtures/` 目录：

```
tests/fixtures/
├── samples.py           # 现有测试样本
├── real_cot_1.txt       # 真实 CoT 输出样本
├── real_build_log.txt   # 真实构建日志
└── user_feedback.md     # 用户反馈汇总
```
