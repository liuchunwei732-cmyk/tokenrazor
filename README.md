<div align="center">
  <h1>🧹 TokenRazor</h1>
  <p><em>AI 编程的上下文智能编排层</em></p>
  <p><strong>不只省 Token，更让 AI 看懂你的项目</strong></p>

  <p>
    <a href="https://pypi.org/project/tokenrazor/">
      <img src="https://img.shields.io/pypi/v/tokenrazor" alt="PyPI">
    </a>
    <a href="https://github.com/liuchunwei732-cmyk/tokenrazor/actions">
      <img src="https://img.shields.io/github/actions/workflow/status/liuchunwei732-cmyk/tokenrazor/ci.yml" alt="CI">
    </a>
    <a href="LICENSE">
      <img src="https://img.shields.io/badge/License-MIT-green.svg" alt="MIT License">
    </a>
    <a href="https://www.python.org/downloads/">
      <img src="https://img.shields.io/badge/python-3.9+-blue.svg" alt="Python 3.9+">
    </a>
    <img src="https://img.shields.io/badge/隐私-纯本地处理-blueviolet" alt="隐私优先">
    <img src="https://img.shields.io/badge/中文-深度适配-brightgreen" alt="中文适配">
  </p>

  <br>
</div>

---

**TokenRazor** 不是又一个 Token 过滤工具。它是面向 AI 编程场景的**上下文智能编排层**——主动理解项目结构、智能降噪终端输出、双向优化 Token 开销，让 AI 助手只看到对它有价值的信息。

对 DeepSeek-R1、OpenAI o1/o3、Claude Sonnet、Cursor、Copilot 等场景尤其有效。

---

## 目录

