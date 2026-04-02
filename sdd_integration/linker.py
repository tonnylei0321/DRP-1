# -*- coding: utf-8 -*-
"""
Code-Requirement Linker

链接代码元素与需求，支持多种链接机制：
- 显式注解 (@spec)
- 文件路径匹配
- Git 提交信息解析
- 语义匹配 (基于 Embedding 的相似度计算)

注意：TTL 生成已移至 ontology 项目的 CodeOntologyBuilder。
使用 ontology_client.OntologyClient.build_sdd_ontology() 构建 SDD 本体。
"""

import re
import hashlib
import os
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
import logging
import subprocess

from code_processor.base_parser import CodeElement, ElementType

logger = logging.getLogger(__name__)

# 尝试导入 numpy，用于向量计算
try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False
    np = None


@dataclass
class Link:
    """代码与需求之间的链接"""
    source_type: str  # 'code', 'test'
    source_id: str  # 完整名称或路径
    target_type: str  # 'requirement', 'design', 'task', 'code'
    target_id: str  # Change ID 或 element_id
    confidence: float  # 0.0 - 1.0
    method: str  # 'annotation', 'file_path', 'git_commit', 'semantic', 'naming_convention'
    context: str = ""  # 附加上下文
    similarity_score: float = 0.0  # 语义相似度分数 (仅 semantic 方法使用)
    element_id: str = ""  # 源元素的 element_id (用于 Neo4j 链接)
    target_element_id: str = ""  # 目标元素的 element_id (用于 Neo4j 链接)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        result = {
            'source_type': self.source_type,
            'source_id': self.source_id,
            'target_type': self.target_type,
            'target_id': self.target_id,
            'confidence': self.confidence,
            'method': self.method,
            'context': self.context
        }
        if self.similarity_score > 0:
            result['similarity_score'] = self.similarity_score
        if self.element_id:
            result['element_id'] = self.element_id
        if self.target_element_id:
            result['target_element_id'] = self.target_element_id
        return result


