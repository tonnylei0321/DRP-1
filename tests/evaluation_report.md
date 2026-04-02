# 图任务模型评测报告

**生成时间**: 2026-02-06T12:19:56.988271

**评测样本数**: 54

**评测模型**: graph_rl, graph_sft


## 1. 总体评测结果

| 模型 | 正确数 | 总数 | 准确率 | 平均延迟 |
|------|--------|------|--------|----------|
| graph_rl | 48 | 54 | 88.9% | 26.64s |
| graph_sft | 38 | 54 | 70.4% | 0.59s |

## 2. 各任务类型准确率

| 任务类型 | graph_rl 准确率 | graph_sft 准确率 |
|----------|----------|----------|
| BipartiteMatching | 0/3 (0%) | 0/3 (0%) |
| COMMON_NEIGHBOR | 3/3 (100%) | 3/3 (100%) |
| EDGE | 3/3 (100%) | 3/3 (100%) |
| MST | 3/3 (100%) | 2/3 (67%) |
| NEIGHBOR | 3/3 (100%) | 3/3 (100%) |
| PREDECESSOR | 3/3 (100%) | 0/3 (0%) |
| SHORTEST_PATH | 2/3 (67%) | 1/3 (33%) |
| cycle_detection | 3/3 (100%) | 3/3 (100%) |
| description | 3/3 (100%) | 3/3 (100%) |
| entity_attribute | 3/3 (100%) | 3/3 (100%) |
| entity_relation | 3/3 (100%) | 3/3 (100%) |
| entity_type | 3/3 (100%) | 3/3 (100%) |
| page_rank_v2 | 3/3 (100%) | 0/3 (0%) |
| relation_between | 3/3 (100%) | 3/3 (100%) |
| relation_path | 3/3 (100%) | 3/3 (100%) |
| summary | 3/3 (100%) | 3/3 (100%) |
| tree_check | 3/3 (100%) | 1/3 (33%) |
| tree_lca | 1/3 (33%) | 2/3 (67%) |

## 3. 详细评测结果


### 3.1 BipartiteMatching

#### 样本 1

**预期输出**: `<<<{'max_matching': 0}>>>`

**graph_rl** ❌ (不匹配, 21.0s)
```
首先，用户的问题是：“假设该图是一个二分图，使用匈牙利算法找出最大匹配数。”

我需要理解这个图网络。根据提供的JSON，图是直接的（directed: true），但用户假设它是一个二分图。二分图通常指的是图的节点集可以分成两个不相交的子集，使得图中所有边都从一个子集连接到另一个子集。

查看图的定义：
- 节点有标签：有些节点有标签 "Entity"，有些有标签 "EntityType"。
- 具体来说，节点列表中：
  - 节点1：id=1, labels=["Entity"], name="Call", properties={"name": "Call"}
  - 节点2：id=2, labels=["EntityType"], name="Design", properties={"name": "Design"}
  - 其他节点：大部分有标签 ["Entity"]，但节点2有标签 ["EntityType"]。

在edges部分，所有边都是从一个节点到另一个节点，关系是 "IS_A"。例如：
- ["Call", "IS_A", "Design"]
- ["sdd_i...
```

**graph_sft** ❌ (不匹配, 1.0s)
```
<<<{35}>>>
```

#### 样本 2

**预期输出**: `<<<{'max_matching': 0}>>>`

**graph_rl** ❌ (不匹配, 21.5s)
```
首先，用户的问题是：“假设该图是一个二分图，使用匈牙利算法找出最大匹配数。”

我需要理解这个图网络。根据提供的信息，图是直接的（directed: true），但用户假设它是一个二分图。二分图通常是指图的节点可以分为两个不相交的集合，使得所有边都从一个集合到另一个集合。

查看图的描述：
- 节点有标签：有些节点有标签 "Entity"，有些有标签 "EntityType"。
- 具体来说，节点列表中：
  - 节点1：id=1, labels=["Entity"], name="CodeQualityAnalysis", properties={"name": "CodeQualityAnalysis"}
  - 节点2：id=2, labels=["EntityType"], name="Requirement", properties={"name": "Requirement"}
  - 其他节点类似，大部分有标签 ["Entity"]，但节点2有标签 ["EntityType"]。

在edges部分，所有边都是 "IS_A" 关系，连接到 "Requirement"。例如...
```

**graph_sft** ❌ (不匹配, 0.5s)
```
<<<{35}>>>
```

#### 样本 3

**预期输出**: `<<<{'max_matching': 0}>>>`

**graph_rl** ❌ (不匹配, 39.7s)
```
首先，用户的问题是：“假设该图是一个二分图，使用匈牙利算法找出最大匹配数。”

我需要理解这个图网络。根据提供的信息，图是直接的（directed: true），但用户假设它是一个二分图。二分图是图论中的一种图，其节点集可以分成两个不相交的子集，使得图中所有边都从一个子集连接到另一个子集。

在给定的图中，节点有标签：有些节点有标签 "Entity"，有些有标签 "EntityType"。具体看：

- 节点列表：每个节点有id、labels、name和properties。

- edges：所有边都是 "IS_A" 关系，连接两个节点。

关键点：在二分图中，节点被分成两个部分：左部和右部。边只在两个部分之间。

但在这个图中，所有边都是 "IS_A" 关系，连接了节点。例如：

- ["CLAUDE_PROJECT_DIR", "IS_A", "CodeField"]

- ["hooks", "IS_A", "CodeField"]

等等。

注意：在edges列表中，每个边都以 "IS_A" 关系连接两个节点。但看节点的标签：

- 节点1：id=1, labels=["E...
```

**graph_sft** ❌ (不匹配, 0.3s)
```
<<<{35}>>>
```


### 3.2 COMMON_NEIGHBOR

#### 样本 1

**预期输出**: `<<<{'CodeMethod'}>>>`

**graph_rl** ✅ (精确匹配, 33.9s)
```
首先，我需要理解用户的问题："找出节点'Research'和节点'add_child'的公共邻居节点。"

根据规则，我需要分析图网络，找出这两个节点的公共邻居节点。公共邻居节点是指同时与节点'Research'和节点'add_child'都直接相连的节点。

回顾图网络的描述：
- 图是定向的（directed: true）。
- 节点有ID、标签、名称和属性。
- 边（edges）表示节点之间的关系。

从图网络数据中，我需要找到节点'Research'和节点'add_child'的邻居节点。

首先，确定节点'Research'和'add_child'的ID。

在图网络的nodes列表中：
- 节点34的名称是"实现/测试/提交/自审"，但用户提到了'Research'，所以我要找名称为'Research'的节点。
- 检查nodes列表：
  - id 25: {"id": 25, "labels": ["Entity"], "name": "Research", "properties": {"name": "Research"}}
  - id 15: {"id": 15...
```

**graph_sft** ✅ (精确匹配, 1.6s)
```
<<<{'CodeMethod'}>>>
```

#### 样本 2

**预期输出**: `<<<{'CodeMethod'}>>>`

**graph_rl** ✅ (精确匹配, 34.2s)
```
首先，我需要理解用户的问题："找出节点'save_analysis_result'和节点'find_source_files'的公共邻居节点。"

根据规则，我需要分析图网络，找出这两个节点的公共邻居节点。公共邻居节点是指在图中同时与这两个节点有边连接的节点。

回顾图网络的定义：
- 图是定向的（directed: true）。
- 节点有ID、标签、名称和属性。
- 边是关系，这里所有边都是"IS_A"关系，表示"是"或"属于"。

从图网络数据中提取节点信息：
- 节点'save_analysis_result'：ID为10，名称是"save_analysis_result"，标签是["Entity"]。
- 节点'find_source_files'：ID为8，名称是"find_source_files"，标签是["Entity"]。

现在，我需要找到与这两个节点都直接相连的节点。也就是说，对于节点10（save_analysis_result）和节点8（find_source_files），找出所有同时与它们有边连接的节点。

在图中，边是表示关系的。这里所有边都是"IS_...
```

**graph_sft** ✅ (精确匹配, 0.6s)
```
<<<{'CodeMethod'}>>>
```

#### 样本 3

**预期输出**: `<<<{'CodeComponent'}>>>`

