"""TokenRazor 入门示例。"""

from tokenrazor.core import Pruner, Report
from tokenrazor.core.splitter import split_cot_answer

# 模拟一段 DeepSeek-R1 的输出
deepseek_output = """<thinking>
我来分析这个排序问题。

首先，我需要理解题目要求：对 [3, 1, 4, 1, 5, 9, 2, 6] 进行升序排序。

让我想想用什么算法。可以用快速排序，这是最常用的。

让我再想想。快速排序的时间复杂度是 O(n log n)，空间复杂度 O(log n)。这是一个好的选择。

不过让我也考虑一下归并排序。归并排序也是 O(n log n)，但空间复杂度是 O(n)。对于这个规模，区别不大。

好的，就用快速排序。我写出代码实现：

def quick_sort(arr):
    if len(arr) <= 1:
        return arr
    pivot = arr[len(arr) // 2]
    left = [x for x in arr if x < pivot]
    middle = [x for x in arr if x == pivot]
    right = [x for x in arr if x > pivot]
    return quick_sort(left) + middle + quick_sort(right)

让我验证一下这个实现是否正确。
pivot = 5, left = [3,1,4,1,2], middle = [5], right = [9,6]
递归... 最终结果应该是 [1,1,2,3,4,5,6,9]

没错，这个实现是正确的。
</thinking>
排序结果：[1, 1, 2, 3, 4, 5, 6, 9]"""

print("=" * 60)
print("TokenRazor 示例：DeepSeek-R1 输出剪枝")
print("=" * 60)

# 执行剪枝
pruner = Pruner()
result = pruner.prune(deepseek_output)

# 打印报告
print(Report.text(result, show_diff=False))

# 详细对比
print("\n" + "=" * 60)
print("剪枝前 (token 数):", result.stats["original_tokens"])
print("剪枝后 (token 数):", result.stats["pruned_tokens"])
print("节省:", result.stats["saved_tokens"], "tokens (" + str(result.stats["saved_percent"]) + "%)")
print("=" * 60)

# 验证答案不变
_, original_answer = split_cot_answer(deepseek_output)
_, pruned_answer = split_cot_answer(result.pruned)
match = original_answer.strip() == pruned_answer.strip()
print(f"\n答案一致性验证: {'✅' if match else '❌'}")
if not match:
    print(f"原始答案: {original_answer[:100]}")
    print(f"剪后答案: {pruned_answer[:100]}")