class CodeRequirementLinker:
    """链接代码元素与需求"""

    # 不同链接方法的置信度分数
    CONFIDENCE_ANNOTATION = 1.0
    CONFIDENCE_FILE_PATH = 0.9
    CONFIDENCE_GIT_COMMIT = 0.8
    CONFIDENCE_SEMANTIC = 0.6

    def __init__(self, project_path: str = "."):
        self.project_path = Path(project_path)

    def find_all_links(self, elements: List[CodeElement], change_id: str,
                       task_file_paths: List[str] = None) -> List[Link]:
        """
        查找代码元素与需求之间的所有链接

        Args:
            elements: 代码元素列表
            change_id: 变更 ID
            task_file_paths: 任务中提到的文件路径列表

        Returns:
            链接列表
        """
        links = []

        # 方法 1: 基于注解的链接
        annotation_links = self.link_by_annotation(elements, change_id)
        links.extend(annotation_links)

        # 方法 2: 文件路径匹配
        if task_file_paths:
            file_links = self.link_by_file_path(elements, change_id, task_file_paths)
            links.extend(file_links)

        # 方法 3: Git 提交链接
        git_links = self.link_by_git_commit(change_id)
        links.extend(git_links)

        # 去重（保留最高置信度）
        links = self._deduplicate_links(links)

        return links

    def link_by_annotation(self, elements: List[CodeElement], change_id: str) -> List[Link]:
        """查找代码元素中的 @spec 注解"""
        links = []

        # 匹配 @spec 注解的模式
        spec_pattern = re.compile(r'@spec\s+([a-zA-Z0-9_-]+)', re.IGNORECASE)

        for element in elements:
            # 检查文档字符串
            if element.docstring:
                matches = spec_pattern.findall(element.docstring)
                for match in matches:
                    if match == change_id or match.lower() == change_id.lower():
                        links.append(Link(
                            source_type='code',
                            source_id=element.full_name,
                            target_type='requirement',
                            target_id=change_id,
                            confidence=self.CONFIDENCE_ANNOTATION,
                            method='annotation',
                            context=f"在 docstring 中找到 @spec {match}"
                        ))

            # 检查注解列表
            for annotation in element.annotations:
                if 'spec' in annotation.lower():
                    ann_matches = spec_pattern.findall(annotation)
                    for match in ann_matches:
                        if match == change_id or match.lower() == change_id.lower():
                            links.append(Link(
                                source_type='code',
                                source_id=element.full_name,
                                target_type='requirement',
                                target_id=change_id,
                                confidence=self.CONFIDENCE_ANNOTATION,
                                method='annotation',
                                context=f"在注解中找到 @spec {match}"
                            ))

        logger.info(f"为 {change_id} 找到 {len(links)} 个基于注解的链接")
        return links

    def link_by_file_path(self, elements: List[CodeElement], change_id: str,
                          task_file_paths: List[str]) -> List[Link]:
        """将任务文件路径与代码元素匹配"""
        links = []

        # 规范化任务文件路径
        normalized_paths = set()
        for path in task_file_paths:
            path = path.strip('`').strip()
            normalized_paths.add(path)
            normalized_paths.add(path.replace('/', '\\'))
            normalized_paths.add(path.replace('\\', '/'))
            normalized_paths.add(Path(path).name)

        for element in elements:
            if not element.file_path:
                continue

            element_path = element.file_path
            element_name = Path(element_path).name

            # 检查元素文件是否匹配任何任务文件
            matched = False
            for task_path in normalized_paths:
                if (task_path in element_path or
                    element_path.endswith(task_path) or
                    element_name == task_path):
                    matched = True
                    break

            if matched:
                links.append(Link(
                    source_type='code',
                    source_id=element.full_name,
                    target_type='requirement',
                    target_id=change_id,
                    confidence=self.CONFIDENCE_FILE_PATH,
                    method='file_path',
                    context=f"文件 {element_path} 在 tasks.md 中被提及"
                ))

        logger.info(f"为 {change_id} 找到 {len(links)} 个基于文件路径的链接")
        return links

    def link_by_git_commit(self, change_id: str) -> List[Link]:
        """解析 git 提交中的变更 ID 引用"""
        links = []

        try:
            # 获取最近的提交
            result = subprocess.run(
                ['git', 'log', '--oneline', '-100', '--all'],
                cwd=self.project_path,
                capture_output=True,
                text=True
            )

            if result.returncode != 0:
                logger.warning("获取 git log 失败")
                return links

            # 匹配提交信息中的变更 ID
            pattern = re.compile(rf'\b{re.escape(change_id)}\b', re.IGNORECASE)

            for line in result.stdout.split('\n'):
                if not line.strip():
                    continue

                if pattern.search(line):
                    commit_hash = line.split()[0]

                    # 获取此提交中更改的文件
                    files_result = subprocess.run(
                        ['git', 'diff-tree', '--no-commit-id', '--name-only', '-r', commit_hash],
                        cwd=self.project_path,
                        capture_output=True,
                        text=True
                    )

                    if files_result.returncode == 0:
                        for file_path in files_result.stdout.split('\n'):
                            if file_path.strip():
                                links.append(Link(
                                    source_type='code',
                                    source_id=file_path.strip(),
                                    target_type='requirement',
                                    target_id=change_id,
                                    confidence=self.CONFIDENCE_GIT_COMMIT,
                                    method='git_commit',
                                    context=f"提交 {commit_hash} 引用了 {change_id}"
                                ))

        except Exception as e:
            logger.warning(f"Git 提交链接失败: {e}")

        logger.info(f"为 {change_id} 找到 {len(links)} 个基于 git 提交的链接")
        return links

    def _deduplicate_links(self, links: List[Link]) -> List[Link]:
        """去重链接，为每个源-目标对保留最高置信度"""
        link_map = {}

        for link in links:
            key = (link.source_id, link.target_id)
            if key not in link_map or link.confidence > link_map[key].confidence:
                link_map[key] = link

        return list(link_map.values())

    def links_to_dict_list(self, links: List[Link]) -> List[Dict[str, Any]]:
        """
        将链接列表转换为字典列表，用于传递给 ontology 服务

        Args:
            links: 链接列表

        Returns:
            字典列表
        """
        return [link.to_dict() for link in links]