**graph_rl** ✅ (精确匹配, 33.8s)
```
首先，我需要理解图网络的结构。图网络是直接的（directed: true），有35个节点和35条边。节点有ID、标签、名称和属性。边是关系，表示节点之间的连接。

用户的问题是：“找出节点'CG'和节点'CLAUDE.md'的公共邻居节点。”

在图论中，公共邻居节点指的是同时与两个给定节点相连的节点。也就是说，对于节点A和节点B，公共邻居是那些既与A相连又与B相连的节点。

这里，给定的节点是'CG'和'CLAUDE.md'。我需要找到所有与'CG'有边连接的节点，以及所有与'CLAUDE.md'有边连接的节点，然后找出它们的交集。

首先，我应该从图网络中提取出节点'CG'和'CLAUDE.md'的邻居。

回顾图网络的描述：

- 节点列表：每个节点有id、labels、name和properties。

- 边列表：每条边是[起点, 关系, 终点]。

在边列表中，关系是"IS_A"，这表示一种类型关系。例如，["CeleryTask", "IS_A", "CodeComponent"] 意思是CeleryTask是CodeComponent的一种。

但问题是要找公共邻居，...
```

**graph_sft** ✅ (精确匹配, 0.8s)
```
<<<{'CodeComponent'}>>>
```


### 3.3 EDGE

#### 样本 1

**预期输出**: `<<<{True}>>>`

**graph_rl** ✅ (精确匹配, 5.8s)
```
首先，我需要理解用户的问题："判断从节点 '自治Claude实例' 到节点 'Design' 是否存在直接的连接边。"

根据规则，我必须先分析图网络的结构。图网络是给定的JSON对象，包含节点和边的信息。

关键点是：用户想知道从节点 "自治Claude实例" 到节点 "Design" 是否有直接的连接边。

在图网络中，边是用列表表示的。每个边是一个三元组：[起点, 关系, 终点]。

查看图网络的edges部分：

edges: [
  ["Archive", "IS_A", "Design"],
  ["sdd_integration.openspec_parser.Design", "IS_A", "Design"],
  ...（其他边）...
  ["自治Claude实例", "IS_A", "Design"]
]

具体地，最后一行是：["自治Claude实例", "IS_A", "Design"]

这表示有一个边，起点是 "自治Claude实例"，关系是 "IS_A"，终点是 "Design"。

所以，从节点 "自治Claude实例" 到节点 "Design" 确...
```

**graph_sft** ✅ (精确匹配, 0.3s)
```
<<<{True}>>>
```

#### 样本 2

**预期输出**: `<<<{True}>>>`

**graph_rl** ✅ (精确匹配, 9.6s)
```
首先，我需要理解用户的问题："判断从节点 'create_parser' 到节点 'CodeMethod' 是否存在直接的连接边。"

根据规则，我必须先分析图网络的结构，然后确定问题的类型，最后列出用于回答问题的信息。

图网络的描述是：
- 它是一个有向图（directed: true）。
- 节点有ID、标签、名称和属性。
- 边（edges）是列表，每个边是三元组：起点、关系、终点。

具体来看节点：
- 节点3：id=3，名称是"ontology_client.config.OntologyConfig.from_env"，标签是["Entity"]
- 节点2：id=2，名称是"CodeMethod"，标签是["EntityType"]
- 节点4：id=4，名称是"create_parser"，标签是["Entity"]

边（edges）列表：
- 边是列表形式，例如：["AddToQueue", "IS_A", "CodeMethod"]
- 每个边表示一个有向关系：起点 -> 关系 -> 终点

我需要检查是否存在从节点 'create_parser' 到节点 'C...
```

**graph_sft** ✅ (精确匹配, 0.4s)
```
<<<{True}>>>
```

#### 样本 3

**预期输出**: `<<<{True}>>>`

**graph_rl** ✅ (精确匹配, 16.6s)
```
首先，我需要理解用户的问题："判断从节点 'Plan' 到节点 'CodeMethod' 是否存在直接的连接边。"

根据规则，我必须先分析图网络的结构，然后确定问题的类型，最后列出用于回答问题的信息。

图网络的描述是：
- 它是有向图（directed: true）
- 节点有ID、标签、名称和属性
- 边（edges）是列表，每个边是三元组：[起点, 关系, 终点]

具体来看节点：
- 节点 "Plan" 的ID是30（从列表中：{"id": 30, "labels": ["Entity"], "name": "Plan", ...}）
- 节点 "CodeMethod" 的ID是2（从列表中：{"id": 2, "labels": ["EntityType"], "name": "CodeMethod", ...}）

边（edges）列表：
- 每个边是 [起点, 关系, 终点]
- 例如：["Deconstruct", "IS_A", "CodeMethod"] 表示从节点 "Deconstruct" 到节点 "CodeMethod" 有边，关系是 "IS_A"

我需要...
```

**graph_sft** ✅ (精确匹配, 0.3s)
```
<<<{True}>>>
```


### 3.4 MST

#### 样本 1

**预期输出**: `<<<{'mst_edge_count': 8}>>>`

**graph_rl** ✅ (数值匹配, 48.4s)
```
首先，用户的问题是：“使用Prim或Kruskal算法计算该图的最小生成树，假设所有边权重为1。”

我需要理解图网络的结构。根据提供的JSON数据：

- 图是定向的（directed: true）。
- 节点（nodes）有9个节点，每个节点有id、labels、name和properties。
- 边（edges）有10条边，每条边是三元组：起点-关系-终点。

具体节点和边：

节点列表：
- id 1: labels ["Entity"], name "BatchExecution", properties {"name": "BatchExecution"}
- id 2: labels ["EntityType"], name "CodeProcess", properties {"name": "CodeProcess"}
- id 3: labels ["Entity"], name "TwoStageReview", properties {"name": "TwoStageReview"}
- id 4: labels ["Entity"], name "Chec...
```

**graph_sft** ❌ (不匹配, 0.7s)
```
<<<{10}>>>
```

#### 样本 2

**预期输出**: `<<<{'mst_edge_count': 12}>>>`

**graph_rl** ✅ (数值匹配, 34.0s)
```
首先，用户的问题是：“使用Prim或Kruskal算法计算该图的最小生成树，假设所有边权重为1。”

我需要理解图网络的结构。根据提供的JSON数据：

- 图是定向的（directed: true）。
- 节点（nodes）有13个节点，每个节点有id、labels、name和properties。
- 边（edges）有12条边，每条边是三元组：起点、关系、终点。所有边的关系都是"IS_A"。

具体节点列表：
- id 1: name "Config", labels ["Entity"]
- id 2: name "CodeClass", labels ["EntityType"]
- id 3: name "sdd_integration.linker.Link", labels ["Entity"]
- id 4: name "ontology_client.config.OntologyConfig", labels ["Entity"]
- id 5: name "ontology_client.client.BuildResult", labels ["Entity"...
```

**graph_sft** ✅ (数值匹配, 0.2s)
```
<<<{12}>>>
```

#### 样本 3

**预期输出**: `<<<{'mst_edge_count': 34}>>>`

**graph_rl** ✅ (数值匹配, 34.8s)
```
首先，用户的问题是：“使用Prim或Kruskal算法计算该图的最小生成树，假设所有边权重为1。”

我需要理解图网络的结构。根据提供的JSON数据：

- 图是定向的（directed: true）。
- 节点（nodes）有35个，每个节点有id、labels、name和properties。
- 边（edges）有34条，每条边是“起点-关系-终点”的三元组。所有边的关系都是“IS_A”，表示“是...的类型”。

关键点：用户要求使用Prim或Kruskal算法计算最小生成树（MST），但图是定向的（directed graph）。

在图论中，最小生成树（MST）通常用于无向图。对于有向图，我们通常讨论的是有向无环图（DAG）的最小生成树，但标准MST概念是针对无向图的。

回顾规则：规则4提到“返回路径或节点的权重或深度，均为1。阻尼因子等参数使用常见参数如0.85。需要遍历的情况，最大遍历深度限制为3次，最大路径数量限制最多为5条的查询。” 但这里用户的问题是关于MST的计算。

问题在于：图是定向的（directed），而MST算法（Prim和Kruskal）是为无向图...
```

**graph_sft** ✅ (数值匹配, 1.4s)
```
<<<{34}>>>
```


### 3.5 NEIGHBOR

#### 样本 1

**预期输出**: `<<<{'CodeClass'}>>>`

**graph_rl** ✅ (精确匹配, 21.4s)
```
首先，用户的问题是：“找出节点 'PythonParser' 的所有邻居节点（前驱节点和后继节点）。”

我需要理解图网络的结构。图网络是直接的（directed: true），所以有方向。节点有ID、标签、名称和属性。边是关系。

从图网络描述中：

- 节点列表：有13个节点，每个节点有id、labels、name和properties。

- 边列表：有12条边，每条边是[起点, 关系, 终点]。

具体边：

- ["Config", "IS_A", "CodeClass"]

- ["sdd_integration.linker.Link", "IS_A", "CodeClass"]

- ["ontology_client.config.OntologyConfig", "IS_A", "CodeClass"]

- ["ontology_client.client.BuildResult", "IS_A", "CodeClass"]

- ["PythonParser", "IS_A", "CodeClass"]  // 这里PythonParser是起点

- ["Pa...
```

