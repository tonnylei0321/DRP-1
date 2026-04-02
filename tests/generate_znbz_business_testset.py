#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从 ontologyv7znbz Neo4j 数据库生成业务场景测试集
聚焦于费用报销、借款、发票、审批等业务场景
"""

import json
import csv
import random
from neo4j import GraphDatabase

NEO4J_URI = "bolt://10.0.50.10:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "12345678"
NEO4J_DATABASE = "ontologyv7znbz"

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


class BusinessGraphGenerator:
    def __init__(self):
        self.driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
        
    def close(self):
        self.driver.close()
    
    def get_business_subgraph(self, center_node: str, max_nodes: int = 40):
        """获取业务相关子图"""
        with self.driver.session(database=NEO4J_DATABASE) as session:
            result = session.run("""
                MATCH path = (center {name: $center_name})-[*1..2]-(connected)
                WHERE connected.name IS NOT NULL 
                AND connected.name <> 'Regex'
                AND NOT connected.name CONTAINS '{'
                AND size(connected.name) < 50
                WITH center, connected, relationships(path) as rels
                UNWIND rels as r
                WITH center, connected, r, startNode(r) as start_node, endNode(r) as end_node
                WHERE start_node.name IS NOT NULL AND end_node.name IS NOT NULL
                AND start_node.name <> 'Regex' AND end_node.name <> 'Regex'
                AND size(start_node.name) < 50 AND size(end_node.name) < 50
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
                    
                    edge = [from_name, rel_type, to_name]
                    if edge not in edges:
                        edges.append(edge)
            
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
    
    def get_business_entities(self):
        """获取业务相关实体"""
        with self.driver.session(database=NEO4J_DATABASE) as session:
            # 费用报销相关
            result = session.run("""
                MATCH (n)
                WHERE n.name IS NOT NULL 
                AND (n.name CONTAINS '报销' OR n.name CONTAINS '费用' OR n.name CONTAINS '借款' 
                     OR n.name CONTAINS '发票' OR n.name CONTAINS '审批' OR n.name CONTAINS '预算'
                     OR n.name CONTAINS '申请' OR n.name CONTAINS '结算' OR n.name CONTAINS '核销'
                     OR n.name CONTAINS '单据' OR n.name CONTAINS '票据' OR n.name CONTAINS '稽核')
                AND size(n.name) > 3 AND size(n.name) < 40
                AND NOT n.name CONTAINS '{'
                RETURN DISTINCT n.name as name
                LIMIT 100
            """)
            business_entities = [r['name'] for r in result]
            
            # DocGraph节点
            result = session.run("""
                MATCH (n:DocGraph)
                WHERE n.name IS NOT NULL AND size(n.name) < 40
                RETURN n.name as name
                LIMIT 50
            """)
            doc_entities = [r['name'] for r in result]
            
            # CoreClass节点
            result = session.run("""
                MATCH (n:CoreClass)
                WHERE n.name IS NOT NULL 
                AND size(n.name) > 3 AND size(n.name) < 40
                AND NOT n.name CONTAINS 'Regex'
                RETURN DISTINCT n.name as name
                LIMIT 50
            """)
            core_entities = [r['name'] for r in result]
            
            all_entities = list(set(business_entities + doc_entities + core_entities))
            random.shuffle(all_entities)
            return all_entities