class TestCodeLinker:
    """链接测试文件与代码元素"""

    def __init__(self, project_path: str = "."):
        self.project_path = Path(project_path)

    def find_test_links(self, elements: List[CodeElement]) -> List[Link]:
        """查找测试文件与代码之间的链接"""
        links = []

        # 分离测试元素和代码元素
        test_elements = []
        code_elements = []

        for element in elements:
            if element.file_path and self._is_test_file(element.file_path):
                test_elements.append(element)
            else:
                code_elements.append(element)

        # 按名称构建代码元素索引
        code_index = {}
        for elem in code_elements:
            code_index[elem.name] = elem
            code_index[elem.full_name] = elem

        # 链接测试到代码
        for test in test_elements:
            tested_name = self._extract_tested_name(test.name)
            if tested_name and tested_name in code_index:
                code_elem = code_index[tested_name]
                links.append(Link(
                    source_type='test',
                    source_id=test.full_name,
                    target_type='code',
                    target_id=code_elem.full_name,
                    confidence=0.9,
                    method='naming_convention',
                    context=f"测试 {test.name} 测试 {code_elem.name}"
                ))

        return links

    def _is_test_file(self, file_path: str) -> bool:
        """检查文件是否为测试文件"""
        path = Path(file_path)
        name = path.stem.lower()

        return (
            name.startswith('test_') or
            name.endswith('_test') or
            name.endswith('.test') or
            name.endswith('.spec') or
            'test' in path.parts or
            'tests' in path.parts or
            '__tests__' in path.parts
        )

    def _extract_tested_name(self, test_name: str) -> Optional[str]:
        """从测试名称中提取被测试元素的名称"""
        name = test_name

        # Python 风格: test_something -> something
        if name.startswith('test_'):
            name = name[5:]
        elif name.startswith('Test'):
            name = name[4:]

        # JS 风格: something.test -> something
        if name.endswith('_test'):
            name = name[:-5]
        elif name.endswith('Test'):
            name = name[:-4]
        elif name.endswith('.test'):
            name = name[:-5]
        elif name.endswith('.spec'):
            name = name[:-5]

        return name if name != test_name else None


