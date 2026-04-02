"""
模型评估主入口

CLI 参数解析已完成。待接入各模块。

用法（在 scaffold/ 目录下执行）：
    python src/evaluate.py --input data/sample_predictions.csv --output report/
"""
import argparse
import sys
from pathlib import Path


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="模型评估与可视化流水线")
    parser.add_argument(
        "--input",
        nargs="+",
        required=True,
        help="预测结果 CSV 文件路径（支持多个文件用于模型对比）",
    )
    parser.add_argument(
        "--output",
        default="report/",
        help="输出报告目录（默认 report/）",
    )
    return parser.parse_args()


def main():
    """主流程"""
    args = parse_args()

    # 验证输入文件存在
    for input_file in args.input:
        if not Path(input_file).exists():
            print(f"错误：文件不存在 - {input_file}")
            sys.exit(1)

    # 创建输出目录
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"输入文件：{args.input}")
    print(f"输出目录：{args.output}")

    # TODO: 接入各模块
    # 1. 读取 CSV 数据
    # 2. 调用 metrics.py 计算指标
    # 3. 调用 visualizer.py 生成图表
    # 4. 调用 reporter.py 生成报告

    print("评估流水线待实现")


if __name__ == "__main__":
    main()
