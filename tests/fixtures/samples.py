"""测试样本：真实的 LLM CoT 输出。"""

# 样本1: DeepSeek-R1 风格 CoT（带 <thinking> 标签）
DEEPSEEK_R1_SAMPLE = """<thinking>
我需要判断 "Hello, World!" 这个字符串中是否包含大写字母。

首先，让我看看字符串中的字符：
"H" - 大写
"e" - 小写
"l" - 小写
"l" - 小写
"o" - 小写
"," - 标点
" " - 空格
"W" - 大写
"o" - 小写
"r" - 小写
"l" - 小写
"d" - 小写
"!" - 标点

让我再确认一下。这个字符串中有两个大写字母：H 和 W。
让我再思考一下，是否还有其他大写字母。
H 是大写，W 是大写，其他都是小写或符号。对的。
因此，这个字符串包含大写字母。
</thinking>
最终答案：是的，"Hello, World!" 包含大写字母 H 和 W。"""

# 样本2: 带填充短语和死胡同推理的 CoT
FILLER_AND_DEADEND_SAMPLE = """让我思考一下这个问题。用户问的是 23 乘以 17 等于多少。

首先，我需要计算 23 × 17。

让我想想，23 × 10 = 230，23 × 7 = 161。所以 230 + 161 = 391。

等等，让我重新确认一下。23 × 10 = 230 没问题。23 × 7 = 20×7 + 3×7 = 140 + 21 = 161。230 + 161 = 391。

让我再检查一遍。也许我应该用另一种方法。
23 × 17 = (20+3) × 17 = 20×17 + 3×17 = 340 + 51 = 391。对的。

实际上，让我再想想看有没有其他方法验证。21 × 17 = 357，加上 2 × 17 = 34，357 + 34 = 391。确认了。

好的，这个计算没有问题。

答案：391"""

# 样本3: 死胡同推理模式
DEAD_END_SAMPLE = """分析这个问题，需要考虑所有可能的方法。

方法一：直接计算法。用公式直接代入计算。这应该是正确的，但让我们先看看其他方法。

方法二：分步求解法。先分解问题，再逐步求解。这个方法看起来也行得通。

等等，方法一其实有点问题，因为它假设了某些条件成立，但这些条件在这个场景下不满足。所以方法一不可行。

方法二才是正确方向。让我认真把方法二做一遍：
第一步：提取关键数据。第二步：应用公式。第三步：验证结果。

但仔细想想，方法二也有局限性，在边界情况下会出问题。算了，这个方法也放弃。

让我重新想想。实际上有一个更简单的方法三，不需要用到复杂的公式。
方法三：直接使用定义推导。这个方法既简单又正确。

最终答案选 B。"""

# 样本4: OpenAI o1 风格
OPENAI_O1_SAMPLE = """<|start_thought|>
The user is asking about the capital of France.

This is a straightforward geography question. France is a country in Western Europe, and its capital is Paris.

Let me verify this by considering other major French cities: Lyon, Marseille, Bordeaux, Toulouse, Nice. None of these are the capital.

Actually, let me also consider if there's any recent change. No, Paris has been the capital of France for centuries.

I'm confident about this answer.
<|end_thought|>
The capital of France is Paris."""

# 样本5: 纯文本（不含 CoT）
PLAIN_TEXT_SAMPLE = """Python 是一种广泛使用的高级编程语言。

它由 Guido van Rossum 于 1989 年发明，1991 年首次发布。

Python 的设计哲学强调代码的可读性。"""

# 样本6: 平行世界枚举
PARALLEL_ENUMERATION_SAMPLE = """我需要找出 1 到 100 之间所有能被 3 整除但不能被 5 整除的数。

方法一: 遍历每个数，检查条件。这是最直接的方法。

方法二: 也可以用集合操作。先找出所有 3 的倍数，再排除掉 5 的倍数。

方法三: 用列表推导式，一行搞定。

方法一最直观，方法三最简洁。我选择方法三作为最终方案。

答案：[3, 6, 9, 12, 18, 21, 24, 27, 33, 36, 39, 42, 48, 51, 54, 57, 63, 66, 69, 72, 78, 81, 84, 87, 93, 96, 99]"""