class SemanticLinker:
    """
    基于语义相似度的链接器

    使用 Embedding 向量计算代码元素与需求之间的语义相似度，
    生成高置信度的链接候选。

    需要 ontology 项目的 EmbeddingClient 支持。
    """

    # 语义匹配的置信度阈值
    SIMILARITY_THRESHOLD = 0.6  # 最低相似度阈值
    HIGH_CONFIDENCE_THRESHOLD = 0.8  # 高置信度阈值

    def __init__(
        self,
        embedding_client: Optional[Any] = None,
        ontology_path: Optional[str] = None
    ):
        """
        初始化语义链接器

        Args:
            embedding_client: Embedding 客户端实例 (可选)
            ontology_path: ontology 项目路径，用于创建 EmbeddingClient
        """
        self.embedding_client = embedding_client
        self.ontology_path = ontology_path or os.environ.get(
            "ONTOLOGY_PROJECT_PATH",
            os.path.expanduser("~/iuapgit/ontology")
        )
        self._initialized = False

    def _ensure_initialized(self) -> bool:
        """确保 Embedding 客户端已初始化"""
        if self._initialized:
            return self.embedding_client is not None

        if self.embedding_client is None:
            self.embedding_client = self._create_embedding_client()

        self._initialized = True
        return self.embedding_client is not None

    def _create_embedding_client(self) -> Optional[Any]:
        """
        创建 Embedding 客户端

        尝试从 ontology 项目导入 EmbeddingClient。
        """
        try:
            import sys
            ontology_path = Path(self.ontology_path)

            # 添加 ontology 项目到 Python 路径
            if str(ontology_path) not in sys.path:
                sys.path.insert(0, str(ontology_path))

            from graph_reasoning.core.embedding_client import CachedEmbeddingClient

            # 从环境变量获取配置
            api_base = os.environ.get("EMBEDDING_API_BASE", "http://localhost:8003/v1")
            api_key = os.environ.get("EMBEDDING_API_KEY", "EMPTY")
            model = os.environ.get("EMBEDDING_MODEL", "bge-m3")

            client = CachedEmbeddingClient(
                api_base=api_base,
                api_key=api_key,
                model=model
            )
            logger.info(f"Embedding 客户端已创建: {model}")
            return client

        except ImportError as e:
            logger.warning(f"无法导入 EmbeddingClient: {e}")
            return None
        except Exception as e:
            logger.warning(f"创建 Embedding 客户端失败: {e}")
            return None

    def generate_text_for_element(self, element: CodeElement) -> str:
        """
        为代码元素生成用于 Embedding 的文本

        Args:
            element: 代码元素

        Returns:
            用于 Embedding 的文本
        """
        parts = []

        # 元素名称
        parts.append(element.name)

        # 文档字符串
        if element.docstring:
            parts.append(element.docstring)

        # 方法签名 (如果有参数)
        if element.parameters:
            # parameters 可能是 List[str] 或 List[Dict]
            if element.parameters and isinstance(element.parameters[0], str):
                param_str = ", ".join(element.parameters)
            else:
                param_str = ", ".join(str(p) for p in element.parameters)
            parts.append(f"参数: {param_str}")

        # 返回类型
        if element.return_type:
            parts.append(f"返回: {element.return_type}")

        return " ".join(parts)

    def generate_text_for_requirement(self, requirement_text: str) -> str:
        """
        为需求文本生成用于 Embedding 的文本

        Args:
            requirement_text: 需求文本

        Returns:
            处理后的文本
        """
        # 移除 Markdown 格式
        text = re.sub(r'#+\s*', '', requirement_text)
        text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
        text = re.sub(r'\*([^*]+)\*', r'\1', text)
        text = re.sub(r'`([^`]+)`', r'\1', text)
        text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)

        return text.strip()

    def link_by_semantic(
        self,
        elements: List[CodeElement],
        requirements: List[Dict[str, str]],
        top_k: int = 5,
        min_similarity: Optional[float] = None
    ) -> List[Link]:
        """
        基于语义相似度链接代码元素与需求

        Args:
            elements: 代码元素列表
            requirements: 需求列表，每个需求是 {'id': str, 'text': str}
            top_k: 每个需求返回的最相似代码元素数量
            min_similarity: 最低相似度阈值

        Returns:
            链接列表
        """
        if not self._ensure_initialized():
            logger.warning("Embedding 客户端未初始化，跳过语义匹配")
            return []

        if not HAS_NUMPY:
            logger.warning("numpy 未安装，跳过语义匹配")
            return []

        if not elements or not requirements:
            return []

        min_sim = min_similarity or self.SIMILARITY_THRESHOLD
        links = []

        try:
            # 生成代码元素的文本和 Embedding
            element_texts = [self.generate_text_for_element(e) for e in elements]
            element_embeddings = self.embedding_client.embed_batch(element_texts)

            # 为每个需求找到最相似的代码元素
            for req in requirements:
                req_id = req.get('id', '')
                req_text = req.get('text', '')

                if not req_text:
                    continue

                # 生成需求的 Embedding
                req_text_processed = self.generate_text_for_requirement(req_text)
                req_embedding = self.embedding_client.embed(req_text_processed)

                # 计算相似度
                similarities = self.embedding_client.batch_cosine_similarity(
                    req_embedding, element_embeddings
                )

                # 找到 top_k 个最相似的元素
                top_indices = np.argsort(similarities)[::-1][:top_k]

                for idx in top_indices:
                    sim = float(similarities[idx])
                    if sim < min_sim:
                        continue

                    element = elements[idx]

                    # 计算置信度 (基于相似度)
                    if sim >= self.HIGH_CONFIDENCE_THRESHOLD:
                        confidence = 0.8 + (sim - self.HIGH_CONFIDENCE_THRESHOLD) * 0.5
                    else:
                        confidence = 0.5 + (sim - min_sim) / (self.HIGH_CONFIDENCE_THRESHOLD - min_sim) * 0.3

                    confidence = min(confidence, 0.95)  # 语义匹配最高 0.95

                    links.append(Link(
                        source_type='code',
                        source_id=element.full_name,
                        target_type='requirement',
                        target_id=req_id,
                        confidence=confidence,
                        method='semantic',
                        context=f"语义相似度: {sim:.3f}",
                        similarity_score=sim
                    ))

            logger.info(f"语义匹配找到 {len(links)} 个链接")
            return links

        except Exception as e:
            logger.error(f"语义匹配失败: {e}")
            return []

    def find_similar_elements(
        self,
        query_text: str,
        elements: List[CodeElement],
        top_k: int = 10
    ) -> List[Tuple[CodeElement, float]]:
        """
        找到与查询文本最相似的代码元素

        Args:
            query_text: 查询文本
            elements: 代码元素列表
            top_k: 返回数量

        Returns:
            [(element, similarity), ...] 按相似度降序
        """
        if not self._ensure_initialized():
            return []

        if not HAS_NUMPY:
            return []

        try:
            element_texts = [self.generate_text_for_element(e) for e in elements]
            results = self.embedding_client.find_similar(query_text, element_texts, top_k)

            # 映射回元素
            text_to_element = {text: elem for text, elem in zip(element_texts, elements)}
            return [(text_to_element[text], sim) for text, sim in results if text in text_to_element]

        except Exception as e:
            logger.error(f"相似元素查找失败: {e}")
            return []


