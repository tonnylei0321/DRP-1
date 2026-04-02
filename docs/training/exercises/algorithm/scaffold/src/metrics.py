"""
指标计算模块

TODO: 实现以下函数：
- load_predictions(csv_path): 读取 CSV → DataFrame
- calculate_metrics(df): 计算所有评估指标
  返回字典：
  {
    "accuracy": float,
    "per_class": {
      "cat": {"precision": float, "recall": float, "f1": float, "support": int},
      ...
    },
    "weighted_f1": float,
    "total_samples": int,
    "num_classes": int
  }

提示：
- 使用 pandas 读取 CSV
- 可以使用 sklearn.metrics 辅助计算
- 也可以手动实现（更好理解原理）
"""
import pandas as pd


def load_predictions(csv_path: str) -> pd.DataFrame:
    """读取预测结果 CSV"""
    # TODO: 实现
    pass


def calculate_metrics(df: pd.DataFrame) -> dict:
    """计算评估指标"""
    # TODO: 实现
    pass