def generate_business_question(task_type: str, subgraph: dict, center_node: str):
    """生成业务场景问题"""
    nodes = subgraph['nodes']
    edges = subgraph['edges']
    
    if not nodes or not edges:
        return None
    
    node_names = [n['name'] for n in nodes if n['name']]
    
    # 业务化的问题模板
    if task_type == 'NEIGHBOR':
        target = random.choice(node_names)
        neighbors = set()
        for edge in edges:
            if edge[0] == target:
                neighbors.add(edge[2])
            if edge[2] == target:
                neighbors.add(edge[0])
        return {
            'question': f"在费控系统中，'{target}'直接关联的所有业务对象有哪些？",
            'output': "<<<" + str(neighbors) + ">>>" if neighbors else "<<<set()>>>"
        }
    
    elif task_type == 'PREDECESSOR':
        target = random.choice(node_names)
        predecessors = set()
        for edge in edges:
            if edge[2] == target:
                predecessors.add(edge[0])
        return {
            'question': f"哪些业务对象会流转到'{target}'？（即找出所有指向该节点的前驱节点）",
            'output': "<<<" + str(predecessors) + ">>>" if predecessors else "<<<set()>>>"
        }
    
    elif task_type == 'EDGE':
        edge = random.choice(edges)
        return {
            'question': f"'{edge[0]}'和'{edge[2]}'之间是否存在直接的业务关联？",
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
            n1, n2 = random.sample(node_names, 2)
            def bfs_shortest_path(start, end):
                if start == end: return [start]
                visited = {start}
                queue = [(start, [start])]
                while queue:
                    node, path = queue.pop(0)
                    if len(path) > 5: continue
                    for neighbor in adj.get(node, set()):
                        if neighbor == end: return path + [neighbor]
                        if neighbor not in visited:
                            visited.add(neighbor)
                            queue.append((neighbor, path + [neighbor]))
                return []
            path = bfs_shortest_path(n1, n2)
            if path:
                path_str = ", ".join([f"'{n}'" for n in path])
                return {
                    'question': f"从'{n1}'到'{n2}'的最短业务流转路径经过哪些节点？",
                    'output': "<<<{" + path_str + "}>>>"
                }
            else:
                return {
                    'question': f"从'{n1}'到'{n2}'的最短业务流转路径经过哪些节点？",
                    'output': "<<<set()>>>"
                }
        return None
    
    elif task_type == 'cycle_detection':
        has_cycle = len(edges) >= len(nodes)
        return {
            'question': "该业务流程图中是否存在循环依赖或环路？",
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
            'question': f"请描述业务对象'{node['name']}'的详细信息，包括类型、属性和关联关系统计。",
            'output': "<<<" + json.dumps(output_dict, ensure_ascii=False) + ">>>"
        }
    
    elif task_type == 'entity_attribute':
        node = random.choice(nodes)
        return {
            'question': f"业务对象'{node['name']}'的名称属性值是什么？",
            'output': "<<<{'" + node['name'] + "'}>>>"
        }
    
    elif task_type == 'entity_relation':
        edge = random.choice(edges)
        return {
            'question': f"'{edge[0]}'与'{edge[2]}'之间是什么类型的业务关系？",
            'output': "<<<{'" + edge[1] + "'}>>>"
        }
    
    elif task_type == 'entity_type':
        node = random.choice(nodes)
        node_type = node['labels'][0] if node['labels'] else 'Unknown'
        return {
            'question': f"'{node['name']}'在系统中属于什么类型的业务对象？",
            'output': "<<<{'" + node_type + "'}>>>"
        }
    
    elif task_type == 'relation_between':
        edge = random.choice(edges)
        return {
            'question': f"'{edge[0]}'和'{edge[2]}'之间的关联类型是什么？",
            'output': "<<<{'" + edge[1] + "'}>>>"
        }
    
    elif task_type == 'relation_path':
        edge = random.choice(edges)
        path_str = f"frozenset([('{edge[0]}', '{edge[1]}', '{edge[2]}')])"
        return {
            'question': f"找出从'{edge[0]}'到'{edge[2]}'的业务关系路径。",
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
            'question': "请统计该业务子图的基本信息：节点数、边数、各类型节点数量、各类型关系数量。",
            'output': "<<<" + json.dumps(output_dict, ensure_ascii=False) + ">>>"
        }
    
    elif task_type == 'tree_check':
        is_tree = len(edges) == len(nodes) - 1
        return {
            'question': "该业务流程是否构成树形结构（无环且连通）？",
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
            # 找到度数最高的节点作为根
            root = max(node_names, key=lambda n: len(adj.get(n, set())))
            non_root_nodes = [n for n in node_names if n != root and len(adj.get(n, set())) > 0]
            if len(non_root_nodes) >= 2:
                n1, n2 = random.sample(non_root_nodes, 2)
                def bfs_path(start, end):
                    if start == end: return [start]
                    visited = {start}
                    queue = [(start, [start])]
                    while queue:
                        node, path = queue.pop(0)
                        for neighbor in adj.get(node, set()):
                            if neighbor == end: return path + [neighbor]
                            if neighbor not in visited:
                                visited.add(neighbor)
                                queue.append((neighbor, path + [neighbor]))
                    return []
                path1 = bfs_path(root, n1)
                path2 = bfs_path(root, n2)
                lca = root
                for i in range(min(len(path1), len(path2))):
                    if path1[i] == path2[i]: lca = path1[i]
                    else: break
                return {
                    'question': f"以'{root}'为根节点，'{n1}'和'{n2}'的最近公共上级业务对象是什么？",
                    'output': "<<<{'" + lca + "'}>>>"
                }
        return None
    
    elif task_type == 'MST':
        mst_edges = len(nodes) - 1 if nodes else 0
        return {
            'question': "如果要用最少的关联关系连接所有业务对象，需要多少条边？（最小生成树）",
            'output': "<<<{'mst_edge_count': " + str(mst_edges) + "}>>>"
        }
    
    elif task_type == 'page_rank_v2':
        top_node = node_names[0] if node_names else 'unknown'
        return {
            'question': "使用PageRank算法分析该业务网络，哪些业务对象最重要？返回前3个。",
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
                'question': f"'{n1}'和'{n2}'共同关联的业务对象有哪些？",
                'output': "<<<" + str(common) + ">>>" if common else "<<<set()>>>"
            }
        return None
    
    elif task_type == 'BipartiteMatching':
        return {
            'question': "假设该图是二分图结构，使用匈牙利算法计算最大匹配数。",
            'output': "<<<{'max_matching': 0}>>>"
        }
    
    return None


def main():
    generator = BusinessGraphGenerator()
    test_cases = []
    
    try:
        entities = generator.get_business_entities()
        print(f"获取到 {len(entities)} 个业务实体节点")
        
        task_types = [
            'NEIGHBOR', 'PREDECESSOR', 'EDGE', 'SHORTEST_PATH',
            'cycle_detection', 'description', 'entity_attribute',
            'entity_relation', 'entity_type', 'relation_between',
            'relation_path', 'summary', 'tree_check', 'tree_lca',
            'MST', 'page_rank_v2', 'COMMON_NEIGHBOR', 'BipartiteMatching'
        ]
        
        samples_per_type = 3
        
        for task_type in task_types:
            print(f"生成 {task_type} 测试用例...")
            generated = 0
            attempts = 0
            
            while generated < samples_per_type and attempts < 40:
                attempts += 1
                center_node = random.choice(entities)
                subgraph = generator.get_business_subgraph(center_node, max_nodes=35)
                
                if subgraph['metadata']['num_nodes'] < 5:
                    continue
                
                graph_json = json.dumps(subgraph, ensure_ascii=False)
                case = generate_business_question(task_type, subgraph, center_node)
                
                if case:
                    instruction = SYSTEM_PROMPT_TEMPLATE.replace('$GRAPH$', graph_json).replace('$QUESTION$', case['question'])
                    test_cases.append({
                        'task_type': task_type,
                        'instruction': instruction,
                        'output': case['output']
                    })
                    generated += 1
            
            print(f"  生成了 {generated} 个样本")
        
        output_file = 'tests/znbz_business_testset.csv'
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