class LinkValidator:
    """
    链接验证器

    验证链接的有效性，包括：
    - element_id 存在性验证
    - 置信度计算
    - 链接结果导入 Neo4j
    """

    def __init__(
        self,
        neo4j_uri: Optional[str] = None,
        neo4j_user: Optional[str] = None,
        neo4j_password: Optional[str] = None,
        database: str = "ontologydevos"
    ):
        """
        初始化链接验证器

        Args:
            neo4j_uri: Neo4j 连接地址
            neo4j_user: 用户名
            neo4j_password: 密码
            database: 数据库名
        """
        self.neo4j_uri = neo4j_uri or os.environ.get("ONTOLOGY_NEO4J_URI", "bolt://localhost:7687")
        self.neo4j_user = neo4j_user or os.environ.get("ONTOLOGY_NEO4J_USER", "neo4j")
        self.neo4j_password = neo4j_password or os.environ.get("ONTOLOGY_NEO4J_PASSWORD", "")
        self.database = database
        self._adapter = None

    def _get_adapter(self) -> Optional[Any]:
        """获取 Neo4j 适配器"""
        if self._adapter is not None:
            return self._adapter

        try:
            import sys
            ontology_path = os.environ.get(
                "ONTOLOGY_PROJECT_PATH",
                os.path.expanduser("~/iuapgit/ontology")
            )
            if ontology_path not in sys.path:
                sys.path.insert(0, ontology_path)

            from graph_reasoning.core.neo4j_adapter import Neo4jAdapter

            self._adapter = Neo4jAdapter(
                uri=self.neo4j_uri,
                user=self.neo4j_user,
                password=self.neo4j_password,
                database=self.database
            )
            self._adapter.connect()
            logger.info(f"Neo4j 适配器已连接: {self.database}")
            return self._adapter

        except Exception as e:
            logger.warning(f"无法创建 Neo4j 适配器: {e}")
            return None

    def validate_element_exists(self, element_id: str) -> bool:
        """
        验证 element_id 在 Neo4j 中是否存在

        Args:
            element_id: 元素 ID

        Returns:
            是否存在
        """
        adapter = self._get_adapter()
        if not adapter:
            return False

        try:
            result = adapter.execute_query(
                "MATCH (n {element_id: $element_id}) RETURN count(n) as count",
                parameters={"element_id": element_id},
                max_results=1
            )

            if result.success and result.data:
                return result.data[0].get('count', 0) > 0
            return False

        except Exception as e:
            logger.error(f"验证 element_id 失败: {e}")
            return False

    def validate_links(self, links: List[Link]) -> List[Link]:
        """
        验证链接列表，过滤无效链接

        Args:
            links: 链接列表

        Returns:
            有效的链接列表
        """
        valid_links = []
        adapter = self._get_adapter()

        if not adapter:
            logger.warning("Neo4j 未连接，跳过链接验证")
            return links

        # 批量查询所有 element_id
        all_ids = set()
        for link in links:
            if link.element_id:
                all_ids.add(link.element_id)
            if link.target_element_id:
                all_ids.add(link.target_element_id)

        if not all_ids:
            return links

        # 批量验证
        existing_ids = set()
        try:
            result = adapter.execute_query(
                "MATCH (n) WHERE n.element_id IN $ids RETURN n.element_id as id",
                parameters={"ids": list(all_ids)},
                max_results=len(all_ids)
            )

            if result.success:
                existing_ids = {r.get('id') for r in result.data if r.get('id')}

        except Exception as e:
            logger.error(f"批量验证失败: {e}")
            return links

        # 过滤有效链接
        for link in links:
            is_valid = True

            if link.element_id and link.element_id not in existing_ids:
                logger.debug(f"源 element_id 不存在: {link.element_id}")
                is_valid = False

            if link.target_element_id and link.target_element_id not in existing_ids:
                logger.debug(f"目标 element_id 不存在: {link.target_element_id}")
                is_valid = False

            if is_valid:
                valid_links.append(link)

        logger.info(f"链接验证: {len(valid_links)}/{len(links)} 有效")
        return valid_links

    def calculate_confidence(self, link: Link) -> float:
        """
        计算链接的综合置信度

        综合考虑：
        - 链接方法的基础置信度
        - 语义相似度 (如果有)
        - element_id 存在性

        Args:
            link: 链接

        Returns:
            综合置信度
        """
        base_confidence = link.confidence

        # 语义相似度加成
        if link.similarity_score > 0:
            sim_bonus = link.similarity_score * 0.1
            base_confidence = min(base_confidence + sim_bonus, 1.0)

        # element_id 存在性验证
        if link.element_id:
            if self.validate_element_exists(link.element_id):
                base_confidence = min(base_confidence + 0.05, 1.0)
            else:
                base_confidence *= 0.8  # 降低置信度

        return base_confidence

    def import_links_to_neo4j(self, links: List[Link]) -> Dict[str, int]:
        """
        将链接导入 Neo4j

        创建 TRACES_TO 关系连接代码元素和需求。

        Args:
            links: 链接列表

        Returns:
            {'created': int, 'failed': int}
        """
        adapter = self._get_adapter()
        if not adapter:
            return {'created': 0, 'failed': len(links)}

        created = 0
        failed = 0

        for link in links:
            try:
                # 创建链接关系
                cypher = """
                MATCH (source {element_id: $source_id})
                MATCH (target {element_id: $target_id})
                MERGE (source)-[r:TRACES_TO]->(target)
                SET r.confidence = $confidence,
                    r.method = $method,
                    r.context = $context,
                    r.similarity_score = $similarity_score,
                    r.created_at = datetime()
                RETURN count(r) as count
                """

                result = adapter.execute_query(
                    cypher,
                    parameters={
                        'source_id': link.element_id or link.source_id,
                        'target_id': link.target_element_id or link.target_id,
                        'confidence': link.confidence,
                        'method': link.method,
                        'context': link.context,
                        'similarity_score': link.similarity_score
                    },
                    max_results=1
                )

                if result.success and result.data and result.data[0].get('count', 0) > 0:
                    created += 1
                else:
                    failed += 1

            except Exception as e:
                logger.error(f"导入链接失败: {e}")
                failed += 1

        logger.info(f"链接导入完成: 成功 {created}, 失败 {failed}")
        return {'created': created, 'failed': failed}

    def close(self):
        """关闭连接"""
        if self._adapter:
            self._adapter.close()
            self._adapter = None