**graph_sft** ✅ (精确匹配, 0.2s)
```
<<<{'CodeClass'}>>>
```

#### 样本 2

**预期输出**: `<<<{'文档架构代理'}>>>`

**graph_rl** ✅ (精确匹配, 25.8s)
```
首先，我需要理解用户的问题："找出节点 'global/CLAUDE.md' 的所有邻居节点（前驱节点和后继节点）。"

根据规则，这个图网络是直接的（directed: true），所以邻居节点包括前驱（in-neighbors）和后继（out-neighbors）。

回顾图网络的定义：
- 节点有id、labels、name和properties。
- 边（edges）是列表，每个边是三元组：[起点, 关系, 终点]

用户指定了节点名称：'global/CLAUDE.md'。我需要找到这个节点的所有邻居节点。

在图网络中，节点的名称是给定的。从图数据中，我看到：
- 节点20的name是"global/CLAUDE.md"，id是20。

所以，节点'global/CLAUDE.md'对应图中的节点id=20。

现在，我需要找到这个节点的所有邻居节点。由于图是直接的（directed），邻居包括：
- 前驱节点（in-neighbors）：那些有边指向这个节点的节点（即，边的终点是这个节点）。
- 后继节点（out-neighbors）：那些从这个节点有边出发的节点（即，边...
```

**graph_sft** ✅ (精确匹配, 0.3s)
```
<<<{'文档架构代理'}>>>
```

#### 样本 3

**预期输出**: `<<<{'CodeMethod'}>>>`

**graph_rl** ✅ (精确匹配, 25.9s)
```
首先，我需要理解用户的问题："找出节点 'OutputR' 的所有邻居节点（前驱节点和后继节点）。"

根据规则，这是一个关于图网络的查询。图网络是给定的JSON结构，我需要分析节点 'OutputR' 的邻居节点。

关键点是：图是定向的（directed: true），所以邻居节点包括前驱（in-neighbors）和后继（out-neighbors）。

在图中，节点的邻居取决于边的关系：
- 对于有向图，前驱节点（in-neighbors）是那些有边指向该节点的节点。
- 后继节点（out-neighbors）是那些有边从该节点指向的节点。

用户指定了“前驱节点和后继节点”，所以我需要找到：
- 所有指向 'OutputR' 的节点（前驱）
- 所有从 'OutputR' 指向的节点（后继）

现在，查看图网络的定义：
- 节点列表：有35个节点，每个节点有id、labels、name和properties。
- 边列表：有35条边，每条边是[起点, 关系, 终点]。

具体到节点 'OutputR'：
- 在节点列表中，id 33 的节点是：{"id": 33, "labe...
```

**graph_sft** ✅ (精确匹配, 0.3s)
```
<<<{'CodeMethod'}>>>
```


### 3.6 PREDECESSOR

#### 样本 1

**预期输出**: `<<<set()>>>`

**graph_rl** ✅ (空集匹配, 20.3s)
```
首先，我需要理解这个图网络的结构。图网络是定向的（directed: true），有35个节点和35条边。

节点信息：
- 每个节点有id、labels、name和properties。
- 节点的name是关键，因为问题中提到了节点 'imports'。

问题：找出节点 'imports' 的所有前驱节点。

在图网络中，前驱节点（predecessors）指的是在有向图中，指向当前节点的节点。也就是说，对于节点 'imports'，它的前驱节点是那些有边指向 'imports' 的节点。

回顾图网络的定义：
- 边是列表形式，例如：["BLOCK", "IS_A", "CodeEnum"] 表示从节点 "BLOCK" 到节点 "CodeEnum" 的边，关系是 "IS_A"。

在给定的图中，边的列表是：
[
  ["BLOCK", "IS_A", "CodeEnum"],
  ["TriggerType", "IS_A", "CodeEnum"],
  ...,
  ["imports", "IS_A", "CodeEnum"]
]

注意：每个边的格式是 [起点, 关系,...
```

**graph_sft** ❌ (不匹配, 0.4s)
```
<<<{'CodeEnum'}>>>
```

#### 样本 2

**预期输出**: `<<<set()>>>`

**graph_rl** ✅ (空集匹配, 19.2s)
```
首先，我需要理解图网络的结构。根据提供的JSON数据：

- 图是定向的（directed: true）。
- 节点有7个，每个节点有id、labels、name和properties。
- 边（edges）列出了关系：每个边是[起点, 关系, 终点]。

具体节点信息：
- 节点1: id=1, labels=["Entity"], name="BASE_PARSER", properties={"name": "BASE_PARSER"}
- 节点2: id=2, labels=["EntityType"], name="CodeModule", properties={"name": "CodeModule"}
- 节点3: id=3, labels=["Entity"], name="ontologyDevOS", properties={"name": "ontologyDevOS"}
- 节点4: id=4, labels=["Entity"], name="code_processor", properties={"name": "code_processor"}
- 节...
```

**graph_sft** ❌ (不匹配, 0.2s)
```
<<<{'CodeModule'}>>>
```

#### 样本 3

**预期输出**: `<<<set()>>>`

**graph_rl** ✅ (空集匹配, 24.4s)
```
首先，我需要理解图网络的结构。用户提供的图网络信息是JSON格式的，描述了一个有向图。

关键点：
- 图是定向的（directed: true）
- 节点（nodes）有15个，每个节点有id、标签、名称和属性。
- 边（edges）有14条，每条边表示一个关系，格式是["起点", "关系", "终点"]。这里的关系都是"IS_A"，表示"是"或"属于"。

具体节点列表：
- id 1: name = "BackendImplementation", labels = ["Entity"]
- id 2: name = "CodeModule", labels = ["EntityType"]
- id 3: name = "ontologyDevOS", labels = ["Entity"]
- id 4: name = "code_processor", labels = ["Entity"]
- id 5: name = "ontology_client", labels = ["Entity"]
- id 6: name = "plugins.ontology-devos...
```

**graph_sft** ❌ (不匹配, 0.3s)
```
<<<{'code_processor'}>>>
```


### 3.7 SHORTEST_PATH

#### 样本 1

**预期输出**: `<<<set()>>>`

**graph_rl** ✅ (精确匹配, 40.6s)
```
首先，我需要理解这个图网络的结构。用户提供的图网络是一个有向图（directed: true），有35个节点和35条边。节点有ID、标签、名称和属性。边是关系，表示节点之间的连接。

关键点是：用户的问题是“找出从节点 'ModelContextProtocol' 到节点 'MCPtools' 的最短路径上所有的节点，最大深度限制为5。”

根据规则，我需要：
- 理解图网络的节点内涵和关系。
- 分析用户问题的类型。
- 列出用于回答问题的信息。

用户问题类型是：找最短路径上的所有节点。这属于“返回路径”类型，但具体是路径上的节点列表。

规则2说：返回路径时，把每条路径上所有「起点-关系-终点」三元组放入一个frozenset中。但这里用户要的是路径上所有的节点，不是三元组。

再仔细看规则：
- 规则2：返回路径 → 每条路径的三元组集合。
- 但用户问的是“最短路径上所有的节点”，所以可能需要返回路径节点列表。

规则3：返回节点 → 直接使用节点name的字符串，放入set。

用户问题指定了“最短路径上所有的节点”，所以这应该归类为“返回节点”类型，因为最终输出是节点名称...
```

**graph_sft** ❌ (不匹配, 0.3s)
```
<<<{'ModelContextProtocol', 'CodeComponent', 'MCPtools'}>>>
```

#### 样本 2

**预期输出**: `<<<set()>>>`

**graph_rl** ✅ (精确匹配, 26.2s)
```
首先，我需要理解用户的问题："找出从节点 '自治Claude实例' 到节点 'planning-reviewagent' 的最短路径上所有的节点，最大深度限制为5。"

根据规则，我需要分析图网络，然后返回最短路径上的所有节点。规则指定了返回节点的格式：直接使用节点name的字符串，放入一个set中，外部用<<<>>>括起来。

关键点是：
- 起点节点：'自治Claude实例'
- 终点节点：'planning-reviewagent'
- 最大深度限制为5：这意味着路径长度（节点数）不能超过5个节点（包括起点和终点）。

我需要从图网络中找到从'自治Claude实例'到'planning-reviewagent'的最短路径。由于图是带向量的（directed: true），我必须考虑有向边。

先确认图网络的结构：
- 节点列表：有35个节点，每个节点有id、labels、name和properties。
- 边列表：有34条边，每条边是（起点节点名，关系，终点节点名）。关系都是"IS_A"，表示"是"，即这些节点是Design类型实体的实例。

具体地，我需要找到从节点名"自治C...
```

**graph_sft** ❌ (不匹配, 0.5s)
```
<<<{'自治Claude实例', 'Design', 'planning-reviewagent'}>>>
```

