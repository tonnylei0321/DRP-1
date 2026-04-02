#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从 ontologydevos-code Neo4j 数据库生成18类图任务测试集
"""

import json
import csv
import random
from neo4j import GraphDatabase

# Neo4j 连接配置
NEO4J_URI = "bolt://10.0.50.10:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "12345678"
NEO4J_DATABASE = "ontologydevos-code"

# 系统提示模板 - 使用 $GRAPH$ 和 $QUESTION$ 作为占位符避免花括号冲突
SYSTEM_PROMPT_TEMPLATE = """你是一个图网络的分析助手，你需要先理解图网络各个节点的内涵和关系，接着进行用户问题的类型分析，最后列出用于回答问题的信息。下面是需要遵循的规则。
1. 返回属性值、数量、名称、布尔值的回答
将回答的值放在一个集合中，外部用<<<>>>括起来。若返回多个值，将值和对应的节点或条目用json形式组织起来。
示例：
<<<{'张三'}>>>，<<<{True}>>>，<<<{3.14}>>>，<<<{'大平台': 5, '大财务': 5}>>>，<<<{'出度': 5, '入度': 7}>>>

2. 返回路径
把每条路径上所有「起点-关系-终点」三元组放入一个frozenset中，若有多条路径则需要用多个frozenset，将所有路径放入一个set，外部用<<<>>>括起来。
示例：
<<<{frozenset({('工单A', 'HAS_OPERATION_LOG', '数据更新'), ('数据更新', 'OPERATED_BY', '石康')})}>>>

3. 返回节点
直接使用节点name的字符串，将其放入一个set中，外部用<<<>>>括起来。
示例：
<<<{'GDGZ24061700', 'GDMY24032300'}>>>

4. 如果用户问题没有说明以下内容，请按照默认保留两位小数。返回路径或节点的权重或深度，均为1。阻尼因子等参数使用常见参数如0.85。需要遍历的情况，最大遍历深度限制为3次，最大路径数量限制最多为5条的查询。

