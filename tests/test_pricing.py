"""费用计算器测试。"""

from tokenrazor.core.pricing import (
    calculate_cost,
    cost_report,
    format_cost,
    get_model_price,
    supported_models,
)


class TestPricing:

    def test_get_model_price_gpt4o(self):
        assert get_model_price("gpt-4o") == 2.50

    def test_get_model_price_claude(self):
        assert get_model_price("claude-3.5-sonnet") == 3.00

    def test_get_model_price_deepseek(self):
        assert get_model_price("deepseek-r1") == 0.55

    def test_get_model_price_unknown_default(self):
        """未知模型应返回默认价格。"""
        assert get_model_price("unknown-model") == 1.00

    def test_get_model_price_alias_gpt4(self):
        """gpt4 应映射到 gpt-4o。"""
        assert get_model_price("gpt4") == 2.50

    def test_get_model_price_alias_claude(self):
        """claude 应映射到 claude-3.5-sonnet。"""
        assert get_model_price("claude") == 3.00

    def test_calculate_cost_basic(self):
        """基本费用计算。"""
        cost = calculate_cost(1000, price_per_1m=2.50)
        assert cost == 0.0025  # 1000 / 1M * 2.50

    def test_calculate_cost_by_model(self):
        """通过模型名计算。"""
        cost = calculate_cost(1000000, model="gpt-4o")
        assert cost == 2.50

    def test_calculate_cost_zero(self):
        assert calculate_cost(0, price_per_1m=2.50) == 0.0

    def test_cost_report_structure(self):
        """费用报告应包含完整字段。"""
        report = cost_report(100000, 50000, model="gpt-4o")
        assert "original_cost" in report
        assert "pruned_cost" in report
        assert "saved_cost" in report
        assert "saved_percent" in report
        assert "model" in report
        assert "currency" in report

    def test_cost_report_savings(self):
        """费用节省应为正值。"""
        report = cost_report(100000, 50000, model="gpt-4o")
        assert report["saved_cost"] > 0
        assert report["saved_percent"] == 50.0

    def test_format_cost_small(self):
        """小金额应显示4位小数。"""
        assert format_cost(0.0025) == "$0.0025"

    def test_format_cost_medium(self):
        """中金额应显示2位小数。"""
        assert format_cost(1.50) == "$1.50"

    def test_supported_models_list(self):
        """支持的模型列表应有常见模型。"""
        models = supported_models()
        assert "gpt-4o" in models
        assert "claude-3.5-sonnet" in models
        assert "deepseek-r1" in models
