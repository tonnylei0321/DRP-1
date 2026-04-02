#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从 ontologydevos-code Neo4j 数据库生成18类图任务测试集 - 增强版
每种任务类型生成多个测试用例
"""

import json
import csv
import random
from neo4j import GraphDatabase

NEO4J_URI = "bolt://10.0.50.10:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "12345678"
NEO4J_DATABASE = "ontologydevos-code"

SYSTEM_PROMPT_TEMPLATE = """你是一个图网络的分析助手，你需要先理解图网络各个节点的内涵和关系，接着进行用户问题的类型分析，最后列出用于回答问题的信息。下面是需要遵循的规则。
1. 返回属性值、数量、名称、布尔值的回答
将回答的值放在一个集合中，外部用<<<>>>括起来。若返回多个值，将值和对应的节点或条目用json形式组织起来。
示例：
<<<{'张三'}>>>，<<<{True}>>>，<<<{3.14}>>>，<<<{'大平台': 5, '大财务': 5}>>>，<<<{'出度': 5, '入度': 7}>>>

2. 返回路径
把每条路径上所有「起点-关系-终点」三元组放入一个frozenset中，若有多条路径则需要用多个frozenset，将所有路径放入一个set，外部用<<<>>>括起来。

3. 返回节点
直接使用节点name的字符串，将其放入一个set中，外部用<<<>>>括起来。
示例：
<<<{'GDGZ24061700', 'GDMY24032300'}>>>

4. 如果用户问题没有说明以下内容，请按照默认保留两位小数。返回路径或节点的权重或深度，均为1。阻尼因子等参数使用常见参数如0.85。需要遍历的情况，最大遍历深度限制为3次，最大路径数量限制最多为5条的查询。