#### 样本 3

**预期输出**: `<<<{'CIConfiguration', 'CodeComponent', 'openspec_parser.py'}>>>`

**graph_rl** ❌ (不匹配, 31.7s)
```
首先，我需要理解这个图网络的结构。图网络是直接的（directed: true），有30个节点和30条边。

节点列表：
- 节点1: id=1, labels=["Entity"], name="DetectLang", properties={"name": "DetectLang"}
- 节点2: id=2, labels=["EntityType"], name="CodeComponent", properties={"name": "CodeComponent"}
- 节点3: id=3, labels=["Entity"], name="openspec_parser.py", properties={"name": "openspec_parser.py"}
- 节点4: id=4, labels=["Entity"], name="ttl_generator.py", properties={"name": "ttl_generator.py"}
- ... 依此类推，直到节点30。

边列表：
- 边是关系三元组：["起点", "关系", "终点"]
- 所有边都使...
```

**graph_sft** ✅ (精确匹配, 0.4s)
```
<<<{'CIConfiguration', 'CodeComponent', 'openspec_parser.py'}>>>
```


### 3.8 cycle_detection

#### 样本 1

**预期输出**: `<<<{False}>>>`

**graph_rl** ✅ (精确匹配, 23.0s)
```
首先，用户的问题是：“忽略边的方向，该图中是否存在环或循环路径？”

我需要理解图网络的结构。图是直接的（directed: true），但用户说“忽略边的方向”，所以我要考虑无向图来检查环。

规则中提到：如果用户问题没有说明以下内容，请按照默认保留两位小数。但这里的问题是关于是否存在环，所以可能不需要数值，而是布尔值。

关键点：检查是否存在环（cycle）或循环路径（circular path）。

在图论中，环（cycle）是一个路径，其中起点和终点是同一个节点，并且路径中不重复节点（除了起点和终点）。

由于用户说“忽略边的方向”，我应该将图视为无向图来检查环。

图网络是给定的，有节点和边。边是直接的（directed: true），但用户要求忽略方向，所以我要考虑无向图。

列出所有节点和边：

节点（id 1 到 35）：

- id 1: name: "BEST_PRACTICES.md", labels: ["Entity"]

- id 2: name: "CodeModule", labels: ["EntityType"]

- id 3: name: "on...
```

**graph_sft** ✅ (精确匹配, 0.3s)
```
<<<{False}>>>
```

#### 样本 2

**预期输出**: `<<<{False}>>>`

**graph_rl** ✅ (精确匹配, 22.1s)
```
首先，用户的问题是：“忽略边的方向，该图中是否存在环或循环路径？”

我需要理解图网络的结构。图是无向的吗？问题说“忽略边的方向”，所以我要考虑图是无向的。但给定的图网络是直接的（directed: true），这意味着边是有方向的。不过，用户要求忽略边的方向，所以我应该将图视为无向图来分析环。

规则4提到：需要遍历的情况，最大遍历深度限制为3次，最大路径数量限制最多为5条的查询。但这里的问题是关于是否存在环，所以我不需要遍历路径，而是需要检查图中是否有环。

在图论中，环（cycle）是一个路径，其中起点和终点是同一个节点，并且路径中没有其他重复的节点（除了起点和终点）。

由于用户说“忽略边的方向”，我应该将有向图视为无向图来检查环。因为有向图中环的定义可能不同，但问题指定了“忽略边的方向”，所以我会假设图是无向的。

给定的图网络是directed: true，但边是用列表表示的，例如：["ClaudeCodeOpenSpecWorkflowDesign", "IS_A", "Design"]。这表示从ClaudeCodeOpenSpecWorkflowDesign到Desig...
```

**graph_sft** ✅ (精确匹配, 0.3s)
```
<<<{False}>>>
```

#### 样本 3

**预期输出**: `<<<{True}>>>`

**graph_rl** ✅ (精确匹配, 15.9s)
```
首先，用户的问题是：“忽略边的方向，该图中是否存在环或循环路径？”

我需要理解图网络的结构。图是直接的（directed: true），但用户说“忽略边的方向”，所以我应该考虑无向图来检查环。

图网络描述是：
- 节点：有17个节点，每个节点有id、labels、name和properties。
- 边：有17条边，所有边的关系都是"IS_A"。

关键点：边是直接的（directed: true），但用户要求忽略边的方向。所以，我需要将图视为无向图来检查环。

在图论中，环（cycle）是一个路径，其中起点和终点是同一个节点，并且路径中不重复节点（除了起点和终点）。

由于用户说“忽略边的方向”，我应该检查图中是否存在环，即是否存在一个闭合的路径，其中节点不重复（除了起点）。

现在，查看边的列表：
所有边都是以"IS_A"关系连接的。具体边是：
- ["ClaudeCode主体", "IS_A", "CodeComponent"]
- ["openspec_parser.py", "IS_A", "CodeComponent"]
- ... 一直到 ["CodexSkills"...
```

**graph_sft** ✅ (精确匹配, 0.3s)
```
<<<{True}>>>
```


### 3.9 description

#### 样本 1

**预期输出**: `<<<{"entity_type": "Entity", "entity_name": "rd_ontology", "properties": {"name": "rd_ontology"}, "relation_type_counts": {}, "neighbor_type_counts": {}}>>>`

**graph_rl** ✅ (实体匹配, 22.3s)
```
首先，用户的问题是：“请描述节点'rd_ontology'的详细信息，返回一个JSON对象。”

我需要根据给定的图网络信息来回答这个问题。规则指定了如何返回答案，但问题要求返回一个JSON对象描述节点的详细信息。

回顾规则：

- 规则1：返回属性值、数量、名称、布尔值等，用特定格式。

- 规则2：返回路径，用frozenset。

- 规则3：返回节点，用set。

- 规则4：关于路径或节点的权重、深度等。

但用户的问题是“描述节点'rd_ontology'的详细信息”，这看起来不是直接返回属性值、路径或节点列表。问题指定了“返回一个JSON对象”，所以我需要构造一个JSON对象来描述该节点。

在图网络中，每个节点有属性。从给定的图网络数据中，我可以看到节点信息。

具体看节点'rd_ontology'：

在nodes列表中，id为7的节点是：

{
  "id": 7,
  "labels": ["Entity"],
  "name": "rd_ontology",
  "properties": {
    "name": "rd_ontology"
  }
}

...
```

**graph_sft** ✅ (实体匹配, 1.0s)
```
<<<{'name': 'rd_ontology'}>>>
```

#### 样本 2

**预期输出**: `<<<{"entity_type": "Entity", "entity_name": "language-indicator-extension-mapping", "properties": {"name": "language-indicator-extension-mapping"}, "relation_type_counts": {}, "neighbor_type_counts": ...`

**graph_rl** ✅ (名称匹配, 31.2s)
```
首先，用户的问题是：“请描述节点'language-indicator-extension-mapping'的详细信息，返回一个JSON对象。”

我需要根据给定的图网络信息来回答。图网络的结构是：有节点和边。节点有id、labels、name和properties。

关键点是：用户要描述节点'language-indicator-extension-mapping'的详细信息。所以，我需要找到这个节点在图网络中的具体信息。

查看图网络的定义：

- 节点列表中，id 22 的节点是：{"id": 22, "labels": ["Entity"], "name": "language-indicator-extension-mapping", "properties": {"name": "language-indicator-extension-mapping"}}

所以，这个节点的详细信息包括：

- id: 22

- labels: ["Entity"]

- name: "language-indicator-extension-mapping"

- properti...
```

**graph_sft** ✅ (实体匹配, 3.7s)
```
<<<{'name': 'language-indicator-extension-mapping'}>>>
```

#### 样本 3

**预期输出**: `<<<{"entity_type": "EntityType", "entity_name": "Task", "properties": {"name": "Task"}, "relation_type_counts": {}, "neighbor_type_counts": {}}>>>`

**graph_rl** ✅ (实体匹配, 37.9s)
```
首先，用户的问题是：“请描述节点'Task'的详细信息，返回一个JSON对象。”

我需要根据给定的图网络信息来回答。图网络的结构是：

- 它是有向图（directed: true）。

- 节点（nodes）列表：每个节点有id、labels、name和properties。

- 边（edges）列表：每条边是三元组（起点, 关系, 终点）。

用户指定了节点'Task'，所以我需要找到图中所有与节点'Task'相关的详细信息。

回顾规则：

1. 返回属性值、数量、名称、布尔值的回答：值放在集合中，用<<<>>>括起来。

2. 返回路径：路径用frozenset表示。

3. 返回节点：节点名的集合。

4. 其他：如果问题没说明，路径或节点的权重、深度默认为1，阻尼因子0.85，最大遍历深度3，最大路径数量5。

用户的问题是“描述节点'Task'的详细信息”，这看起来像是要返回节点的属性信息，而不是路径或节点列表。

在图网络中，节点'Task'是存在的。让我检查图网络的节点列表。

从图网络的JSON中：

- 节点列表有多个节点，其中有一个节点的name是"Task...
```

