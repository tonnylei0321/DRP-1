"""
可视化模块

TODO: 实现以下函数：
- plot_confusion_matrix(df, output_path): 生成混淆矩阵热力图
- plot_f1_scores(metrics, output_path): 生成 F1-Score 柱状图

提示：
- 使用 matplotlib
- 图表标题、轴标签使用中文
- 配色建议：使用 matplotlib 内置 colormap
- 图片分辨率：dpi=150
"""
import matplotlib
matplotlib.use('Agg')  # 无 GUI 模式
import matplotlib.pyplot as plt


def plot_confusion_matrix(df, output_path: str):
    """生成混淆矩阵热力图"""
    # TODO: 实现
    pass


def plot_f1_scores(metrics: dict, output_path: str):
    """生成 F1-Score 柱状图"""
    # TODO: 实现
    pass
