"""
指标计算测试

第一个示例测试已写好（体验 RED 状态）。
TODO: 按以下场景补充更多测试，然后实现 metrics.py 让测试通过（GREEN）。

建议测试场景：
1. 正确计算 3 类别的 Accuracy ✅（已有示例）
2. 正确计算每类的 Precision/Recall/F1
3. 全部预测正确时 Accuracy = 1.0, F1 = 1.0
4. 加权 F1 计算正确
5. 某类别样本为 0 时处理正确

先写测试，再实现代码！
"""
import pytest


def test_accuracy_calculation(sample_df):
    """示例测试：Accuracy 应为正确预测数 / 总数

    当前会报错（因为 calculate_metrics 还未实现）。
    实现 metrics.py 后应通过。
    """
    from src.metrics import calculate_metrics

    result = calculate_metrics(sample_df)
    assert result is not None, "calculate_metrics 返回了 None，请先实现该函数"
    assert "accuracy" in result, "返回结果应包含 accuracy 字段"

    # sample_df 中有 10 条数据，7 条预测正确
    # cat: 3/4 正确, dog: 3/3 正确（1 个被误判为 cat）, bird: 1/3 正确（2 个被误判）
    # 实际正确数：请根据 conftest.py 的 sample_df 计算
    assert 0.0 <= result["accuracy"] <= 1.0, "accuracy 应在 0-1 之间"


def test_perfect_predictions(perfect_df):
    """全部预测正确时 Accuracy 应为 1.0"""
    from src.metrics import calculate_metrics

    result = calculate_metrics(perfect_df)
    assert result is not None, "calculate_metrics 返回了 None"
    assert result["accuracy"] == 1.0, "全部预测正确时 accuracy 应为 1.0"


# TODO: 在这里补充更多测试场景