**graph_sft** ✅ (实体匹配, 1.9s)
```
<<<{'name': 'Task', 'outbound': 34, 'inbound': 1, 'properties': {'name': 'Task'}}>>>
```


### 3.10 entity_attribute

#### 样本 1

**预期输出**: `<<<{'ClaudeCodebehaviorrules'}>>>`

**graph_rl** ✅ (精确匹配, 7.4s)
```
首先，用户的问题是：“节点'ClaudeCodebehaviorrules'的'name'属性值是什么？”

我需要理解图网络的结构。根据提供的图网络信息：

- 节点列表中有多个节点，每个节点有id、labels、name和properties。
- 具体到节点'ClaudeCodebehaviorrules'，我需要找到它的属性值。

查看节点列表：

在nodes数组中，有一个节点：
{
  "id": 9,
  "labels": ["Entity"],
  "name": "ClaudeCodebehaviorrules",
  "properties": {
    "name": "ClaudeCodebehaviorrules"
  }
}

这里，节点的name是"ClaudeCodebehaviorrules"，而properties属性中也有一个"name"键，其值是"ClaudeCodebehaviorrules"。

用户问的是“节点'ClaudeCodebehaviorrules'的'name'属性值是什么？”

所以，节点的name属性值就是"Claude...
```

**graph_sft** ✅ (精确匹配, 0.3s)
```
<<<{'ClaudeCodebehaviorrules'}>>>
```

#### 样本 2

**预期输出**: `<<<{'完整开发示例:从概念到实现'}>>>`

**graph_rl** ✅ (精确匹配, 9.5s)
```
首先，用户的问题是：“节点'完整开发示例:从概念到实现'的'name'属性值是什么？”

我需要理解图网络的结构。图网络有节点和边。节点有id、labels、name和properties属性。

从给定的图网络数据中，我可以看到节点列表：

- 节点8的id是8，labels是["Entity"]，name是"完整开发示例:从概念到实现"，properties是{"name": "完整开发示例:从概念到实现"}

具体来说，节点8的properties属性是{"name": "完整开发示例:从概念到实现"}。

用户问的是节点'完整开发示例:从概念到实现'的'name'属性值是什么？

这里有点需要注意：节点的name字段是"完整开发示例:从概念到实现"，而它的properties中也有一个'name'属性，值也是"完整开发示例:从概念到实现"。

在图网络中，每个节点有：
- name：节点的名称（字符串）
- properties：一个字典，包含节点的属性

对于节点8：
- name: "完整开发示例:从概念到实现"
- properties: {"name": "完整开发示例...
```

**graph_sft** ✅ (精确匹配, 0.5s)
```
<<<{'完整开发示例:从概念到实现'}>>>
```

#### 样本 3

**预期输出**: `<<<{'CodeComponent'}>>>`

**graph_rl** ✅ (精确匹配, 10.1s)
```
首先，用户的问题是：“节点'CodeComponent'的'name'属性值是什么？”

我需要理解图网络的结构。图网络是给定的JSON对象，描述了节点和边。

关键点是：用户问的是节点'CodeComponent'的'name'属性值。

在图网络的定义中，节点有属性。具体看节点列表：

- 节点2的id是2，labels是["EntityType"]，name是"CodeComponent"，properties是{"name": "CodeComponent"}。

让我仔细检查：

在"nodes"数组中：

- 第二个节点（id=2）：{"id": 2, "labels": ["EntityType"], "name": "CodeComponent", "properties": {"name": "CodeComponent"}}

所以，这个节点的name属性是"CodeComponent"，而properties中也有"name": "CodeComponent"。

用户问的是节点'CodeComponent'的'name'属性值。这里有点歧义。

节点'CodeC...
```

**graph_sft** ✅ (精确匹配, 0.3s)
```
<<<{'CodeComponent'}>>>
```


### 3.11 entity_relation

#### 样本 1

**预期输出**: `<<<{'IS_A'}>>>`

**graph_rl** ✅ (精确匹配, 15.3s)
```
首先，我需要理解图网络的结构。根据提供的JSON数据：

- 图是定向的（directed: true）。
- 节点列表有9个节点，每个节点有id、labels、name和properties。
- 边（edges）列表描述了节点之间的关系。

关键点是：用户的问题是“节点'四阶段'与节点'CodeProcess'之间存在什么类型的关系？”

我需要找出节点“四阶段”和节点“CodeProcess”之间直接的关系类型。

查看边列表：

- 边是用列表表示的，每个边是三元组：[起点, 关系类型, 终点]

具体边：

1. ["BatchExecution", "IS_A", "CodeProcess"]
2. ["TwoStageReview", "IS_A", "CodeProcess"]
3. ["CheckpointMechanism", "IS_A", "CodeProcess"]
4. ["dev-workflow", "IS_A", "CodeProcess"]
5. ["四阶段", "IS_A", "CodeProcess"]  // 这里有节点“四阶段”和关系“IS_...
```

**graph_sft** ✅ (精确匹配, 0.4s)
```
<<<{'IS_A'}>>>
```

#### 样本 2

**预期输出**: `<<<{'IS_A'}>>>`

**graph_rl** ✅ (精确匹配, 11.0s)
```
首先，我需要理解用户的问题："节点'sdd_integration.openspec_parser.Task'与节点'Task'之间存在什么类型的关系？"

根据规则，我必须先分析图网络的结构，然后确定问题的类型，最后列出用于回答问题的信息。

图网络的描述是：
- 它是一个有向图（directed: true）。
- 节点列表（nodes）有17个节点，每个节点有id、labels、name和properties。
- 边（edges）列表有17条边，每条边是三元组：起点、关系、终点。

关键点是：用户问的是节点'sdd_integration.openspec_parser.Task'和节点'Task'之间存在什么类型的关系。

我需要查看图网络中这些节点之间的关系。

从edges列表中，我可以看到：
- 边是：["ANALYZE", "IS_A", "Task"]
- ["sdd_integration.openspec_parser.Task", "IS_A", "Task"]
- 等等

具体地，有一条边是：["sdd_integration.openspec_parser...
```

**graph_sft** ✅ (精确匹配, 0.5s)
```
<<<{'IS_A'}>>>
```

#### 样本 3

**预期输出**: `<<<{'IS_A'}>>>`

**graph_rl** ✅ (精确匹配, 9.7s)
```
首先，我需要理解用户的问题："节点'generate_stable_id'与节点'CodeMethod'之间存在什么类型的关系？"

根据提供的图网络信息，图网络是直接的（directed: true），有节点和边。边的类型是"IS_A"，这表示一种关系类型。

让我检查图网络的边列表。边是用列表表示的，每个边是一个三元组：[起点, 关系, 终点]。

在edges列表中，我看到：
- ["generate_stable_id", "IS_A", "CodeMethod"]

具体来说，edges列表中有一条边：["generate_stable_id", "IS_A", "CodeMethod"]

这表示节点"generate_stable_id"和节点"CodeMethod"之间存在"IS_A"类型的关系。

用户问的是"节点'generate_stable_id'与节点'CodeMethod'之间存在什么类型的关系？"，所以答案应该是"IS_A"。

现在，我需要根据规则来返回答案。

规则1：返回属性值、数量、名称、布尔值的回答。将回答的值放在一个集合中，外部用<<<>>>括...
```

**graph_sft** ✅ (精确匹配, 1.0s)
```
<<<{'IS_A'}>>>
```


### 3.12 entity_type

#### 样本 1

**预期输出**: `<<<{'Entity'}>>>`

**graph_rl** ✅ (精确匹配, 9.7s)
```
首先，我需要理解用户的问题："节点'ontology_client.config.OntologyConfig.from_env'的类型是什么？"

根据规则，我必须先分析图网络的各个节点的内涵和关系。图网络的描述是：

- 它是一个有向图（directed: true）。
- 节点有id、labels、name和properties。
- 边（edges）表示节点之间的关系。

关键点是：用户问的是节点'ontology_client.config.OntologyConfig.from_env'的类型。

在图网络中，每个节点都有一个"labels"属性，这表示该节点的类型或类别。例如，节点的labels列表指定了它的类型。

查看图网络的节点列表：

- 节点3：{"id": 3, "labels": ["Entity"], "name": "ontology_client.config.OntologyConfig.from_env", "properties": {"name": "ontology_client.config.OntologyConfig.from_env"...
```

**graph_sft** ✅ (精确匹配, 0.3s)
```
<<<{'Entity'}>>>
```

