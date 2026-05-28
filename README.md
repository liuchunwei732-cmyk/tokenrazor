<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://img.shields.io/badge/TokenRazor-v0.5.0-4A90D9?style=flat-square&logo=python&logoColor=white">
    <img alt="TokenRazor" src="https://img.shields.io/badge/TokenRazor-v0.5.0-4A90D9?style=flat-square&logo=python&logoColor=white">
  </picture>
</p>

<p align="center">
  <b>🧹 AI 编程的上下文智能编排层</b><br>
  剪枝 CoT · 过滤终端输出 · 项目感知<br>
  不只省 Token，更让 AI 看懂你的项目
</p>

<p align="center">
  <a href="#"><img src="https://img.shields.io/github/actions/workflow/status/liuchunwei732-cmyk/tokenrazor/ci.yml?style=flat-square&logo=github" alt="CI"></a>
  <a href="https://pypi.org/project/tokenrazor/"><img src="https://img.shields.io/pypi/v/tokenrazor?style=flat-square&logo=pypi" alt="PyPI"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue.svg?style=flat-square" alt="License"></a>
  <a href="#"><img src="https://img.shields.io/badge/python-3.9+-blue.svg?style=flat-square&logo=python" alt="Python"></a>
  <a href="#"><img src="https://img.shields.io/badge/coverage-85%25-brightgreen?style=flat-square" alt="Coverage"></a>
</p>

---

