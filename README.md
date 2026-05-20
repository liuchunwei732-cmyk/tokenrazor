<div align="center">
  <h1>🧹 TokenRazor</h1>
  <p><em>脱水不脱脑 — LLM CoT 逻辑剪枝工具</em></p>

  <p>
    <a href="https://pypi.org/project/tokenrazor/">
      <img src="https://img.shields.io/pypi/v/tokenrazor" alt="PyPI">
    </a>
    <a href="https://github.com/liuchunwei/tokenrazor/actions">
      <img src="https://img.shields.io/github/actions/workflow/status/liuchunwei/tokenrazor/ci.yml" alt="CI">
    </a>
    <a href="https://github.com/liuchunwei/tokenrazor/blob/main/LICENSE">
      <img src="https://img.shields.io/badge/License-MIT-green.svg" alt="MIT License">
    </a>
    <a href="https://www.python.org/downloads/">
      <img src="https://img.shields.io/badge/python-3.9+-blue.svg" alt="Python 3.9+">
    </a>
    <a href="https://github.com/liuchunwei/tokenrazor">
      <img src="https://img.shields.io/github/stars/liuchunwei/tokenrazor" alt="Stars">
    </a>
  </p>

  <br>
</div>

---

**TokenRazor** 是一个应用层的 LLM 思维链（Chain of Thought）逻辑剪枝工具。

它不碰模型权重、不依赖特定硬件。它只做一件事：**把 AI 推理模型输出的 CoT 中那些冗余、自我重复、填充废话、死胡同推理精准切掉，保留答案的完整性。**

对 DeepSeek-R1、OpenAI o1/o3、Claude Sonnet 等输出超长 CoT 的模型尤其有效。

## 为什么做这个

用推理模型的开发者都经历过这个场景：

```
原始输出: 2,847 tokens  ← 其中 800 tokens 是「让我思考一下...」
                        ← 400 tokens 是「方法A...但是...方法B...」
                        ← 300 tokens 是「再确认一下...」
最终答案: 一句话 (36 tokens)
```

**TokenRazor 的定位：**

| 维度 | 传统方案 (LLM-KICK, Awesome-LLM-Prune) | TokenRazor |
|------|------|------|
| 剪枝层级 | 神经网络权重 / KV Cache | 输出文本 / 逻辑层 |
| 依赖 | PyTorch, 特定硬件 | 纯 Python, 通杀任何 API |
| 风险 | 微调可能导致能力漂移 | 无损（Answer 严格不变） |
| 集成为 | 训练管线 | CLI / SDK / CI Pipeline |

## 快速开始

```bash
pip install tokenrazor
```

### 命令行

```bash
# 从文件读取
tokenrazor prune model_output.txt

# 管道输入
cat response.txt | tokenrazor prune

# 查看剪枝细节
tokenrazor prune response.txt --diff

# 指定策略（仅去填充话）
tokenrazor prune response.txt --strategy filler

# JSON 输出（集成用）
tokenrazor prune response.txt --json -o report.json
```

### Python SDK

```python
from tokenrazor import Pruner

pruner = Pruner()

# 原始 LLM 输出（含 CoT）
raw_output = """
<thinking>
我先分析一下这个问题。
用户问的是 23 × 17 等于多少。

让我算算，23 × 10 = 230，23 × 7 = 161。所以结果是 391。

等等，让我再确认一下。23 × 7 = 20×7 + 3×7 = 140 + 21 = 161。没错。

好的，没问题。
</thinking>
最终答案：391
"""

result = pruner.prune(raw_output)

print(f"压缩率: {result.stats['saved_percent']}%")
print(f"原始: {result.stats['original_tokens']} tokens → 剪后: {result.stats['pruned_tokens']} tokens")
print(f"移除冗余: {len(result.removed_spans)} 处")
print(f"\n剪后输出:\n{result.pruned}")
```

输出：

```
压缩率: 47.2%
原始: 142 tokens → 剪后: 75 tokens
移除冗余: 3 处
  · filler (置信度 85%)
  · filler (置信度 85%)
  · filler (置信度 85%)

剪后输出:
分析一下这个问题。用户问的是 23 × 17 等于多少。
23 × 10 = 230，23 × 7 = 161。所以结果是 391。
23 × 7 = 20×7 + 3×7 = 140 + 21 = 161。没错。

最终答案：391
```