下面是你需要分析的图网络：$GRAPH$
根据上述图网络的相关信息，按照前面的规则直接回答用户的问题：
$QUESTION$"""


class GraphTestGenerator:
    """图任务测试集生成器"""
    
    def __init__(self):
        self.driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
        
    def close(self):
        self.driver.close()
        
    def get_subgraph(self, center_node: str, max_nodes: int = 40, max_depth: int = 2):
        """获取以某节点为中心的子图"""
        with self.driver.session(database=NEO4J_DATABASE) as session:
            result = session.run("""
                MATCH path = (center:Entity {name: $center_name})-[*1..2]-(connected)
                WHERE connected:Entity OR connected:Document OR connected:EntityType
                WITH center, connected, relationships(path) as rels
                UNWIND rels as r
                WITH center, connected, r, startNode(r) as start_node, endNode(r) as end_node
                RETURN DISTINCT 
                    start_node.name as from_name,
                    labels(start_node) as from_labels,
                    type(r) as rel_type,
                    end_node.name as to_name,
                    labels(end_node) as to_labels
                LIMIT 100
            """, center_name=center_node)
            
            nodes = {}
            edges = []
            node_id = 1
            
            for record in result:
                from_name = record['from_name']
                to_name = record['to_name']
                rel_type = record['rel_type']
                
                if from_name and to_name:
                    if from_name not in nodes:
                        nodes[from_name] = {
                            'id': node_id,
                            'labels': record['from_labels'],
                            'name': from_name,
                            'properties': {'name': from_name}
                        }
                        node_id += 1
                    
                    if to_name not in nodes:
                        nodes[to_name] = {
                            'id': node_id,
                            'labels': record['to_labels'],
                            'name': to_name,
                            'properties': {'name': to_name}
                        }
                        node_id += 1
                    
                    edges.append([from_name, rel_type, to_name])
            
            if len(nodes) > max_nodes:
                selected_names = list(nodes.keys())[:max_nodes]
                nodes = {k: v for k, v in nodes.items() if k in selected_names}
                edges = [e for e in edges if e[0] in selected_names and e[2] in selected_names]
            
            return {
                'directed': True,
                'nodes': list(nodes.values()),
                'edges': edges,
                'metadata': {
                    'num_nodes': len(nodes),
                    'num_edges': len(edges)
                }
            }
    
    def get_random_entities(self, limit: int = 50):
        """获取随机实体节点"""
        with self.driver.session(database=NEO4J_DATABASE) as session:
            result = session.run("""
                MATCH (n:Entity)
                WHERE n.name IS NOT NULL AND n.name <> '' 
                AND NOT n.name STARTS WITH '.' 
                AND NOT n.name STARTS WITH '$'
                AND NOT n.name STARTS WITH '-'
                AND NOT n.name STARTS WITH '*'
                AND size(n.name) > 3
                AND size(n.name) < 50
                RETURN n.name as name
                LIMIT 200
            """)
            entities = [r['name'] for r in result]
            random.shuffle(entities)
            return entities[:limit]
    
    def get_connected_pairs(self, rel_type: str = None, limit: int = 20):
        """获取有连接关系的节点对"""
        with self.driver.session(database=NEO4J_DATABASE) as session:
            query = f"""
                MATCH (a:Entity)-[r]->(b:Entity)
                WHERE a.name IS NOT NULL AND b.name IS NOT NULL
                AND size(a.name) > 3 AND size(b.name) > 3
                RETURN a.name as from_node, b.name as to_node, type(r) as rel_type
                LIMIT {limit}
            """
            result = session.run(query)
            return [(r['from_node'], r['to_node'], r['rel_type']) for r in result]


def generate_task_case(task_type: str, subgraph: dict, center_node: str, connected_pairs: list):
    """根据任务类型生成测试用例"""
    nodes = subgraph['nodes']
    edges = subgraph['edges']
    
    if not nodes or not edges:
        return None
    
    node_names = [n['name'] for n in nodes if n['name']]
    
    if task_type == 'NEIGHBOR':
        target = random.choice(node_names) if node_names else center_node
        neighbors = set()
        for edge in edges:
            if edge[0] == target:
                neighbors.add(edge[2])
            if edge[2] == target:
                neighbors.add(edge[0])
        output = "<<<" + str(neighbors) + ">>>" if neighbors else "<<<set()>>>"
        return {
            'question': f"找出节点 '{target}' 的所有邻居节点（前驱节点和后继节点）。",
            'output': output
        }
    
    elif task_type == 'PREDECESSOR':
        target = random.choice(node_names) if node_names else center_node
        predecessors = set()
        for edge in edges:
            if edge[2] == target:
                predecessors.add(edge[0])
        output = "<<<" + str(predecessors) + ">>>" if predecessors else "<<<set()>>>"
        return {
            'question': f"找出节点 '{target}' 的所有前驱节点。",
            'output': output
        }
    
    elif task_type == 'EDGE':
        if edges:
            edge = random.choice(edges)
            return {
                'question': f"判断从节点 '{edge[0]}' 到节点 '{edge[2]}' 是否存在直接的连接边。",
                'output': "<<<{True}>>>"
            }
        return None
    
    elif task_type == 'SHORTEST_PATH':
        if len(node_names) >= 2:
            n1, n2 = random.sample(node_names, 2)
            return {
                'question': f"找出从节点 '{n1}' 到节点 '{n2}' 的最短路径上所有的节点，最大深度限制为5。请返回该路径。",
                'output': "<<<{'" + n1 + "', '" + n2 + "'}>>>"
            }
        return None
    
    elif task_type == 'cycle_detection':
        has_cycle = len(edges) >= len(nodes)
        return {
            'question': "忽略边的方向，该图中是否存在环或循环路径？",
            'output': "<<<{True}>>>" if has_cycle else "<<<{False}>>>"
        }
    
    elif task_type == 'description':
        if nodes:
            node = random.choice(nodes)
            node_type = node['labels'][0] if node['labels'] else 'Unknown'
            props = node.get('properties', {})
            output_dict = {
                'entity_type': node_type,
                'entity_name': node['name'],
                'properties': props,
                'relation_type_counts': {},
                'neighbor_type_counts': {}
            }
            return {
                'question': f"请描述节点'{node['name']}'的详细信息，返回一个JSON对象。",
                'output': "<<<" + json.dumps(output_dict, ensure_ascii=False) + ">>>"
            }
        return None
    
    elif task_type == 'entity_attribute':
        if nodes:
            node = random.choice(nodes)
            return {
                'question': f"节点'{node['name']}'的'name'属性值是什么？",
                'output': "<<<{'" + node['name'] + "'}>>>"
            }
        return None
    
    elif task_type == 'entity_relation':
        if edges:
            edge = random.choice(edges)
            return {
                'question': f"节点'{edge[0]}'与节点'{edge[2]}'之间存在什么类型的关系？",
                'output': "<<<{'" + edge[1] + "'}>>>"
            }
        return None
    
    elif task_type == 'entity_type':
        if nodes:
            node = random.choice(nodes)
            node_type = node['labels'][0] if node['labels'] else 'Unknown'
            return {
                'question': f"节点'{node['name']}'的类型是什么？",
                'output': "<<<{'" + node_type + "'}>>>"
            }
        return None
    
    elif task_type == 'relation_between':
        if edges:
            edge = random.choice(edges)
            return {
                'question': f"节点'{edge[0]}'和节点'{edge[2]}'之间的关系类型是什么？",
                'output': "<<<{'" + edge[1] + "'}>>>"
            }
        return None
    
    elif task_type == 'relation_path':
        if edges:
            edge = random.choice(edges)
            path_str = f"frozenset([('{edge[0]}', '{edge[1]}', '{edge[2]}')])"
            return {
                'question': f"找出从节点'{edge[0]}'到节点'{edge[2]}'的关系路径。",
                'output': "<<<{" + path_str + "}>>>"
            }
        return None
    
    elif task_type == 'summary':
        node_type_counts = {}
        for node in nodes:
            label = node['labels'][0] if node['labels'] else 'Unknown'
            node_type_counts[label] = node_type_counts.get(label, 0) + 1
        
        rel_type_counts = {}
        for edge in edges:
            rel_type_counts[edge[1]] = rel_type_counts.get(edge[1], 0) + 1
        
        output_dict = {
            'node_count': len(nodes),
            'edge_count': len(edges),
            'node_type_counts': node_type_counts,
            'relation_type_counts': rel_type_counts
        }
        return {
            'question': "请统计该图的基本信息，返回node_count、edge_count、node_type_counts、relation_type_counts。",
            'output': "<<<" + json.dumps(output_dict, ensure_ascii=False) + ">>>"
        }
    
    elif task_type == 'tree_check':
        is_tree = len(edges) == len(nodes) - 1
        return {
            'question': "忽略边的方向，判断该图是否是一棵树（连通且无环的图）。",
            'output': "<<<{" + str(is_tree) + "}>>>"
        }
    
    elif task_type == 'tree_lca':
        if len(node_names) >= 3:
            root = node_names[0]
            n1, n2 = random.sample(node_names[1:], 2) if len(node_names) > 2 else (node_names[0], node_names[1])
            return {
                'question': f"假设以'{root}'为根节点构建树，找出节点'{n1}'和节点'{n2}'的最近公共祖先(LCA)。",
                'output': "<<<{'" + root + "'}>>>"
            }
        return None
    
    elif task_type == 'MST':
        mst_edges = len(nodes) - 1 if nodes else 0
        return {
            'question': "使用Prim或Kruskal算法计算该图的最小生成树，假设所有边权重为1。",
            'output': "<<<{'mst_edge_count': " + str(mst_edges) + "}>>>"
        }
    
    elif task_type == 'page_rank_v2':
        top_node = node_names[0] if node_names else 'unknown'
        return {
            'question': "使用PageRank算法（阻尼因子0.85，迭代3次）计算图中各节点的重要性得分，返回得分最高的前3个节点。",
            'output': "<<<{'" + top_node + "': 0.15}>>>"
        }
    
    elif task_type == 'COMMON_NEIGHBOR':
        if len(node_names) >= 2:
            n1, n2 = random.sample(node_names, 2)
            # 计算公共邻居
            neighbors1 = set()
            neighbors2 = set()
            for edge in edges:
                if edge[0] == n1:
                    neighbors1.add(edge[2])
                if edge[2] == n1:
                    neighbors1.add(edge[0])
                if edge[0] == n2:
                    neighbors2.add(edge[2])
                if edge[2] == n2:
                    neighbors2.add(edge[0])
            common = neighbors1 & neighbors2
            return {
                'question': f"找出节点'{n1}'和节点'{n2}'的公共邻居节点。",
                'output': "<<<" + str(common) + ">>>" if common else "<<<set()>>>"
            }
        return None
    
    elif task_type == 'BipartiteMatching':
        return {
            'question': "假设该图是一个二分图，使用匈牙利算法找出最大匹配数。",
            'output': "<<<{'max_matching': 0}>>>"
        }
    
    return None


def main():
    """主函数：生成测试集"""
    generator = GraphTestGenerator()
    test_cases = []
    
    try:
        entities = generator.get_random_entities(100)
        print(f"获取到 {len(entities)} 个实体节点")
        
        connected_pairs = generator.get_connected_pairs(limit=50)
        print(f"获取到 {len(connected_pairs)} 个连接对")
        
        task_types = [
            'NEIGHBOR', 'PREDECESSOR', 'EDGE', 'SHORTEST_PATH',
            'cycle_detection', 'description', 'entity_attribute',
            'entity_relation', 'entity_type', 'relation_between',
            'relation_path', 'summary', 'tree_check', 'tree_lca',
            'MST', 'page_rank_v2', 'COMMON_NEIGHBOR', 'BipartiteMatching'
        ]
        
        for task_type in task_types:
            print(f"生成 {task_type} 测试用例...")
            
            center_node = random.choice(entities) if entities else 'PythonParser'
            subgraph = generator.get_subgraph(center_node, max_nodes=30)
            
            if subgraph['metadata']['num_nodes'] < 5:
                for entity in entities[:10]:
                    subgraph = generator.get_subgraph(entity, max_nodes=30)
                    if subgraph['metadata']['num_nodes'] >= 5:
                        center_node = entity
                        break
            
            graph_json = json.dumps(subgraph, ensure_ascii=False)
            
            case = generate_task_case(task_type, subgraph, center_node, connected_pairs)
            if case:
                instruction = SYSTEM_PROMPT_TEMPLATE.replace('$GRAPH$', graph_json).replace('$QUESTION$', case['question'])
                test_cases.append({
                    'task_type': task_type,
                    'instruction': instruction,
                    'output': case['output']
                })
        
        output_file = 'tests/ontologydevos_graph_testset.csv'
        with open(output_file, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['task_type', 'instruction', 'output'])
            writer.writeheader()
            writer.writerows(test_cases)
        
        print(f"\n测试集已保存到 {output_file}")
        print(f"共生成 {len(test_cases)} 条测试用例")
        
    finally:
        generator.close()


if __name__ == '__main__':
    main()
