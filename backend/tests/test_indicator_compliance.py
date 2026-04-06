"""指标达标判断正确性测试。

Property 7: 指标达标判断正确性
"""
import pytest
from hypothesis import given, strategies as st

from drp.indicators.calculator import _check_compliance


class TestIndicatorCompliance:
    """Property 7: 指标达标判断正确性"""
    # Feature: e2e-test-data-pipeline, Property 7: 指标达标判断正确性

    def test_none_value_is_non_compliant(self):
        """value 为 None 时不达标"""
        indicator = {"target_value": 1.0, "threshold": 0.95}
        assert _check_compliance(indicator, None) is False

    def test_ratio_indicator_above_threshold_is_compliant(self):
        """比率类指标 value >= threshold 达标"""
        indicator = {"target_value": 1.0, "threshold": 0.95}
        assert _check_compliance(indicator, 0.96) is True
        assert _check_compliance(indicator, 0.95) is True

    def test_ratio_indicator_below_threshold_is_non_compliant(self):
        """比率类指标 value < threshold 不达标"""
        indicator = {"target_value": 1.0, "threshold": 0.95}
        assert _check_compliance(indicator, 0.94) is False

    def test_count_indicator_below_threshold_is_compliant(self):
        """计数类指标（target_value=0）value <= threshold 达标"""
        indicator = {"target_value": 0, "threshold": 5}
        assert _check_compliance(indicator, 3) is True
        assert _check_compliance(indicator, 5) is True

    def test_count_indicator_above_threshold_is_non_compliant(self):
        """计数类指标 value > threshold 不达标"""
        indicator = {"target_value": 0, "threshold": 5}
        assert _check_compliance(indicator, 6) is False

    def test_no_target_always_compliant(self):
        """无目标要求时默认达标"""
        indicator = {"target_value": None, "threshold": None}
        assert _check_compliance(indicator, 42.0) is True

    @given(
        value=st.floats(min_value=0, max_value=1, allow_nan=False),
        threshold=st.floats(min_value=0, max_value=1, allow_nan=False),
    )
    def test_ratio_compliance_property(self, value, threshold):
        """Property: 比率类指标 value >= threshold ↔ 达标"""
        indicator = {"target_value": 1.0, "threshold": threshold}
        result = _check_compliance(indicator, value)
        assert result == (value >= threshold)
