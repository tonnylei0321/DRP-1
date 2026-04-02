"""pytest fixtures"""
import pytest
import pandas as pd


@pytest.fixture
def sample_df():
    """示例预测数据"""
    return pd.DataFrame({
        "sample_id": range(1, 11),
        "true_label": ["cat", "dog", "cat", "bird", "dog", "cat", "bird", "dog", "cat", "bird"],
        "predicted_label": ["cat", "cat", "cat", "bird", "dog", "dog", "bird", "dog", "cat", "cat"],
        "confidence": [0.95, 0.51, 0.88, 0.92, 0.79, 0.45, 0.86, 0.91, 0.77, 0.38],
    })


@pytest.fixture
def perfect_df():
    """全部预测正确的数据"""
    labels = ["cat", "dog", "bird"] * 3
    return pd.DataFrame({
        "sample_id": range(1, 10),
        "true_label": labels,
        "predicted_label": labels,
        "confidence": [0.99] * 9,
    })
