#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图任务模型评测脚本
评测 graph_rl 和 graph_sft 两个模型
"""

import csv
import json
import time
import requests
from datetime import datetime
from typing import Dict, List, Tuple
import re

# API配置
API_URL = "https://bip-daily.yonyoucloud.com/iuap-aip-gateway/yonchat/v1/chat/completions"
MODELS = ["graph_rl", "graph_sft"]

# 请求超时时间（秒）
REQUEST_TIMEOUT = 180


def call_model_api(model: str, prompt: str, max_tokens: int = 16384) -> Tuple[str, float]:
    """
    调用模型API
    """
    headers = {"Content-Type": "application/json"}
    
    payload = {
        "messages": [{"content": prompt, "role": "user"}],
        "model": model,
        "stream": False,
        "max_tokens": max_tokens
    }
    
    start_time = time.time()
    
    try:
        response = requests.post(API_URL, headers=headers, json=payload, timeout=REQUEST_TIMEOUT)
        latency = time.time() - start_time
        
        if response.status_code == 200:
            result = response.json()
            if "choices" in result and len(result["choices"]) > 0:
                content = result["choices"][0].get("message", {}).get("content", "")
                return content, latency
            else:
                return f"[ERROR] 响应格式异常: {result}", latency
        else:
            return f"[ERROR] HTTP {response.status_code}: {response.text}", latency
            
    except requests.exceptions.Timeout:
        return "[ERROR] 请求超时", time.time() - start_time
    except Exception as e:
        return f"[ERROR] 请求异常: {str(e)}", time.time() - start_time


def extract_answer_from_response(response: str, model: str) -> Tuple[str, str]:
    """
    从模型响应中提取答案
    
    Args:
        response: 原始响应
        model: 模型名称
        
    Returns:
        (thinking_part, answer_part)
    """
    thinking = ""
    answer = response
    
    # RL模型：提取</think>后的内容
    if model == "graph_rl" and '</think>' in response:
        parts = response.split('</think>', 1)
        thinking = parts[0]
        answer = parts[1].strip() if len(parts) > 1 else ""
    
    return thinking, answer


def extract_answer_content(text: str) -> str:
    """
    从文本中提取<<<...>>>格式的答案内容
    """
    pattern = r'<<<(.+?)>>>'
    matches = re.findall(pattern, text, re.DOTALL)
    
    if matches:
        return matches[-1].strip()
    
    return text.strip()


def normalize_for_comparison(s: str) -> str:
    """标准化字符串用于比较"""
    s = re.sub(r'\s+', '', s)
    s = s.replace('"', "'")
    return s


def compare_answers(expected: str, actual: str, task_type: str) -> Tuple[bool, str]:
    """
    比较预期答案和实际答案
    
    Returns:
        (is_match, comparison_detail)
    """
    # 提取答案内容
    exp_content = extract_answer_content(expected)
    act_content = extract_answer_content(actual)
    
    # 标准化
    exp_norm = normalize_for_comparison(exp_content)
    act_norm = normalize_for_comparison(act_content)
    
    # 1. 精确匹配
    if exp_norm == act_norm:
        return True, "精确匹配"
    
    # 2. 空集匹配: {} == set()
    empty_patterns = ["{}", "set()", "frozenset()"]
    if exp_norm in empty_patterns and act_norm in empty_patterns:
        return True, "空集匹配"
    
    # 3. 布尔值匹配
    true_patterns = ["{True}", "{true}", "True", "true"]
    false_patterns = ["{False}", "{false}", "False", "false"]
    if exp_norm in true_patterns and act_norm in true_patterns:
        return True, "布尔匹配"
    if exp_norm in false_patterns and act_norm in false_patterns:
        return True, "布尔匹配"
    
    # 4. 数值匹配 (MST等任务)
    # 预期: {'mst_edge_count': 8} 实际: {8}
    exp_numbers = set(re.findall(r'\d+', exp_norm))
    act_numbers = set(re.findall(r'\d+', act_norm))
    if task_type in ['MST', 'BipartiteMatching'] and exp_numbers and act_numbers:
        if exp_numbers & act_numbers:  # 有交集
            return True, "数值匹配"
    
    # 5. 集合内容匹配（忽略顺序）
    try:
        exp_items = set(re.findall(r"'([^']+)'", exp_content))
        act_items = set(re.findall(r"'([^']+)'", act_content))
        
        if exp_items and act_items:
            if exp_items == act_items:
                return True, "集合匹配"
            
            # 部分匹配
            intersection = exp_items & act_items
            if intersection:
                ratio = len(intersection) / max(len(exp_items), len(act_items))
                if ratio >= 0.5:
                    return True, f"部分匹配({ratio:.0%})"
                
                # PageRank: 只要包含目标节点就算对
                if task_type == 'page_rank_v2' and intersection:
                    return True, f"包含目标节点"
    except:
        pass
    
    # 6. JSON内容匹配 (description, summary等)
    try:
        # 尝试解析JSON
        exp_json = json.loads(exp_content.replace("'", '"'))
        act_json = json.loads(act_content.replace("'", '"'))
        
        # 检查关键字段
        if isinstance(exp_json, dict) and isinstance(act_json, dict):
            # summary任务：检查node_count, edge_count
            if task_type == 'summary':
                if (exp_json.get('node_count') == act_json.get('node_count') and
                    exp_json.get('edge_count') == act_json.get('edge_count')):
                    return True, "统计匹配"
            
            # description任务：检查entity_name
            if task_type == 'description':
                if exp_json.get('entity_name') == act_json.get('entity_name'):
                    return True, "实体匹配"
                # 或者name字段匹配
                if exp_json.get('entity_name') == act_json.get('name'):
                    return True, "实体匹配"
    except:
        pass
    
    # 7. description任务特殊处理：name匹配
    if task_type == 'description':
        # 从预期中提取entity_name
        name_match = re.search(r'"entity_name":\s*"([^"]+)"', exp_content)
        if name_match:
            expected_name = name_match.group(1)
            if expected_name in act_content:
                return True, "名称匹配"

    # 8. relation_path任务：frozenset内容匹配
    if task_type == 'relation_path':
        # 提取三元组内容，忽略frozenset的括号类型差异
        # 预期: frozenset([('A', 'B', 'C')]) 或 frozenset({('A', 'B', 'C')})
        exp_tuples = re.findall(r"\('([^']+)',\s*'([^']+)',\s*'([^']+)'\)", exp_content)
        act_tuples = re.findall(r"\('([^']+)',\s*'([^']+)',\s*'([^']+)'\)", act_content)
        # 也匹配双引号版本
        if not act_tuples:
            act_tuples = re.findall(r'\("([^"]+)",\s*"([^"]+)",\s*"([^"]+)"\)', act_content)

        if exp_tuples and act_tuples:
            exp_set = set(exp_tuples)
            act_set = set(act_tuples)
            if exp_set == act_set:
                return True, "路径匹配"
            if exp_set & act_set:
                return True, "部分路径匹配"

    return False, "不匹配"


def run_evaluation(testset_file: str, output_file: str, max_samples: int = None):
    """运行评测"""
    with open(testset_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        test_cases = list(reader)
    
    if max_samples:
        test_cases = test_cases[:max_samples]
    
    print(f"加载了 {len(test_cases)} 条测试用例")
    print(f"评测模型: {MODELS}")
    print("=" * 60)
    
    results = []
    model_stats = {model: {"correct": 0, "total": 0, "total_latency": 0} for model in MODELS}
    task_stats = {}
    
    for i, case in enumerate(test_cases, 1):
        task_type = case['task_type']
        instruction = case['instruction']
        expected_output = case['output']
        
        print(f"\n[{i}/{len(test_cases)}] 任务类型: {task_type}")
        
        if task_type not in task_stats:
            task_stats[task_type] = {model: {"correct": 0, "total": 0} for model in MODELS}
        
        case_result = {
            "id": i,
            "task_type": task_type,
            "expected": expected_output
        }
        
        for model in MODELS:
            print(f"  调用 {model}...", end=" ", flush=True)
            
            response, latency = call_model_api(model, instruction)
            
            # 提取思考和答案部分
            thinking, answer = extract_answer_from_response(response, model)
            
            # 比较答案
            is_correct, match_detail = compare_answers(expected_output, answer, task_type)
            
            # 保存结果
            case_result[f"{model}_response"] = response
            case_result[f"{model}_thinking"] = thinking
            case_result[f"{model}_answer"] = answer
            case_result[f"{model}_latency"] = round(latency, 2)
            case_result[f"{model}_correct"] = is_correct
            case_result[f"{model}_match_detail"] = match_detail
            
            # 更新统计
            model_stats[model]["total"] += 1
            model_stats[model]["total_latency"] += latency
            if is_correct:
                model_stats[model]["correct"] += 1
            
            task_stats[task_type][model]["total"] += 1
            if is_correct:
                task_stats[task_type][model]["correct"] += 1
            
            status = "✓" if is_correct else "✗"
            print(f"{status} ({latency:.1f}s) {match_detail}")
        
        results.append(case_result)
        
        # 每5条保存一次
        if i % 5 == 0:
            save_results(results, model_stats, task_stats, output_file)
    
    save_results(results, model_stats, task_stats, output_file)
    print_summary(model_stats, task_stats)


def save_results(results: List[Dict], model_stats: Dict, task_stats: Dict, output_file: str):
    """保存评测结果"""
    output = {
        "timestamp": datetime.now().isoformat(),
        "model_stats": model_stats,
        "task_stats": task_stats,
        "results": results
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)


def print_summary(model_stats: Dict, task_stats: Dict):
    """打印评测总结"""
    print("\n" + "=" * 60)
    print("评测完成！")
    print("\n=== 总体准确率 ===")
    for model in MODELS:
        stats = model_stats[model]
        accuracy = stats["correct"] / stats["total"] * 100 if stats["total"] > 0 else 0
        avg_latency = stats["total_latency"] / stats["total"] if stats["total"] > 0 else 0
        print(f"{model}: {stats['correct']}/{stats['total']} ({accuracy:.1f}%) 平均延迟: {avg_latency:.2f}s")
    
    print("\n=== 各任务类型准确率 ===")
    for task_type in sorted(task_stats.keys()):
        print(f"\n{task_type}:")
        for model in MODELS:
            stats = task_stats[task_type][model]
            accuracy = stats["correct"] / stats["total"] * 100 if stats["total"] > 0 else 0
            print(f"  {model}: {stats['correct']}/{stats['total']} ({accuracy:.1f}%)")


def reeval_from_results(results_file: str, output_file: str):
    """从已有结果重新评估（不重新调用API）"""
    with open(results_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    results = data['results']
    model_stats = {model: {"correct": 0, "total": 0, "total_latency": 0} for model in MODELS}
    task_stats = {}
    
    print(f"重新评估 {len(results)} 条结果...")
    
    for r in results:
        task_type = r['task_type']
        expected = r['expected']
        
        if task_type not in task_stats:
            task_stats[task_type] = {model: {"correct": 0, "total": 0} for model in MODELS}
        
        for model in MODELS:
            response = r.get(f'{model}_response', '')
            latency = r.get(f'{model}_latency', 0)
            
            # 重新提取答案
            thinking, answer = extract_answer_from_response(response, model)
            
            # 重新比较
            is_correct, match_detail = compare_answers(expected, answer, task_type)
            
            # 更新结果
            r[f'{model}_thinking'] = thinking
            r[f'{model}_answer'] = answer
            r[f'{model}_correct'] = is_correct
            r[f'{model}_match_detail'] = match_detail
            
            # 更新统计
            model_stats[model]["total"] += 1
            model_stats[model]["total_latency"] += latency
            if is_correct:
                model_stats[model]["correct"] += 1
            
            task_stats[task_type][model]["total"] += 1
            if is_correct:
                task_stats[task_type][model]["correct"] += 1
    
    # 保存
    save_results(results, model_stats, task_stats, output_file)
    print_summary(model_stats, task_stats)


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='图任务模型评测')
    parser.add_argument('--testset', default='tests/ontologydevos_graph_testset_v2.csv',
                        help='测试集文件路径')
    parser.add_argument('--output', default='tests/evaluation_results.json',
                        help='输出结果文件路径')
    parser.add_argument('--max-samples', type=int, default=None,
                        help='最大评测样本数')
    parser.add_argument('--reeval', type=str, default=None,
                        help='从已有结果文件重新评估')
    
    args = parser.parse_args()
    
    if args.reeval:
        print(f"从已有结果重新评估: {args.reeval}")
        reeval_from_results(args.reeval, args.output)
    else:
        print(f"测试集: {args.testset}")
        print(f"输出文件: {args.output}")
        if args.max_samples:
            print(f"最大样本数: {args.max_samples}")
        run_evaluation(args.testset, args.output, args.max_samples)


if __name__ == '__main__':
    main()