#### 样本 2

**预期输出**: `<<<{'Entity'}>>>`

**graph_rl** ✅ (精确匹配, 11.3s)
```
首先，我需要理解用户的问题："节点'CG'的类型是什么？"

根据规则，我必须先分析图网络的结构，然后确定问题的类型，最后列出用于回答问题的信息。

图网络的描述是：
- 它是一个有向图（directed: true）
- 节点有ID、标签（labels）、名称（name）和属性（properties）
- 边（edges）表示节点之间的关系

关键点是：用户问的是节点'CG'的类型是什么？

在图网络中，每个节点都有标签（labels）和属性（properties）。问题问的是"类型"，这可能指的是节点的标签（labels）或属性中的某个值。

回顾图网络的定义：
- 节点有"labels"字段，例如：["Entity"] 或 ["EntityType"]
- 节点有"properties"字段，例如：{"name": "CG"}

具体到节点'CG'：
- 在图网络中，节点ID 14的名称是"CG"，其属性是：{"name": "CG"}
- 节点ID 14的标签是：["Entity"]

所以，节点'CG'的标签是["Entity"]。但问题问的是"类型"，在上下文中，可能指的是...
```

**graph_sft** ✅ (精确匹配, 0.3s)
```
<<<{'Entity'}>>>
```

#### 样本 3

**预期输出**: `<<<{'Entity'}>>>`

**graph_rl** ✅ (精确匹配, 10.4s)
```
首先，我需要理解用户的问题："节点'FaultTolerance'的类型是什么？"

根据规则，我必须先分析图网络的结构，然后确定问题的类型，最后列出用于回答问题的信息。

回顾图网络的描述：
- 这是一个有向图（directed: true）。
- 节点（nodes）有ID、标签（labels）、名称（name）和属性（properties）。
- 边（edges）表示节点之间的关系。

关键点是：用户问的是节点'FaultTolerance'的类型。

在图网络中，每个节点都有一个"labels"属性，这表示该节点的类型或类别。例如，节点的定义中：
- 每个节点有"labels"字段，如["Entity"]，表示该节点的标签。
- 问题问的是"类型"，可能指的是节点的标签。

查看节点列表：
- 节点ID 14：{"id": 14, "labels": ["Entity"], "name": "FaultTolerance", "properties": {"name": "FaultTolerance"}}

这里，节点'FaultTolerance'的标签是["Entity"]...
```

**graph_sft** ✅ (精确匹配, 0.3s)
```
<<<{'Entity'}>>>
```


### 3.13 page_rank_v2

#### 样本 1

**预期输出**: `<<<{'API文档': 0.15}>>>`

**graph_rl** ✅ (包含目标节点, 113.6s)
```
首先，我需要理解用户的问题：使用PageRank算法（阻尼因子0.85，迭代3次）计算图中各节点的重要性得分，返回得分最高的前3个节点。

根据规则，我需要：
- 使用PageRank算法
- 阻尼因子设为0.85（默认）
- 迭代3次（最大遍历深度限制为3次）
- 返回得分最高的前3个节点

PageRank算法是用于计算图中节点重要性的算法，它基于节点的链接关系。在PageRank中，每个节点的得分取决于它被其他节点链接的次数和链接到的节点的得分。

关键点：
- 图是直接的（directed: true）
- 节点有ID、标签、名称和属性
- 边有关系类型（如IS_A, GENERATES, CONTAINS等）

我需要为每个节点计算PageRank得分。PageRank的计算公式是：
\[ PR(p) = (1 - d) + d \times \sum_{q \in \text{backlinks}} \frac{PR(q)}{L(q)} \]
其中：
- \( d \) 是阻尼因子（这里设为0.85）
- \( L(q) \) 是节点q的出度（即q指向的边的数量）
- 求和...
```

**graph_sft** ❌ (不匹配, 0.6s)
```
<<<{'文档架构代理', 'Claude', 'Superpowers'}>>>
```

#### 样本 2

**预期输出**: `<<<{'Active': 0.15}>>>`

**graph_rl** ✅ (包含目标节点, 49.9s)
```
首先，用户的问题是：使用PageRank算法（阻尼因子0.85，迭代3次）计算图中各节点的重要性得分，返回得分最高的前3个节点。

我需要根据规则来回答。规则说：

- 返回属性值、数量、名称、布尔值的回答：用集合形式，如<<<{'张三'}>>>

- 返回路径：用frozenset的集合

- 返回节点：用节点name的字符串集合

- 对于PageRank问题，需要计算节点的重要性得分，返回得分最高的前3个节点。

问题指定了PageRank算法，阻尼因子0.85，迭代3次。规则还提到：需要遍历的情况，最大遍历深度限制为3次，最大路径数量限制最多为5条的查询。但这里不是返回路径，而是返回节点的重要性得分。

关键点是：我需要计算PageRank得分，然后返回得分最高的前3个节点。

但图网络的描述中，没有直接给出边的关系。图网络是给定的JSON格式。

让我仔细看图网络的描述：

- 它是一个有向图（directed: true）

- 节点有35个，每个节点有id、labels、name和properties

- 边（edges）是列表，每个边是三元组：[起点, 关系, 终点]...
```

**graph_sft** ❌ (不匹配, 0.6s)
```
<<<{'CodeField', 'field', 'res.locals.claims'}>>>
```

#### 样本 3

**预期输出**: `<<<{'CheckDir': 0.15}>>>`

**graph_rl** ✅ (包含目标节点, 39.3s)
```
首先，用户的问题是：使用PageRank算法（阻尼因子0.85，迭代3次）计算图中各节点的重要性得分，返回得分最高的前3个节点。

我需要根据规则来回答。规则说：

- 返回属性值、数量、名称、布尔值的回答：将值放在集合中，用<<<>>>括起来。

- 返回路径：用frozenset表示路径。

- 返回节点：直接用节点name的字符串，放入set中。

- 对于PageRank问题，需要计算节点的重要性得分，返回得分最高的前3个节点。

问题指定了PageRank算法，阻尼因子0.85，迭代3次。所以，我需要模拟PageRank计算。

图网络的描述是：

- directed: true（有向图）

- nodes: 23个节点，每个节点有id、labels、name和properties

- edges: 22条边，所有边都是"IS_A"关系，从各种节点指向"CodeMethod"节点。

具体看edges列表：

edges是：[["CheckDir", "IS_A", "CodeMethod"], ... , ["Context", "IS_A", "CodeMethod"...
```

**graph_sft** ❌ (不匹配, 0.5s)
```
<<<{'CodeMethod', 'add_element', 'add_relation'}>>>
```


### 3.14 relation_between

#### 样本 1

**预期输出**: `<<<{'IS_A'}>>>`

**graph_rl** ✅ (精确匹配, 9.9s)
```
首先，我需要理解用户的问题："节点'CodexSkills'和节点'CodeComponent'之间的关系类型是什么？"

根据规则，我必须先分析图网络的结构，然后确定问题的类型，最后列出用于回答问题的信息。

回顾图网络的描述：
- 这是一个有向图（directed: true）。
- 节点有ID、标签、名称和属性。
- 边（edges）表示节点之间的关系。

关键点是：用户问的是节点'CodexSkills'和节点'CodeComponent'之间的关系类型。

我需要查看图网络中是否有直接连接这两个节点的边。

从图网络的edges列表中，我可以看到所有边的定义。edges是一个列表，每个元素是三元组：[起点, 关系类型, 终点]。

具体地，edges列表中有一条边是：["CodexSkills", "IS_A", "CodeComponent"]

让我检查一下：
- edges列表中有一条：["CodexSkills", "IS_A", "CodeComponent"]

是的，这里明确显示：CodexSkills 通过关系 "IS_A" 连接到 CodeComponent...
```

**graph_sft** ✅ (精确匹配, 0.2s)
```
<<<{'IS_A'}>>>
```

#### 样本 2

**预期输出**: `<<<{'IS_A'}>>>`

**graph_rl** ✅ (精确匹配, 12.5s)
```
首先，我需要理解用户的问题："节点'name'和节点'CodeField'之间的关系类型是什么？"

根据提供的图网络信息，图网络是直接的（directed: true），有节点和边。节点有ID、标签、名称和属性。边表示节点之间的关系。

关键点是：用户问的是节点'name'和节点'CodeField'之间的关系类型。

我需要查看图网络中是否有直接连接这两个节点的边。

从图网络的edges列表中，我可以看到所有边的定义。edges是一个列表，每个元素是三元组：[起点, 关系类型, 终点]。

具体地，edges列表是：

[
  ["CLAUDE_PROJECT_DIR", "IS_A", "CodeField"],
  ["hooks", "IS_A", "CodeField"],
  ...,
  ["name", "IS_A", "CodeField"],
  ...
]

在edges列表中，有一个条目是：["name", "IS_A", "CodeField"]

这表示节点"name"（ID 8）和节点"CodeField"（ID 2）之间有一个关系类型为"IS_A"。...
```