## 工作原理

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  输入解析器   │ ──► │  冗余扫描器    │ ──► │  精准剪枝器   │
│              │     │              │     │              │
│ CoT / Answer │     │ Filler       │     │ 从后往前剪    │
│ 自动分离      │     │ DeadEnd      │     │ Answer 不变   │
└──────────────┘     └──────────────┘     └──────────────┘
```

### 三步流程

**1. CoT-Answer 分离** — Splitter
自动识别主流推理模型的 CoT 边界标记（`<thinking>`、`<|start_thought|>` 等），将输出分为"推理块"和"答案块"。

**2. 冗余模式扫描** — Scanner
在推理块中识别三类冗余：
- **Filler**（填充废话）："让我思考一下""首先，我需要""等等，我再确认一下"
- **DeadEnd**（死胡同）："这个方法不行，换一个""仔细想想，这个思路有问题"
- *更多策略开发中*

**3. 无损剪枝** — Pruner
- 只处理推理块，不动答案块
- 从后往前剪，避免下标偏移
- 严格模式自动验证答案一致性，发现不一致立刻回退

## 剪枝策略

| 策略 | 默认 | 说明 |
|------|------|------|
| `filler` | ✅ | 移除填充式过渡短语 |
| `dead_end` | ✅ | 移除被模型主动放弃的推理路径 |

```bash
# 仅使用 filler 策略
tokenrazor prune output.txt --strategy filler

# 关闭 dead_end，仅保留 filler
tokenrazor prune output.txt --strategy filler --strategy filler
```

## 支持的模型

| 模型 | CoT 格式 | 状态 |
|------|----------|------|
| DeepSeek-R1 | `<thinking>...</thinking>` | ✅ 已验证 |
| OpenAI o1 / o3 | `<|start_thought|>...<|end_thought|>` | ✅ 已验证 |
| Claude Sonnet 3.5+ | `<thinking>...</thinking>` | ✅ 基本支持 |
| 通用格式 | 末段为 Answer 的文本 | ✅ 启发式支持 |

## 在 CI/CD 中使用

```yaml
# .github/workflows/prune-check.yml
name: TokenRazor check
on: [pull_request]
jobs:
  prune:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: pip install tokenrazor
      - run: |
          for f in outputs/*.txt; do
            echo "=== $f ==="
            tokenrazor prune "$f" --json
          done
```

## 与现有方案的对比

| 项目 | 层级 | 硬件依赖 | 答案无损 | 定位 |
|------|------|----------|----------|------|
| TokenRazor | 应用层/文本层 | ❌ | ✅ | CoT 脱水 |
| Guardrails AI | 内容安全层 | ❌ | ❌ | 安全合规 |
| NeMo Guardrails | 对话控制层 | ❌ | ❌ | 对话护栏 |
| LLM-KICK | 模型权重层 | ✅ (GPU) | ❌ | 模型剪枝 |
| Awesome-LLM-Prune | 资源收集 | — | — | 论文列表 |

## 路线图

- [x] CoT-Answer 分离器（支持 DeepSeek / OpenAI / Claude）
- [x] Filler 短语检测（中英文）
- [x] DeadEnd 推理检测（中英文）
- [x] 严格模式自动验证
- [x] CLI 接口（文件/管道/JSON）
- [ ] VS Code 扩展
- [ ] Parallel Universe 剪枝（合并枚举分支）
- [ ] 质量评估指标（剪枝后正确率验证）
- [ ] Pre-commit hook

## 项目结构

```
tokenrazor/
├── tokenrazor/
│   ├── cli.py              # 命令行入口
│   ├── core/
│   │   ├── splitter.py     # CoT-Answer 分离器
│   │   ├── scanner.py      # 冗余模式检测器
│   │   ├── pruner.py       # 核心剪枝引擎
│   │   └── reporter.py     # 报告生成器
│   └── utils/
│       └── tokenizer.py    # Token 计数（tiktoken）
├── tests/
│   ├── test_splitter.py
│   ├── test_pruner.py
│   └── fixtures/
│       └── samples.py      # 真实 LLM 输出样本
└── pyproject.toml
```

## 开发

```bash
git clone https://github.com/liuchunwei/tokenrazor.git
cd tokenrazor
pip install -e ".[dev]"
pytest
```

## 许可

[MIT License](LICENSE)

---

<p align="center">
  <sub>脱水不脱脑 · 精简不简智</sub>
</p>
