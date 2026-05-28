"""Token 费用计算器 — 把压缩率换算成钱。

产品经理不看压缩比，他们看省了多少钱。
支持主流模型 API 定价，输出直观费用对比。

定价来源 (2026-05 最新):
- GPT-4o:       $2.50 / 1M input tokens
- GPT-4o-mini:  $0.15 / 1M input tokens
- Claude 3.5 Sonnet: $3.00 / 1M input tokens
- DeepSeek-R1:  $0.55 / 1M input tokens  (推理)
- DeepSeek-V3:  $0.27 / 1M input tokens
- Kimi K2.5:    $0.40 / 1M input tokens
"""

from typing import Optional

# 模型定价表（美元 / 1M tokens）
# 使用双向平均估算（input + output 的混合）
_MODEL_PRICING: dict = {
    # OpenAI
    "gpt-4o":           2.50,
    "gpt-4o-128k":      2.50,
    "gpt-4o-mini":      0.15,
    "gpt-4-turbo":      10.00,
    "gpt-3.5-turbo":    0.50,
    "o1":               15.00,
    "o1-mini":          1.10,
    "o3-mini":          1.10,
    # Anthropic
    "claude-sonnet-4":  3.00,
    "claude-3.5-sonnet": 3.00,
    "claude-3-opus":    15.00,
    "claude-3-haiku":   0.25,
    # DeepSeek
    "deepseek-r1":      0.55,
    "deepseek-v3":      0.27,
    "deepseek-coder":   0.14,
    # Kimi / Moonshot
    "kimi-k2.5":        0.40,
    "kimi-k2":          0.30,
    # Google
    "gemini-2.0-flash": 0.10,
    "gemini-2.0-pro":   2.00,
    # 国产
    "qwen-max":         0.80,
    "qwen-plus":        0.20,
    "ernie-4.0":        1.20,
    "glm-4":            0.50,
    # 通用兜底
    "default":          1.00,  # 保守估计 $1 / 1M tokens
}

# 推荐模型别名映射
_MODEL_ALIASES: dict = {
    "gpt4": "gpt-4o",
    "gpt4o": "gpt-4o",
    "gpt4turbo": "gpt-4-turbo",
    "gpt35": "gpt-3.5-turbo",
    "claude": "claude-3.5-sonnet",
    "claude35": "claude-3.5-sonnet",
    "claude4": "claude-sonnet-4",
    "ds": "deepseek-v3",
    "ds-r1": "deepseek-r1",
    "deepseek": "deepseek-v3",
    "kimi": "kimi-k2.5",
    "gemini": "gemini-2.0-flash",
    "qwen": "qwen-max",
    "glm": "glm-4",
    "ernie": "ernie-4.0",
}


def get_model_price(model: str) -> float:
    """获取模型每百万 token 的价格（美元）。"""
    resolved = _MODEL_ALIASES.get(model.lower(), model.lower())
    return _MODEL_PRICING.get(resolved, _MODEL_PRICING["default"])


def calculate_cost(
    tokens: int,
    model: Optional[str] = None,
    price_per_1m: Optional[float] = None,
) -> float:
    """计算 token 对应的费用（美元）。

    Args:
        tokens: Token 数量
        model: 模型名（与 price_per_1m 二选一）
        price_per_1m: 每百万 token 的价格（与 model 二选一）

    Returns:
        费用（美元）
    """
    if price_per_1m is not None:
        rate = price_per_1m
    else:
        rate = get_model_price(model or "default")
    return (tokens / 1_000_000) * rate


def cost_report(
    original_tokens: int,
    pruned_tokens: int,
    model: Optional[str] = None,
    price_per_1m: Optional[float] = None,
    currency: str = "USD",
) -> dict:
    """生成费用对比报告。

    Returns:
        {
            "original_cost": 0.0125,
            "pruned_cost": 0.0060,
            "saved_cost": 0.0065,
            "saved_percent": 52.0,
            "model": "gpt-4o",
            "price_per_1m": 2.5,
            "currency": "USD",
        }
    """
    rate = price_per_1m if price_per_1m is not None else get_model_price(model or "default")
    model_name = model or "default"

    orig_cost = (original_tokens / 1_000_000) * rate
    pruned_cost = (pruned_tokens / 1_000_000) * rate
    saved_cost = orig_cost - pruned_cost
    saved_pct = round(100 * (1 - pruned_cost / orig_cost), 1) if orig_cost else 0

    return {
        "original_cost": round(orig_cost, 6),
        "pruned_cost": round(pruned_cost, 6),
        "saved_cost": round(saved_cost, 6),
        "saved_percent": saved_pct,
        "model": model_name,
        "price_per_1m": rate,
        "currency": currency,
    }


def format_cost(amount: float, currency: str = "USD") -> str:
    """格式化费用显示。"""
    if amount < 0.01:
        return f"${amount:.4f}"
    elif amount < 1:
        return f"${amount:.2f}"
    else:
        return f"${amount:.2f}"


def supported_models() -> list:
    """返回支持的模型列表。"""
    return sorted(set(_MODEL_PRICING.keys()) - {"default"})