**English** · [中文版](#-中文文档)

TokenRazor is your AI programming **context orchestrator**. It sits between your terminal and your AI, reducing token waste at three levels:

| Level | What it does | Typical savings |
|-------|-------------|-----------------|
| 🗜️ **Output** | Prune verbose CoT chains (DeepSeek R1 / Claude / o1) | 20–35% |
| 🧹 **Input** | Filter terminal noise, keep only errors and key info | 50–80% |
| 🧠 **Context** | Project-aware scan, generate AI-friendly snapshots | 30–60% combined |

### Quick Demo

```bash
# Prune an AI CoT output
curl -s https://raw.githubusercontent.com/liuchunwei732-cmyk/tokenrazor/main/demo/cot.txt | tokenrazor prune --model gpt-4o

# Filter a build log
make 2>&1 | tokenrazor filter --stats

# See savings immediately
tokenrazor demo
```

### Installation

```bash
pip install tokenrazor
# or
pip3 install tokenrazor
```

### Commands

| Command | Description |
|---------|-------------|
| `prune` | Prune AI output — strip filler, dead ends, parallel enums |
| `filter` | Filter terminal output — keep errors, fold noise |
| `demo` | Built-in demo — see savings in 3 seconds |
| `tokens` | Count tokens in any text or file |
| `scan` | Scan project — detect framework, toolchain, rules |
| `snapshot` | Generate project snapshot for AI context |
| `integrate` | Generate shell aliases for daily use |

### Usage Examples

**1. Prune AI CoT output (save 20-35%)**

```bash
# Pipe AI response directly
cat ai_response.txt | tokenrazor prune --model claude-3.5-sonnet

# With diff to see what was removed
echo "Let me think... method A... method B... method C... I'll pick C." | tokenrazor prune --diff
```

<details>
<summary>👆 Click to see before/after</summary>

**Before** (DeepSeek R1 style, 1085 tokens):
```
<thinking>
让我想想这个问题如何解决。
首先分析需求。
方法一：方案A。这是最直接的方法...
方法二：方案B。虽然复杂但更稳定...
方法三：方案C。综合了前两者的优点...
我选择方案三。
好的开始写代码。先定义函数...
等等让我再确认一下边界条件...
嗯，没问题了。
</thinking>
最终答案：方案C
```

**After** (736 tokens, **32.2% saved**, ~$0.26/month for 1000 calls):
```
让我想想这个问题如何解决。
首先分析需求。

方法三：方案C。综合了前两者的优点...
我选择方案三。
好的开始写代码。先定义函数...

最终答案：方案C
```
</details>

**2. Filter terminal output (save 50-80%)**

```bash
# Filter build logs before sending to AI
npm run build 2>&1 | tokenrazor filter --stats

# Save to file
make 2>&1 | tokenrazor filter -o cleaned_log.txt
```

**3. Integrate into your shell**

```bash
# Generate aliases
tokenrazor integrate -o ~/.tokenrazor.sh
echo 'source ~/.tokenrazor.sh' >> ~/.zshrc

# Now use shortcuts
cat output.txt | rzp              # prune
make 2>&1 | rzf                   # filter
cat output.txt | rzp-r1           # prune with DeepSeek pricing
```

### Supported Models (Pricing)

| Model | Input $/1M | Output $/1M |
|-------|-----------|------------|
| GPT-4o | $2.50 | $10.00 |
| Claude 3.5 Sonnet | $3.00 | $15.00 |
| DeepSeek R1 | $0.55 | $2.19 |
| DeepSeek V4 | $0.25 | $0.80 |
| Kimi k1.5 | $1.00 | $4.00 |
| Gemini 2.0 Flash | $0.10 | $0.40 |
| Qwen Max | $2.00 | $8.00 |

### Supported Toolchains (Input Filter)

| Type | Tools |
|------|-------|
| JavaScript | npm, yarn, pnpm, cnpm, vite, webpack |
| Java | maven, gradle |
| Python | pip (including domestic mirrors) |
| Mobile | Flutter, uni-app |
| Ops | Docker, kubectl |
| Chinese | Ali/TC/HW mirrors, cnpm, taro, umi, ice.js |

---

## 🇨🇳 中文文档

<p align="center">
  <b>🧹 TokenRazor — 让你和 AI 的每一分钱都花在刀刃上</b>
</p>

### 这工具是干啥的？

你在用 Cursor / Claude Code / DeepSeek 写代码时，有大量 token 被浪费在：

- AI 的**自言自语**（"让我想想...方法一...方法二..."，然后它选第三个）
- 终端的**垃圾日志**（npm WARN / node_modules / 几百行 INFO）
- 对话历史里的**废话累积**

TokenRazor 就是干这个的：**剪掉多余的，留下有用的。**

### 安装

```bash
pip install tokenrazor
```

### 一分钟上手

```bash
# 看看效果
tokenrazor demo

# 日常剪枝 AI 输出（省 20-35%）
cat ai_output.txt | tokenrazor prune

# 过滤终端日志（省 50-80%）
npm run build 2>&1 | tokenrazor filter --stats

# 集成到 shell
tokenrazor integrate -o ~/.tokenrazor.sh
echo 'source ~/.tokenrazor.sh' >> ~/.zshrc
```

### 命令一览

| 命令 | 作用 |
|------|------|
| `prune` | 剪枝 AI 的思维链，去掉废话保留结论 |
| `filter` | 过滤终端输出，只看关键信息 |
| `demo` | 内置演示，一秒看效果 |
| `tokens` | 统计 Token 数 |
| `scan` | 扫描项目，自动识别框架和工具链 |
| `snapshot` | 生成项目快照，方便 AI 理解上下文 |
| `integrate` | 生成 shell 别名，一键集成 |

### 省多少钱？

按每天调用 100 次、每次省 300 tokens 算：

| 模型 | 每天省 | 每月省 |
|------|--------|--------|
| DeepSeek R1 ($0.55/M) | $0.02 | $0.50 |
| GPT-4o ($2.50/M) | $0.08 | $2.25 |
| Claude 3.5 ($3.00/M) | $0.09 | $2.70 |

> 当工具链用上 filter 后，input token 减少 80%，省得更多。
> 核心价值不在省钱——在**上下文窗口不爆**和**AI 回复质量更高**。

### 适用场景

- **Cursor / Claude Code / Aider 用户**：管道剪枝思考链，保留最终代码
- **AI 编程重度用户**：每天节省数万 token
- **多 Agent 协作**：子 Agent 通信前脱水，减少无用传递
- **中文开发者**：原生支持中文 CoT 和国内工具链

### 为什么不用 Rust 写？

因为这不是性能瓶颈。一次 AI 回复 3-30 秒，剪枝花 5ms。Rust 省 4.9ms 用户体验为零。
**先让东西能用，再让东西快。**

---

<p align="center">
  Made with 🧹 by <a href="https://github.com/liuchunwei732-cmyk">Kevin Liu</a><br>
  <sub>MIT Licensed — go ahead, fork it, ship it, save tokens.</sub>
</p>