**graph_sft** ✅ (精确匹配, 0.3s)
```
<<<{'IS_A'}>>>
```

#### 样本 3

**预期输出**: `<<<{'IS_A'}>>>`

**graph_rl** ✅ (精确匹配, 13.5s)
```
首先，我需要理解用户的问题："节点'提交消息'和节点'Requirement'之间的关系类型是什么？"

根据提供的图网络信息，图网络是直接的（directed: true），有节点和边。节点有ID、标签、名称和属性。边表示节点之间的关系。

关键点是：用户问的是节点"提交消息"和节点"Requirement"之间的关系类型。

在图网络中，边描述了节点之间的关系。每条边有三个部分：起点、关系类型、终点。

我需要找到所有连接"提交消息"和"Requirement"的边。

先查看节点列表：

- 节点"提交消息"的ID是26（从列表中：{"id": 26, "labels": ["Entity"], "name": "提交消息", ...}）

- 节点"Requirement"的ID是2（从列表中：{"id": 2, "labels": ["EntityType"], "name": "Requirement", ...}）

在边列表中，每条边是["起点", "关系类型", "终点"]。

边列表是：

[

["500linerule", "IS_A", "Requiremen...
```

**graph_sft** ✅ (精确匹配, 0.3s)
```
<<<{'IS_A'}>>>
```


### 3.15 relation_path

#### 样本 1

**预期输出**: `<<<{frozenset([('分析维度', 'IS_A', 'CodeField')])}>>>`

**graph_rl** ✅ (集合匹配, 25.7s)
```
首先，我需要理解用户的问题："找出从节点'分析维度'到节点'CodeField'的关系路径。"

根据规则，我需要分析图网络的结构，然后确定从节点"分析维度"到节点"CodeField"的关系路径。

回顾图网络的描述：
- 图是定向的（directed: true）。
- 节点列表：有35个节点，每个节点有id、labels、name和properties。
- 边（edges）：有35条边，每条边表示一个关系。所有边都使用关系类型"IS_A"。

关键点是：所有边都以"IS_A"关系连接节点。具体来说，每条边的格式是["source_node_name", "IS_A", "target_node_name"]。

例如：
- ["CLAUDE_PROJECT_DIR", "IS_A", "CodeField"]
- ["hooks", "IS_A", "CodeField"]
- ... 依此类推

现在，用户要找的是从节点"分析维度"到节点"CodeField"的关系路径。

首先，我需要确认图中是否有节点叫"分析维度"和"CodeField"。

从节点列表中：
- 节点12...
```

**graph_sft** ✅ (集合匹配, 0.6s)
```
<<<{('分析维度', 'IS_A', 'CodeField')}>>>
```

#### 样本 2

**预期输出**: `<<<{frozenset([('制定计划', 'IS_A', 'Requirement')])}>>>`

**graph_rl** ✅ (路径匹配, 31.6s)
```
首先，我需要理解用户的问题："找出从节点'制定计划'到节点'Requirement'的关系路径。"

根据规则，我需要分析图网络的结构，然后确定从节点"制定计划"到节点"Requirement"的关系路径。

回顾图网络的描述：
- 节点有id、labels、name和properties。
- 边（edges）是关系列表，格式为["起点", "关系", "终点"]。

从图网络数据中：
- 节点列表：每个节点有name属性。例如，节点25的name是"制定计划"，节点2的name是"Requirement"。
- 边列表：每个边是三元组（起点，关系，终点）。关系类型都是"IS_A"。

具体看：
- 节点"制定计划"对应的是id=24的节点，因为节点24的name是"制定计划"。
- 节点"Requirement"对应的是id=2的节点，因为节点2的name是"Requirement"。

在边列表中，有从"制定计划"到"Requirement"的路径吗？

检查边列表：
边列表是：[["500linerule", "IS_A", "Requirement"], ["sdd_inte...
```

**graph_sft** ✅ (集合匹配, 0.4s)
```
<<<{'制定计划', 'IS_A', 'Requirement'}>>>
```

#### 样本 3

**预期输出**: `<<<{frozenset([('Requirement', 'IS_A', 'Requirement')])}>>>`

**graph_rl** ✅ (精确匹配, 35.0s)
```
首先，我需要理解用户的问题："找出从节点'Requirement'到节点'Requirement'的关系路径。"

用户要求找出从节点'Requirement'到节点'Requirement'的关系路径。这意味着起点和终点都是同一个节点：'Requirement'。

现在，回顾图网络的结构。图网络是直接的（directed: true），有节点和边。

从提供的图网络数据中，我看到节点列表和边列表。

节点列表中，有多个节点，其中有一个节点的name是"Requirement"。具体看：

- 节点2：id=2, labels=["EntityType"], name="Requirement", properties={"name": "Requirement"}

其他节点的name都不同，比如"CSS/styleconflictsandrenderingissues"等。

边列表中，有边连接到"Requirement"。例如：

- ["CSS/styleconflictsandrenderingissues", "IS_A", "Requirement"]：这表示从节点"C...
```

**graph_sft** ❌ (不匹配 - 缺少完整三元组, 1.6s)
```
<<<{'IS_A'}>>>
```


### 3.16 summary

#### 样本 1

**预期输出**: `<<<{"node_count": 24, "edge_count": 24, "node_type_counts": {"Entity": 23, "EntityType": 1}, "relation_type_counts": {"IS_A": 24}}>>>`

**graph_rl** ✅ (数值匹配, 25.1s)
```
首先，用户的问题是：“请统计该图的基本信息，返回node_count、edge_count、node_type_counts、relation_type_counts。”

我需要根据给定的图网络信息来回答。图网络的描述是：

- "directed": true
- "nodes": 有24个节点（从id 1到id 24）
- "edges": 有24条边（列表中有24个边）
- "metadata": {"num_nodes": 24, "num_edges": 24}

规则要求返回特定的信息：node_count、edge_count、node_type_counts、relation_type_counts。

让我分析每个部分：

1. **node_count**：节点的总数。从metadata中，num_nodes是24。所以node_count应该是24。

2. **edge_count**：边的总数。从metadata中，num_edges是24。所以edge_count应该是24。

3. **node_type_counts**：节点类型的计数。节点有labe...
```

**graph_sft** ✅ (数值匹配, 1.1s)
```
<<<{'node_count': 24, 'edge_count': 24, 'node_type_counts': {'Entity': 20, 'EntityType': 1}, 'relation_type_counts': {'IS_A': 24}}>>>
```

#### 样本 2

**预期输出**: `<<<{"node_count": 30, "edge_count": 30, "node_type_counts": {"Entity": 29, "EntityType": 1}, "relation_type_counts": {"IS_A": 30}}>>>`

**graph_rl** ✅ (数值匹配, 27.2s)
```
首先，用户的问题是：“请统计该图的基本信息，返回node_count、edge_count、node_type_counts、relation_type_counts。”

我需要根据给定的图网络信息来回答这个问题。图网络的描述是JSON格式的，我需要从中提取相关信息。

回顾图网络的JSON结构：

- "directed": true（表示有向图）

- "nodes": 一个节点列表，每个节点有id、labels、name、properties等属性

- "edges": 一个边列表，每个边是三元组 [起点, 关系, 终点]

- "metadata": 包含 "num_nodes" 和 "num_edges"，但用户要求的是统计基本信息，所以我应该使用这个metadata，或者从节点和边列表中计算。

用户指定了要返回：node_count、edge_count、node_type_counts、relation_type_counts。

从规则中，我需要返回属性值、数量、名称、布尔值等，具体到这个查询。

先看metadata部分：在JSON中，有"metadata": ...
```

**graph_sft** ✅ (数值匹配, 0.7s)
```
<<<{'node_count': 30, 'edge_count': 30, 'node_type_counts': {'Entity': 23, 'EntityType': 1, 'Entity': 6}, 'relation_type_counts': {'IS_A': 30}}>>>
```

#### 样本 3

**预期输出**: `<<<{"node_count": 15, "edge_count": 14, "node_type_counts": {"Entity": 14, "EntityType": 1}, "relation_type_counts": {"IS_A": 14}}>>>`

