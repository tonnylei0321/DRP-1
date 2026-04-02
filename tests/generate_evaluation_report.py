#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成图任务模型评测报告
"""

import json
from datetime import datetime
from collections import defaultdict


def generate_report(results_file: str, output_file: str):
    """生成Markdown格式的评测报告"""
    
    with open(results_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    timestamp = data.get('timestamp', datetime.now().isoformat())
    model_stats = data.get('model_stats', {})
    task_stats = data.get('task_stats', {})
    results = data.get('results', [])
    
    models = list(model_stats.keys())
    
    report = []
    report.append("# 图任务模型评测报告\n")
    report.append(f"**生成时间**: {timestamp}\n")
    report.append(f"**评测样本数**: {len(results)}\n")
    report.append(f"**评测模型**: {', '.join(models)}\n")
    
    # 总体统计
    report.append("\n## 1. 总体评测结果\n")
    report.append("| 模型 | 正确数 | 总数 | 准确率 | 平均延迟 |")
    report.append("|------|--------|------|--------|----------|")
    
    for model in models:
        stats = model_stats[model]
        correct = stats['correct']
        total = stats['total']
        accuracy = correct / total * 100 if total > 0 else 0
        avg_latency = stats['total_latency'] / total if total > 0 else 0
        report.append(f"| {model} | {correct} | {total} | {accuracy:.1f}% | {avg_latency:.2f}s |")
    
    # 各任务类型统计
    report.append("\n## 2. 各任务类型准确率\n")
    report.append("| 任务类型 | " + " | ".join([f"{m} 准确率" for m in models]) + " |")
    report.append("|----------|" + "----------|" * len(models))
    
    for task_type in sorted(task_stats.keys()):
        row = [task_type]
        for model in models:
            stats = task_stats[task_type][model]
            correct = stats['correct']
            total = stats['total']
            accuracy = correct / total * 100 if total > 0 else 0
            row.append(f"{correct}/{total} ({accuracy:.0f}%)")
        report.append("| " + " | ".join(row) + " |")
    
    # 详细结果
    report.append("\n## 3. 详细评测结果\n")
    
    # 按任务类型分组
    results_by_type = defaultdict(list)
    for r in results:
        results_by_type[r['task_type']].append(r)
    
    for task_type in sorted(results_by_type.keys()):
        report.append(f"\n### 3.{list(sorted(results_by_type.keys())).index(task_type)+1} {task_type}\n")
        
        for i, r in enumerate(results_by_type[task_type], 1):
            report.append(f"#### 样本 {i}\n")
            report.append(f"**预期输出**: `{r['expected'][:200]}{'...' if len(r['expected']) > 200 else ''}`\n")
            
            for model in models:
                response_key = f"{model}_response"
                latency_key = f"{model}_latency"
                correct_key = f"{model}_correct"
                match_key = f"{model}_match_detail"
                
                if response_key in r:
                    status = "✅" if r.get(correct_key, False) else "❌"
                    match_detail = r.get(match_key, "")
                    latency = r.get(latency_key, 0)
                    response = r.get(response_key, "")
                    
                    report.append(f"**{model}** {status} ({match_detail}, {latency:.1f}s)")
                    report.append(f"```")
                    report.append(response[:500] + ("..." if len(response) > 500 else ""))
                    report.append(f"```\n")
    
    # 结论
    report.append("\n## 4. 评测结论\n")
    
    # 找出表现最好的模型
    best_model = max(models, key=lambda m: model_stats[m]['correct'] / model_stats[m]['total'] if model_stats[m]['total'] > 0 else 0)
    best_accuracy = model_stats[best_model]['correct'] / model_stats[best_model]['total'] * 100
    
    fastest_model = min(models, key=lambda m: model_stats[m]['total_latency'] / model_stats[m]['total'] if model_stats[m]['total'] > 0 else float('inf'))
    fastest_latency = model_stats[fastest_model]['total_latency'] / model_stats[fastest_model]['total']
    
    report.append(f"- **最高准确率**: {best_model} ({best_accuracy:.1f}%)")
    report.append(f"- **最快响应**: {fastest_model} (平均 {fastest_latency:.2f}s)")
    
    # 各模型优势任务
    report.append("\n### 各模型优势任务类型\n")
    for model in models:
        best_tasks = []
        for task_type, stats in task_stats.items():
            if stats[model]['total'] > 0:
                acc = stats[model]['correct'] / stats[model]['total']
                if acc >= 0.8:  # 80%以上准确率
                    best_tasks.append(f"{task_type}({acc*100:.0f}%)")
        if best_tasks:
            report.append(f"- **{model}**: {', '.join(best_tasks)}")
    
    # 写入文件
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(report))
    
    print(f"报告已生成: {output_file}")
    return '\n'.join(report)


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='生成评测报告')
    parser.add_argument('--input', default='tests/evaluation_results_full.json',
                        help='评测结果JSON文件')
    parser.add_argument('--output', default='tests/evaluation_report.md',
                        help='输出报告文件')
    
    args = parser.parse_args()
    generate_report(args.input, args.output)


if __name__ == '__main__':
    main()