下面是你需要分析的图网络：$GRAPH$
根据上述图网络的相关信息，按照前面的规则直接回答用户的问题：
$QUESTION$"""


class GraphTestGenerator:
    def __init__(self):
        self.driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
        
    def close(self):
        self.driver.close()
        
    def get_subgraph(self, center_node: str, max_nodes: int = 40):
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
                LIMIT 150
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
                    
                    edge_tuple = (from_name, rel_type, to_name)
                    if [from_name, rel_type, to_name] not in edges:
                        edges.append([from_name, rel_type, to_name])
            
            if len(nodes) > max_nodes:
                selected_names = list(nodes.keys())[:max_nodes]
                nodes = {k: v for k, v in nodes.items() if k in selected_names}
                edges = [e for e in edges if e[0] in selected_names and e[2] in selected_names]
            
            return {
                'directed': True,
                'nodes': list(nodes.values()),
                'edges': edges,
                'metadata': {'num_nodes': len(nodes), 'num_edges': len(edges)}
            }
    
    def get_random_entities(self, limit: int = 100):
        with self.driver.session(database=NEO4J_DATABASE) as session:
            result = session.run("""
                MATCH (n:Entity)
                WHERE n.name IS NOT NULL AND n.name <> '' 
                AND NOT n.name STARTS WITH '.' 
                AND NOT n.name STARTS WITH '$'
                AND NOT n.name STARTS WITH '-'
                AND NOT n.name STARTS WITH '*'
                AND NOT n.name STARTS WITH '#'
                AND size(n.name) > 3
                AND size(n.name) < 50
                RETURN n.name as name
                LIMIT 500
            """)
            entities = [r['name'] for r in result]
            random.shuffle(entities)
            return entities[:limit]


def generate_task_case(task_type: str, subgraph: dict, center_node: str):
    nodes = subgraph['nodes']
    edges = subgraph['edges']
    
    if not nodes or not edges:
        return None
    
    node_names = [n['name'] for n in nodes if n['name']]
    
    if task_type == 'NEIGHBOR':
        target = random.choice(node_names)
        neighbors = set()
        for edge in edges:
            if edge[0] == target:
                neighbors.add(edge[2])
            if edge[2] == target:
                neighbors.add(edge[0])
        return {
            'question': f"找出节点 '{target}' 的所有邻居节点（前驱节点和后继节点）。",
            'output': "<<<" + str(neighbors) + ">>>" if neighbors else "<<<set()>>>"
        }
    
    elif task_type == 'PREDECESSOR':
        target = random.choice(node_names)
        predecessors = set()
        for edge in edges:
            if edge[2] == target:
                predecessors.add(edge[0])
        return {
            'question': f"找出节点 '{target}' 的所有前驱节点。",
            'output': "<<<" + str(predecessors) + ">>>" if predecessors else "<<<set()>>>"
        }
    
    elif task_type == 'EDGE':
        edge = random.choice(edges)
        return {
            'question': f"判断从节点 '{edge[0]}' 到节点 '{edge[2]}' 是否存在直接的连接边。",
            'output': "<<<{True}>>>"
        }
    
    elif task_type == 'SHORTEST_PATH':
        if len(node_names) >= 2:
            # 构建无向邻接表
            adj = {name: set() for name in node_names}
            for edge in edges:
                if edge[0] in adj and edge[2] in adj:
                    adj[edge[0]].add(edge[2])
                    adj[edge[2]].add(edge[0])

            # 随机选择起点和终点
            n1, n2 = random.sample(node_names, 2)

            # BFS 找最短路径
            def bfs_shortest_path(start, end):
                if start == end:
                    return [start]
                visited = {start}
                queue = [(start, [start])]
                while queue:
                    node, path = queue.pop(0)
                    if len(path) > 5:  # 最大深度限制
                        continue
                    for neighbor in adj.get(node, set()):
                        if neighbor == end:
                            return path + [neighbor]
                        if neighbor not in visited:
                            visited.add(neighbor)
                            queue.append((neighbor, path + [neighbor]))
                return []

            path = bfs_shortest_path(n1, n2)
            if path:
                path_str = ", ".join([f"'{n}'" for n in path])
                return {
                    'question': f"找出从节点 '{n1}' 到节点 '{n2}' 的最短路径上所有的节点，最大深度限制为5。",
                    'output': "<<<{" + path_str + "}>>>"
                }
            else:
                return {
                    'question': f"找出从节点 '{n1}' 到节点 '{n2}' 的最短路径上所有的节点，最大深度限制为5。",
                    'output': "<<<set()>>>"
                }
        return None
    
    elif task_type == 'cycle_detection':
        has_cycle = len(edges) >= len(nodes)
        return {
            'question': "忽略边的方向，该图中是否存在环或循环路径？",
            'output': "<<<{True}>>>" if has_cycle else "<<<{False}>>>"
        }
    
    elif task_type == 'description':
        node = random.choice(nodes)
        node_type = node['labels'][0] if node['labels'] else 'Unknown'
        output_dict = {
            'entity_type': node_type,
            'entity_name': node['name'],
            'properties': node.get('properties', {}),
            'relation_type_counts': {},
            'neighbor_type_counts': {}
        }
        return {
            'question': f"请描述节点'{node['name']}'的详细信息，返回一个JSON对象。",
            'output': "<<<" + json.dumps(output_dict, ensure_ascii=False) + ">>>"
        }
    
    elif task_type == 'entity_attribute':
        node = random.choice(nodes)
        return {
            'question': f"节点'{node['name']}'的'name'属性值是什么？",
            'output': "<<<{'" + node['name'] + "'}>>>"
        }
    
    elif task_type == 'entity_relation':
        edge = random.choice(edges)
        return {
            'question': f"节点'{edge[0]}'与节点'{edge[2]}'之间存在什么类型的关系？",
            'output': "<<<{'" + edge[1] + "'}>>>"
        }
    
    elif task_type == 'entity_type':
        node = random.choice(nodes)
        node_type = node['labels'][0] if node['labels'] else 'Unknown'
        return {
            'question': f"节点'{node['name']}'的类型是什么？",
            'output': "<<<{'" + node_type + "'}>>>"
        }
    
    elif task_type == 'relation_between':
        edge = random.choice(edges)
        return {
            'question': f"节点'{edge[0]}'和节点'{edge[2]}'之间的关系类型是什么？",
            'output': "<<<{'" + edge[1] + "'}>>>"
        }
    
    elif task_type == 'relation_path':
        edge = random.choice(edges)
        path_str = f"frozenset([('{edge[0]}', '{edge[1]}', '{edge[2]}')])"
        return {
            'question': f"找出从节点'{edge[0]}'到节点'{edge[2]}'的关系路径。",
            'output': "<<<{" + path_str + "}>>>"
        }
    
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
            # 构建邻接表（忽略方向）
            adj = {name: set() for name in node_names}
            for edge in edges:
                if edge[0] in adj and edge[2] in adj:
                    adj[edge[0]].add(edge[2])
                    adj[edge[2]].add(edge[0])

            # 找到度数最高的节点作为根（通常是中心节点）
            root = max(node_names, key=lambda n: len(adj.get(n, set())))

            # 选择两个非根节点
            non_root_nodes = [n for n in node_names if n != root and len(adj.get(n, set())) > 0]
            if len(non_root_nodes) >= 2:
                n1, n2 = random.sample(non_root_nodes, 2)

                # 计算从根到n1和n2的路径，找LCA
                # 简化：如果n1和n2都直接连接到root，则LCA就是root
                # 否则需要BFS找路径
                def bfs_path(start, end):
                    if start == end:
                        return [start]
                    visited = {start}
                    queue = [(start, [start])]
                    while queue:
                        node, path = queue.pop(0)
                        for neighbor in adj.get(node, set()):
                            if neighbor == end:
                                return path + [neighbor]
                            if neighbor not in visited:
                                visited.add(neighbor)
                                queue.append((neighbor, path + [neighbor]))
                    return []

                path1 = bfs_path(root, n1)
                path2 = bfs_path(root, n2)

                # 找最近公共祖先
                lca = root
                for i in range(min(len(path1), len(path2))):
                    if path1[i] == path2[i]:
                        lca = path1[i]
                    else:
                        break

                return {
                    'question': f"假设以'{root}'为根节点构建树，找出节点'{n1}'和节点'{n2}'的最近公共祖先(LCA)。",
                    'output': "<<<{'" + lca + "'}>>>"
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
            neighbors1 = set()
            neighbors2 = set()
            for edge in edges:
                if edge[0] == n1: neighbors1.add(edge[2])
                if edge[2] == n1: neighbors1.add(edge[0])
                if edge[0] == n2: neighbors2.add(edge[2])
                if edge[2] == n2: neighbors2.add(edge[0])
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
    generator = GraphTestGenerator()
    test_cases = []
    
    try:
        entities = generator.get_random_entities(200)
        print(f"获取到 {len(entities)} 个实体节点")
        
        task_types = [
            'NEIGHBOR', 'PREDECESSOR', 'EDGE', 'SHORTEST_PATH',
            'cycle_detection', 'description', 'entity_attribute',
            'entity_relation', 'entity_type', 'relation_between',
            'relation_path', 'summary', 'tree_check', 'tree_lca',
            'MST', 'page_rank_v2', 'COMMON_NEIGHBOR', 'BipartiteMatching'
        ]
        
        samples_per_type = 3  # 每种类型生成3个样本
        
        for task_type in task_types:
            print(f"生成 {task_type} 测试用例...")
            generated = 0
            attempts = 0
            
            while generated < samples_per_type and attempts < 20:
                attempts += 1
                center_node = random.choice(entities)
                subgraph = generator.get_subgraph(center_node, max_nodes=35)
                
                if subgraph['metadata']['num_nodes'] < 5:
                    continue
                
                graph_json = json.dumps(subgraph, ensure_ascii=False)
                case = generate_task_case(task_type, subgraph, center_node)
                
                if case:
                    instruction = SYSTEM_PROMPT_TEMPLATE.replace('$GRAPH$', graph_json).replace('$QUESTION$', case['question'])
                    test_cases.append({
                        'task_type': task_type,
                        'instruction': instruction,
                        'output': case['output']
                    })
                    generated += 1
            
            print(f"  生成了 {generated} 个样本")
        
        output_file = 'tests/ontologydevos_graph_testset_v2.csv'
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