class TraceabilityQuery:
    """
    追溯查询

    提供需求 → 代码、代码 → 测试、变更影响分析等追溯查询功能。
    """

    def __init__(
        self,
        neo4j_uri: Optional[str] = None,
        neo4j_user: Optional[str] = None,
        neo4j_password: Optional[str] = None,
        database: str = "ontologydevos"
    ):
        """
        初始化追溯查询

        Args:
            neo4j_uri: Neo4j 连接地址
            neo4j_user: 用户名
            neo4j_password: 密码
            database: 数据库名
        """
        self.neo4j_uri = neo4j_uri or os.environ.get("ONTOLOGY_NEO4J_URI", "bolt://localhost:7687")
        self.neo4j_user = neo4j_user or os.environ.get("ONTOLOGY_NEO4J_USER", "neo4j")
        self.neo4j_password = neo4j_password or os.environ.get("ONTOLOGY_NEO4J_PASSWORD", "")
        self.database = database
        self._adapter = None

    def _get_adapter(self) -> Optional[Any]:
        """获取 Neo4j 适配器"""
        if self._adapter is not None:
            return self._adapter

        try:
            import sys
            ontology_path = os.environ.get(
                "ONTOLOGY_PROJECT_PATH",
                os.path.expanduser("~/iuapgit/ontology")
            )
            if ontology_path not in sys.path:
                sys.path.insert(0, ontology_path)

            from graph_reasoning.core.neo4j_adapter import Neo4jAdapter

            self._adapter = Neo4jAdapter(
                uri=self.neo4j_uri,
                user=self.neo4j_user,
                password=self.neo4j_password,
                database=self.database
            )
            self._adapter.connect()
            return self._adapter

        except Exception as e:
            logger.warning(f"无法创建 Neo4j 适配器: {e}")
            return None

    def trace_requirement_to_code(
        self,
        requirement_id: str,
        min_confidence: float = 0.5
    ) -> List[Dict[str, Any]]:
        """
        需求 → 代码追溯

        查找实现指定需求的代码元素。

        Args:
            requirement_id: 需求 ID 或 element_id
            min_confidence: 最低置信度

        Returns:
            代码元素列表
        """
        adapter = self._get_adapter()
        if not adapter:
            return []

        try:
            cypher = """
            MATCH (req)-[r:TRACES_TO]->(code)
            WHERE (req.element_id = $req_id OR req.id = $req_id)
              AND r.confidence >= $min_confidence
            RETURN code.element_id as element_id,
                   code.name as name,
                   code.full_name as full_name,
                   code.file_path as file_path,
                   code.line_number as line_number,
                   r.confidence as confidence,
                   r.method as method
            ORDER BY r.confidence DESC
            """

            result = adapter.execute_query(
                cypher,
                parameters={
                    'req_id': requirement_id,
                    'min_confidence': min_confidence
                },
                max_results=100
            )

            if result.success:
                return result.data
            return []

        except Exception as e:
            logger.error(f"需求追溯查询失败: {e}")
            return []

    def trace_code_to_tests(
        self,
        code_element_id: str
    ) -> List[Dict[str, Any]]:
        """
        代码 → 测试追溯

        查找测试指定代码元素的测试用例。

        Args:
            code_element_id: 代码元素 ID

        Returns:
            测试用例列表
        """
        adapter = self._get_adapter()
        if not adapter:
            return []

        try:
            cypher = """
            MATCH (test)-[r:TESTS|TRACES_TO]->(code)
            WHERE code.element_id = $code_id
              AND (test:Test OR test.type = 'test')
            RETURN test.element_id as element_id,
                   test.name as name,
                   test.full_name as full_name,
                   test.file_path as file_path,
                   r.confidence as confidence
            ORDER BY r.confidence DESC
            """

            result = adapter.execute_query(
                cypher,
                parameters={'code_id': code_element_id},
                max_results=100
            )

            if result.success:
                return result.data
            return []

        except Exception as e:
            logger.error(f"代码测试追溯查询失败: {e}")
            return []

    def analyze_change_impact(
        self,
        element_id: str,
        depth: int = 2
    ) -> Dict[str, Any]:
        """
        变更影响分析

        分析修改指定元素可能影响的其他元素。

        Args:
            element_id: 要分析的元素 ID
            depth: 追溯深度

        Returns:
            影响分析结果
        """
        adapter = self._get_adapter()
        if not adapter:
            return {'affected': [], 'tests': [], 'requirements': []}

        result = {
            'affected': [],  # 受影响的代码元素
            'tests': [],     # 需要重新运行的测试
            'requirements': []  # 相关的需求
        }

        try:
            # 查找依赖此元素的代码
            affected_cypher = """
            MATCH (source)-[r:CALLS|IMPORTS|EXTENDS|IMPLEMENTS*1..%d]->(target)
            WHERE target.element_id = $element_id
            RETURN DISTINCT source.element_id as element_id,
                   source.name as name,
                   source.full_name as full_name,
                   source.file_path as file_path,
                   source.type as type
            """ % depth

            affected_result = adapter.execute_query(
                affected_cypher,
                parameters={'element_id': element_id},
                max_results=200
            )

            if affected_result.success:
                result['affected'] = affected_result.data

            # 查找相关测试
            tests_cypher = """
            MATCH (test)-[r:TESTS|TRACES_TO*1..%d]->(target)
            WHERE target.element_id = $element_id
              AND (test:Test OR test.type = 'test')
            RETURN DISTINCT test.element_id as element_id,
                   test.name as name,
                   test.file_path as file_path
            """ % depth

            tests_result = adapter.execute_query(
                tests_cypher,
                parameters={'element_id': element_id},
                max_results=100
            )

            if tests_result.success:
                result['tests'] = tests_result.data

            # 查找相关需求
            req_cypher = """
            MATCH (req)-[r:TRACES_TO*1..%d]->(target)
            WHERE target.element_id = $element_id
              AND (req:Requirement OR req.type = 'requirement')
            RETURN DISTINCT req.element_id as element_id,
                   req.name as name,
                   req.title as title,
                   r.confidence as confidence
            """ % depth

            req_result = adapter.execute_query(
                req_cypher,
                parameters={'element_id': element_id},
                max_results=50
            )

            if req_result.success:
                result['requirements'] = req_result.data

            logger.info(
                f"变更影响分析: {len(result['affected'])} 个受影响元素, "
                f"{len(result['tests'])} 个测试, {len(result['requirements'])} 个需求"
            )

            return result

        except Exception as e:
            logger.error(f"变更影响分析失败: {e}")
            return result

    def get_traceability_matrix(
        self,
        requirement_ids: List[str] = None
    ) -> List[Dict[str, Any]]:
        """
        获取追溯矩阵

        生成需求-代码-测试的追溯矩阵。

        Args:
            requirement_ids: 需求 ID 列表 (可选，为空则查询所有)

        Returns:
            追溯矩阵数据
        """
        adapter = self._get_adapter()
        if not adapter:
            return []

        try:
            if requirement_ids:
                cypher = """
                MATCH (req)-[r1:TRACES_TO]->(code)
                WHERE req.element_id IN $req_ids
                OPTIONAL MATCH (test)-[r2:TESTS|TRACES_TO]->(code)
                WHERE test:Test OR test.type = 'test'
                RETURN req.element_id as requirement_id,
                       req.name as requirement_name,
                       code.element_id as code_id,
                       code.name as code_name,
                       code.file_path as code_file,
                       r1.confidence as link_confidence,
                       collect(DISTINCT test.element_id) as test_ids,
                       collect(DISTINCT test.name) as test_names
                ORDER BY req.element_id, r1.confidence DESC
                """
                params = {'req_ids': requirement_ids}
            else:
                cypher = """
                MATCH (req)-[r1:TRACES_TO]->(code)
                WHERE req:Requirement OR req.type = 'requirement'
                OPTIONAL MATCH (test)-[r2:TESTS|TRACES_TO]->(code)
                WHERE test:Test OR test.type = 'test'
                RETURN req.element_id as requirement_id,
                       req.name as requirement_name,
                       code.element_id as code_id,
                       code.name as code_name,
                       code.file_path as code_file,
                       r1.confidence as link_confidence,
                       collect(DISTINCT test.element_id) as test_ids,
                       collect(DISTINCT test.name) as test_names
                ORDER BY req.element_id, r1.confidence DESC
                """
                params = {}

            result = adapter.execute_query(cypher, parameters=params, max_results=500)

            if result.success:
                return result.data
            return []

        except Exception as e:
            logger.error(f"获取追溯矩阵失败: {e}")
            return []

    def close(self):
        """关闭连接"""
        if self._adapter:
            self._adapter.close()
            self._adapter = None