**graph_rl** ✅ (数值匹配, 30.4s)
```
首先，用户的问题是：“请统计该图的基本信息，返回node_count、edge_count、node_type_counts、relation_type_counts。”

我需要根据给定的图网络信息来回答。图网络的描述是：

- "directed": true
- "nodes": 有15个节点（从id 1到id 15）
- "edges": 有14条边（列表中有14个边）
- "metadata": {"num_nodes": 15, "num_edges": 14}

规则要求返回特定的信息：node_count、edge_count、node_type_counts、relation_type_counts。

让我解析这些：

1. **node_count**：节点的总数。从metadata中，num_nodes是15。所以node_count应该是15。

2. **edge_count**：边的总数。从metadata中，num_edges是14。所以edge_count应该是14。

3. **node_type_counts**：节点类型的计数。节点有labels...
```

**graph_sft** ✅ (数值匹配, 0.6s)
```
<<<{'node_count': 15, 'edge_count': 14, 'node_type_counts': {'Entity': 10, 'EntityType': 1}, 'relation_type_counts': {'IS_A': 14}}>>>
```


### 3.17 tree_check

#### 样本 1

**预期输出**: `<<<{False}>>>`

**graph_rl** ✅ (精确匹配, 22.5s)
```
首先，用户的问题是：“忽略边的方向，判断该图是否是一棵树（连通且无环的图）。”

我需要理解图网络的结构。给定的图是：

- 它是有向图（directed: true）

- 节点：有35个节点，每个节点有id、labels、name和properties

- 边：有35条边，每条边都是“IS_A”关系，连接到“CodeMethod”节点

具体来说，边的列表是：

- 每条边的格式是：[起点, "IS_A", 终点]

例如：["BackwardTracing", "IS_A", "CodeMethod"]

所有边都以“IS_A”关系连接到“CodeMethod”节点。实际上，从列表看，几乎每个节点都通过“IS_A”关系连接到“CodeMethod”节点。

让我仔细看边的列表：

edges: [
  ["BackwardTracing", "IS_A", "CodeMethod"],
  ["ontology_client.config.OntologyConfig.from_env", "IS_A", "CodeMethod"],
  ... 一直到 ["get_langu...
```

**graph_sft** ❌ (不匹配, 0.3s)
```
<<<{True}>>>
```

#### 样本 2

**预期输出**: `<<<{True}>>>`

**graph_rl** ✅ (精确匹配, 19.1s)
```
首先，用户的问题是：“忽略边的方向，判断该图是否是一棵树（连通且无环的图）。”

我需要理解图网络的结构。图网络是给定的JSON对象，其中包含节点和边的信息。

关键点是：忽略边的方向。图是定向的（directed: true），但用户说“忽略边的方向”，所以我应该考虑图作为无向图来分析。

问题是要判断这个图是否是一棵树。树的定义是：连通的、无环的、且有n-1条边（其中n是节点数）。

从图网络的元数据中，我可以看到：
- num_nodes: 18
- num_edges: 17

如果图是树，它应该有n-1条边。这里n=18，所以树应该有17条边。正好，num_edges是17。

但树还必须是连通的，且无环。

用户说“忽略边的方向”，所以我要检查无向图是否连通且无环。

首先，确认图的结构。

节点列表：
- 节点有18个（id从1到18）
- 边有17条，每条边都是“IS_A”关系，连接一个节点到另一个节点。

在图中，所有边都是“IS_A”关系，连接一个实体到“CodeFile”类型。但用户说忽略边的方向，所以我不应该考虑方向。

在给定的图中，边是列表形式：例如，["A...
```

**graph_sft** ✅ (精确匹配, 0.3s)
```
<<<{True}>>>
```

#### 样本 3

**预期输出**: `<<<{False}>>>`

**graph_rl** ✅ (精确匹配, 15.6s)
```
首先，用户的问题是：“忽略边的方向，判断该图是否是一棵树（连通且无环的图）。”

我需要理解图网络的结构。图是给定的JSON：

- 它是有向图（directed: true）
- 节点：有19个节点，每个节点有id、labels、name和properties
- 边：有19条边，每条边是三元组（起点，关系，终点）

关键点是：用户说“忽略边的方向”，所以我要考虑无向图来判断是否是树。

树的定义：一个连通的无环图，且有n个节点的树有n-1条边。

这里，图有19个节点（num_nodes: 19）。

边的数量：num_edges: 19。

在无向图中，树应该有n-1条边。这里n=19，所以树应该有18条边。

但图有19条边，这比18多，所以它不可能是树，因为树必须有恰好n-1条边。

另外，树必须是连通的。我需要检查图是否连通。

用户说“忽略边的方向”，所以我应该将图视为无向图来分析。

首先，计算边的数量：19条边。

节点数：19个。

对于无向图，树的条件是：
1. 连通
2. 无环
3. 边数 = 节点数 - 1

这里，边数 = 19，节点数 = 19，所以边数 ...
```

**graph_sft** ❌ (不匹配, 0.3s)
```
<<<{True}>>>
```


### 3.18 tree_lca

#### 样本 1

**预期输出**: `<<<{'DevelopmentWorkflow'}>>>`

**graph_rl** ❌ (不匹配, 63.5s)
```
首先，我需要理解这个图网络的结构。用户给的图网络是JSON格式的，我来解析一下。

图网络信息：
- 是有向图（directed: true）
- 节点列表（nodes）：
  - id 1: 标签 ["Entity"]，名称 "CheckpointMechanism"，属性 {"name": "CheckpointMechanism"}
  - id 2: 标签 ["EntityType"]，名称 "CodeProcess"，属性 {"name": "CodeProcess"}
  - id 3: 标签 ["Entity"]，名称 "TwoStageReview"，属性 {"name": "TwoStageReview"}
  - id 4: 标签 ["Entity"]，名称 "BatchExecution"，属性 {"name": "BatchExecution"}
  - id 5: 标签 ["Entity"]，名称 "dev-workflow"，属性 {"name": "dev-workflow"}
  - id 6: 标签 ["Entity"]，名称 "四阶段"，属性 {"n...
```

**graph_sft** ✅ (精确匹配, 0.7s)
```
<<<{'DevelopmentWorkflow'}>>>
```

#### 样本 2

**预期输出**: `<<<{'CodeComponent'}>>>`

**graph_rl** ✅ (精确匹配, 47.0s)
```
首先，我需要理解这个图网络的结构。图网络是直接的（directed: true），有19个节点和19条边。

节点列表：
- 节点1: id=1, labels=["Entity"], name="CLI分析", properties={"name": "CLI分析"}
- 节点2: id=2, labels=["EntityType"], name="CodeComponent", properties={"name": "CodeComponent"}
- 节点3: id=3, labels=["Entity"], name="openspec_parser.py", properties={"name": "openspec_parser.py"}
- 节点4: id=4, labels=["Entity"], name="ttl_generator.py", properties={"name": "ttl_generator.py"}
- 节点5: id=5, labels=["Entity"], name="base_parser.py", properties={"nam...
```

**graph_sft** ✅ (精确匹配, 0.2s)
```
<<<{'CodeComponent'}>>>
```

#### 样本 3

**预期输出**: `<<<{'Deconstruct'}>>>`

**graph_rl** ❌ (不匹配, 41.8s)
```
首先，我需要理解这个图网络的结构。图网络是直接的（directed: true），有35个节点和35条边。所有边都使用关系 "IS_A"，表示 "是...的"，意思是这些节点都是 "CodeMethod" 的子类或实例。

关键点是：所有边都连接到 "CodeMethod"。具体来说，每个节点通过 "IS_A" 关系指向 "CodeMethod"。例如：
- "Deconstruct" 是 "CodeMethod" 的一个实例
- "ontology_client.config.OntologyConfig.from_env" 是 "CodeMethod" 的一个实例
- 依此类推，直到 "get_file_extensions" 也是 "CodeMethod" 的一个实例

实际上，从边的列表看，每个节点都有一条边指向 "CodeMethod"，关系是 "IS_A"。但注意，边的表示是 ["source", "relation", "target"]，所以这里所有边都是从某个节点到 "CodeMethod"。

例如：["Deconstruct", "IS_A", "CodeMeth...
```

**graph_sft** ❌ (不匹配, 0.3s)
```
<<<{'CodeMethod'}>>>
```


## 4. 评测结论

- **最高准确率**: graph_rl (88.9%)
- **最快响应**: graph_sft (平均 0.59s)

### 各模型优势任务类型

- **graph_rl**: NEIGHBOR(100%), PREDECESSOR(100%), EDGE(100%), cycle_detection(100%), description(100%), entity_attribute(100%), entity_relation(100%), entity_type(100%), relation_between(100%), relation_path(100%), summary(100%), tree_check(100%), MST(100%), page_rank_v2(100%), COMMON_NEIGHBOR(100%)
- **graph_sft**: NEIGHBOR(100%), EDGE(100%), cycle_detection(100%), description(100%), entity_attribute(100%), entity_relation(100%), entity_type(100%), relation_between(100%), relation_path(100%), summary(100%), COMMON_NEIGHBOR(100%)