- [为什么做这个](#为什么做这个)
- [四大差异化](#四大差异化)
- [功能总览](#功能总览)
- [快速开始](#快速开始)
- [工作原理](#工作原理)
- [命令详解](#命令详解)
- [项目感知](#项目感知)
- [全栈工具链支持](#全栈工具链支持)
- [路线图](#路线图)
- [对比现有方案](#对比现有方案)
- [开发](#开发)
- [许可](#许可)

---

## 为什么做这个

用 AI 编程的开发者都经历过这个场景：

```
终端输出: 2,847 tokens  ← node_modules 的报错堆栈占了大半
                        ← 其中 90% 是重复性的内部调用
AI 回复:  1,200 tokens  ← 800 tokens 是「让我思考一下...」
                        ← 300 tokens 是「方法A不行...方法B试试...」
最终答案: 36 tokens      ← 一句话就解决了问题

花了 4,047 tokens，有效信息不到 3%。
```

市场上现有的工具各管一段：RTK 只过滤终端输出、Guardrails 只管安全合规、模型剪枝要 GPU 且可能漂移。**没有一个工具站在 AI 编程的完整链路上去思考问题。**

TokenRazor 的答案是：**把输入清洗、输出剪枝、上下文理解做成一个完整闭环。**

---

## 四大差异化

### 1. AI 原生的动态降噪——比固定规则聪明

| 方案 | 原理 | 局限 |
|------|------|------|
| RTK | 固定正则/规则 | 误杀率高，无法区分「看似无关但关键」的信息 |
| TokenRazor | 规则 + 轻量本地 AI 判断 | 学习式、自适应、越用越准 |

内置的 Scanner 不只是简单匹配关键词，还能**结合上下文判断**：「这个报错堆栈是核心问题，还是子依赖的无关异常」。

### 2. 双向 Token 优化——输入输出一起管

```
上游：终端输出过滤（类似 RTK，但更智能）
      npm ERR! → 保留核心报错 → 压缩 node_modules 堆栈
      
下游：AI 回复剪枝（CoT 脱水）
      "让我想想...再确认一下..." → 只保留推理骨架

闭环：省 Token × 2，成本直接砍半
```

### 3. 项目感知的智能折叠

TokenRazor 会自动识别你的项目类型，然后**只给 AI 看它该看的东西**：

```
识别出是 React 前端项目 →
  自动折叠 node_modules 下无关模块的报错
  只暴露 src/ 下的上下文摘要
  把 dist/、coverage/ 等产物目录排除
  
识别出是 Spring Boot 后端 →
  自动压缩 Maven/Gradle 依赖树输出
  保留核心异常堆栈
  过滤 health check 类的冗余日志
```

### 4. 中文生态深度适配

RTK 几乎没有中文支持。TokenRazor 从第一天起就是为中文开发者设计的：

- **中文日志识别**：`中文报错`、`中文提示`、`中文堆栈` 自动识别
- **中文项目脚手架**：Vue / React / uni-app / Taro 专属规则预置
- **中文命令行**：`npm run dev` vs `npm install` 区别处理
- **全中文文档**：国内用户零门槛

---

## 功能总览

| 功能 | 说明 | 状态 |
|------|------|------|
| 🧹 **CoT 剪枝** | AI 输出侧的思维链脱水，去除填充废话和死胡同 | ✅ 已完成 |
| 🔎 **终端过滤** | 输入侧过滤，基于工具链感知的智能降噪 | ✅ 已完成 |
| 📁 **项目感知** | 自动识别项目类型，生成折叠策略 | ✅ 已完成 |
| 🛠 **全栈适配** | 前端/后端/移动端/运维工具链专属规则 | ✅ 已完成 |
| 📊 **统计面板** | 实时显示省了多少 Token、多少钱、压缩率 | 🚧 开发中 |
| 🧩 **IDE 插件** | VS Code / Cursor 原生集成 | 📋 规划中 |
| 🤖 **AI 增强** | 内置轻量本地模型辅助判断 | 📋 规划中 |

---

## 快速开始

```bash
pip install tokenrazor
```

### 剪枝 AI 输出（下游）

```bash
# CoT 脱水
tokenrazor prune model_output.txt

# 管道操作
cat response.txt | tokenrazor prune

# 查看剪枝细节
tokenrazor prune response.txt --diff

# JSON 格式输出（集成用）
tokenrazor prune response.txt --json -o report.json
```

### 过滤终端输出（上游）

```bash
# 直接过滤终端输出
npm run build 2>&1 | tokenrazor filter

# 从文件读取终端输出
tokenrazor filter terminal_output.log

# 指定项目类型（自动则跳过）
tokenrazor filter build.log --project react

# 查看过滤报告
tokenrazor filter build.log --stats
```

### 项目感知

```bash
# 扫描并分析当前项目
tokenrazor scan .

# 生成项目快照（给 AI 看的摘要）
tokenrazor snapshot ./src --format markdown --output project_context.md

# 查看推荐规则
tokenrazor scan . --recommend
```

### Python SDK

```python
from tokenrazor import Pruner, TerminalFilter, ProjectContext

# === 1. CoT 剪枝 ===
pruner = Pruner()
result = pruner.prune("""
<thinking>
让我分析一下这个问题。
用户问 23 × 17 等于多少。

让我算算，23 × 10 = 230，23 × 7 = 161。
所以结果是 391。

等等，让我再确认一下。
23 × 7 = 20×7 + 3×7 = 140 + 21 = 161。没错。

好的，没问题。
</thinking>
最终答案：391
""")

print(f"压缩率: {result.stats['saved_percent']}%")
print(f"剪后输出:\n{result.pruned}")

# === 2. 终端输出过滤 ===
filter_ = TerminalFilter()
filtered = filter_.filter("""
> npm run build
Error: Module not found: 'react-router-dom'
  at webpack/compilation.js:245:10
  at resolveModule (node_modules/webpack/lib/...)
  at ...
""")
print(f"过滤后:\n{filtered}")

# === 3. 项目感知 ===
ctx = ProjectContext.detect(".")
print(f"项目类型: {ctx.project_type}")
print(f"框架: {ctx.framework}")
print(f"推荐忽略: {ctx.recommended_ignores}")
```

---

## 工作原理

```
┌─────────────────────────────────────────────────────────┐
│                    TokenRazor 架构                        │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  输入侧 (终端输出)         输出侧 (AI 回复)               │
│  ┌──────────────┐       ┌──────────────┐                │
│  │ 工具链解析器   │       │ CoT 分离器    │                │
│  │ · npm/npx    │       │ · DeepSeek   │                │
│  │ · vue/cli    │       │ · OpenAI     │                │
│  │ · docker     │       │ · Claude     │                │
│  └──────┬───────┘       └──────┬───────┘                │
│         │                      │                         │
│         ▼                      ▼                         │
│  ┌──────────────┐       ┌──────────────┐                │
│  │ 项目感知引擎  │◄─────►│ 冗余扫描器    │                │
│  │ · 前端/后端   │       │ · Filler     │                │
│  │ · 移动端     │       │ · DeadEnd    │                │
│  │ · 识别规则   │       │ · 上下文折叠  │                │
│  └──────┬───────┘       └──────┬───────┘                │
│         │                      │                         │
│         ▼                      ▼                         │
│  ┌──────────────┐       ┌──────────────┐                │
│  │ 精准过滤      │       │ 无损剪枝      │                │
│  │ · 保留关键报错│       │ · 从后往前    │                │
│  │ · 折叠无关栈 │       │ · Answer不变  │                │
│  └──────────────┘       └──────────────┘                │
│                                                          │
│         ◄────────── 双向闭环 ──────────►                 │
└─────────────────────────────────────────────────────────┘
```

### 核心流程（输出剪枝）

**1. CoT-Answer 分离** — Splitter 自动识别主流推理模型的 CoT 边界标记（`<thinking>`、`<|start_thought|>`等），将输出分为"推理块"和"答案块"。

**2. 冗余模式扫描** — Scanner 在推理块中识别三类冗余：
- **Filler**（填充废话）："让我思考一下""首先，我需要""等等，我再确认一下"
- **DeadEnd**（死胡同）："这个方法不行，换一个""仔细想想，这个思路有问题"
- **ParallelEnum**（枚举分支，开发中）—— "方法一...方法二...方法三..."

**3. 无损剪枝** — Pruner
- 只处理推理块，不动答案块
- 从后往前剪，避免下标偏移
- 严格模式自动验证答案一致性，发现不一致立刻回退

### 核心流程（输入过滤）

**1. 工具链识别** — 自动检测终端输出的命令类型（npm/webpack/docker/java 等）

**2. 项目感知匹配** — 结合项目类型，选择对应的过滤规则集

**3. 智能降噪** — 区分"关键报错"和"冗余信息"：
- 保留：错误消息、核心堆栈、退出码
- 折叠：node_modules 内部长堆栈、无意义的日志流
- 统计：压缩率、省了多少 Token

---

## 命令详解

### `prune` — 剪枝 AI 输出

```
tokenrazor prune [OPTIONS] [TEXT_FILE]

选项:
  -t, --text TEXT          直接传入文本
  -s, --strategy STRATEGY  剪枝策略 (filler / dead_end)
  --diff                    显示剪枝前后对比
  --json                    输出 JSON 格式
  --no-strict              关闭严格验证模式
  -o, --output FILE        输出到文件
```

### `filter` — 过滤终端输出

```
tokenrazor filter [OPTIONS] [LOG_FILE]

选项:
  -p, --project TEXT       指定项目类型 (auto / react / vue / springboot / flutter 等)
  -s, --stats              显示过滤统计
  --diff                   显示过滤前后对比
  --json                   输出 JSON 格式
  -o, --output FILE        输出到文件
```

### `scan` — 项目感知扫描

```
tokenrazor scan [OPTIONS] [PROJECT_DIR]

选项:
  --recommend              推荐过滤规则
  --json                   输出 JSON 格式
```

### `snapshot` — 生成项目快照

```
tokenrazor snapshot [OPTIONS] [SOURCE_DIR]

选项:
  -f, --format FORMAT      输出格式 (markdown / json)
  -o, --output FILE        输出到文件
  --max-depth N            最大目录深度
```

### `tokens` — 统计 Token

```
tokenrazor tokens [TEXT_FILE] [-t TEXT]
```

---

## 项目感知

TokenRazor 内置了项目类型检测引擎，可以自动识别常见的前端、后端和移动端项目并应用对应的过滤规则。

### 检测逻辑

| 特征文件 | 项目类型 | 框架 |
|----------|----------|------|
| `package.json` + `vite.config.*` | 前端 | Vite |
| `package.json` + `vue.config.*` | 前端 | Vue |
| `package.json` + `next.config.*` | 前端 | Next.js |
| `pom.xml` / `build.gradle` | 后端 | Spring Boot / Maven |
| `pubspec.yaml` | 移动端 | Flutter |
| `Podfile` / `*.xcworkspace` | 移动端 | iOS |
| `Dockerfile` + `k8s/` | 运维 | Kubernetes |

### 智能折叠规则

当检测到项目类型后，以下目录/文件会自动被折叠处理：

**前端**：`node_modules/`、`dist/`、`coverage/`、`.next/`、`build/`、`pnpm-lock.yaml` 等

**后端**：`target/`、`build/`、`logs/`、`.gradle/` 等

**移动端**：`Pods/`、`DerivedData/`、`.build/`、`android/app/build/` 等

---

## 全栈工具链支持

| 领域 | 工具 | 状态 |
|------|------|------|
| 前端 | npm / yarn / pnpm / vite / webpack / vue-cli / next | ✅ 已支持 |
| 后端 | maven / gradle / spring-boot / tomcat / jetty | ✅ 已支持 |
| 移动端 | flutter / xcodebuild / gradlew / pod | ✅ 已支持 |
| 运维 | docker / kubectl / helm / terraform | ✅ 已支持 |
| 数据库 | mysql / redis / elasticsearch / mongodb | 🚧 开发中 |
| AI | transformers / torch / tensorflow / onnx | 🚧 开发中 |

---

## 路线图

### 短期（1–2 个月）—— 差异化 MVP

- [x] CoT-Answer 分离器（DeepSeek / OpenAI / Claude）
- [x] Filler 短语检测（中英文）
- [x] DeadEnd 推理检测（中英文）
- [x] 严格模式自动验证
- [x] 项目类型自动检测（前端/后端/移动端）
- [x] 中文工具链适配（npm / vue / flutter / spring boot 等）
- [ ] VS Code 扩展 + 实时统计面板
- [ ] `ParallelEnum` 策略（合并枚举分支）

### 中期（3–6 个月）—— 全链路闭环

- [ ] 双向 Token 优化统计面板
- [ ] 全栈工具链全覆盖（数据库 / AI 框架）
- [ ] Project Snapshot（结构化项目快照）
- [ ] 企业版功能（团队规则共享、云端配置）

### 长期（6–12 个月）—— 生态壁垒

- [ ] 插件化规则市场，社区贡献
- [ ] 内置轻量本地 AI 增强判断
- [ ] 升级为 AI 编程上下文操作系统
- [ ] Token 经济体系（RAZOR 积分）

---

## 对比现有方案

| 维度 | RTK | Guardrails AI | LLM-KICK | TokenRazor |
|------|-----|---------------|----------|------------|
| **定位** | 终端输出过滤 | 内容安全 | 模型剪枝 | **上下文编排** |
| **覆盖链路** | 仅输入 | 仅内容 | 仅权重 | **输入+输出+上下文** |
| **中文支持** | ❌ | 有限 | ❌ | **✅ 深度适配** |
| **项目感知** | ❌ | ❌ | ❌ | **✅ 自动识别** |
| **隐私** | 本地 | 云端 | 本地 | **纯本地** |
| **答案无损** | — | ❌ | ❌ | **✅ 严格保证** |
| **硬件依赖** | ❌ | ❌ | ✅ GPU | **❌ 纯 Python** |
| **IDE 集成** | ❌ | ❌ | ❌ | **📋 规划中** |

---

## 开发

```bash
git clone https://github.com/liuchunwei732-cmyk/tokenrazor.git
cd tokenrazor
pip install -e ".[dev]"
pytest
```

项目结构：

```
tokenrazor/
├── tokenrazor/
│   ├── __init__.py          # 包入口
│   ├── cli.py               # 命令行入口
│   ├── context.py           # 项目感知引擎（新增）
│   ├── input_filter.py      # 终端输出过滤器（新增）
│   ├── toolchain.py         # 工具链规则库（新增）
│   ├── core/
│   │   ├── splitter.py      # CoT-Answer 分离器
│   │   ├── scanner.py       # 冗余模式检测器
│   │   ├── pruner.py        # 核心剪枝引擎
│   │   └── reporter.py      # 报告生成器
│   └── utils/
│       └── tokenizer.py     # Token 计数
├── tests/
│   ├── test_splitter.py
│   ├── test_pruner.py
│   ├── test_context.py      # 新增
│   ├── test_input_filter.py # 新增
│   └── fixtures/
│       └── samples.py
└── pyproject.toml
```

---

## 许可

[MIT License](LICENSE)

---

<p align="center">
  <sub>脱水不脱脑 · 精简不简智 · 中文优先 · 隐私至上</sub>
</p>
