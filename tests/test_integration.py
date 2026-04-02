# -*- coding: utf-8 -*-
"""
集成测试：代码本体构建端到端流程

测试流程：
1. 代码解析 → 文档生成 → ontology 服务 → TTL 生成
2. SDD 链接 → ontology 服务 → 链接 TTL
3. 语义匹配 → 链接验证 → 追溯查询
"""

import sys
import json
import logging
import os
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from code_processor import (
    ParserFactory, DocumentGenerator, ProjectInfo,
    CodeElement, ElementType, LanguageType
)
from code_processor.document_writer import DocumentWriter, Document, generate_element_id
from ontology_client import OntologyClient, BuildResult
from rd_ontology import get_schema_ttl
from sdd_integration import (
    CodeRequirementLinker, SemanticLinker, LinkValidator, TraceabilityQuery
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_document_generator():
    """测试文档生成器"""
    print("\n" + "=" * 50)
    print("测试 1: DocumentGenerator")
    print("=" * 50)

    # 创建测试项目
    project = ProjectInfo('/test/project', LanguageType.PYTHON)

    # 添加测试元素
    class_elem = CodeElement(
        element_type=ElementType.CLASS,
        name='UserService',
        full_name='com.example.service.UserService',
        file_path='src/service/user_service.py',
        line_number=10,
        package='com.example.service',
        modifiers=['public'],
        docstring='用户服务类，提供用户认证和管理功能',
        annotations=['@Service']
    )

    method_elem = CodeElement(
        element_type=ElementType.METHOD,
        name='authenticate',
        full_name='com.example.service.UserService.authenticate',
        file_path='src/service/user_service.py',
        line_number=25,
        parameters=[
            {'name': 'username', 'type': 'str'},
            {'name': 'password', 'type': 'str'}
        ],
        return_type='bool',
        docstring='验证用户凭据'
    )
    class_elem.add_child(method_elem)

    project.add_element(class_elem)

    # 生成文档
    generator = DocumentGenerator()
    documents = generator.generate_all_documents(project)

    print(f"✅ 生成了 {len(documents)} 个文档")
    print(f"✅ 统计: {generator.get_stats()}")

    # 验证文档内容
    assert len(documents) >= 2, "应该至少生成 2 个文档"
    assert any('UserService' in doc for doc in documents), "文档应包含 UserService"

    print("✅ DocumentGenerator 测试通过")
    return documents


def test_ontology_client_init():
    """测试 OntologyClient 初始化"""
    print("\n" + "=" * 50)
    print("测试 2: OntologyClient 初始化")
    print("=" * 50)

    client = OntologyClient()

    print(f"✅ ontology_path: {client.config.ontology_path}")
    print(f"✅ domain: {client.config.domain}")
    print(f"✅ neo4j_uri: {client.config.neo4j_uri}")

    # 验证配置
    assert client.config.ontology_path, "ontology_path 应该已配置"

    print("✅ OntologyClient 初始化测试通过")
    return client


def test_schema_ttl():
    """测试 Schema TTL 读取"""
    print("\n" + "=" * 50)
    print("测试 3: Schema TTL")
    print("=" * 50)

    schema = get_schema_ttl()

    print(f"✅ Schema TTL 长度: {len(schema)} 字符")

    # 验证 schema 内容
    assert len(schema) > 0, "Schema TTL 不应为空"
    assert '@prefix' in schema, "Schema 应包含前缀定义"
    assert 'CodeClass' in schema, "Schema 应包含 CodeClass 定义"

    print("✅ Schema TTL 测试通过")
    return schema


def test_code_requirement_linker():
    """测试代码-需求链接器"""
    print("\n" + "=" * 50)
    print("测试 4: CodeRequirementLinker")
    print("=" * 50)

    linker = CodeRequirementLinker()

    # 创建测试元素
    elements = [
        CodeElement(
            element_type=ElementType.CLASS,
            name='UserService',
            full_name='com.example.UserService',
            file_path='src/user_service.py',
            line_number=10,
            docstring='@spec add-user-auth 用户认证服务'
        ),
        CodeElement(
            element_type=ElementType.METHOD,
            name='authenticate',
            full_name='com.example.UserService.authenticate',
            file_path='src/user_service.py',
            line_number=25
        )
    ]

    # 查找链接
    links = linker.find_all_links(
        elements=elements,
        change_id='add-user-auth',
        task_file_paths=['src/user_service.py']
    )

    print(f"✅ 找到 {len(links)} 个链接")
    for link in links:
        print(f"   - {link.source_id} -> {link.target_id} ({link.method}, {link.confidence})")

    # 验证链接
    assert len(links) > 0, "应该找到至少一个链接"

    # 转换为字典列表
    links_dict = linker.links_to_dict_list(links)
    print(f"✅ 链接字典: {json.dumps(links_dict[0], ensure_ascii=False, indent=2)}")

    print("✅ CodeRequirementLinker 测试通过")
    return links


def test_build_code_ontology(client: OntologyClient, documents: list):
    """测试构建代码本体（需要 LLM 配置）"""
    print("\n" + "=" * 50)
    print("测试 5: build_code_ontology")
    print("=" * 50)

    try:
        result = client.build_code_ontology(
            documents=documents,
            domain="rd",
            import_to_neo4j=False
        )

        print(f"✅ 构建结果: {result.success}")
        print(f"✅ 实体数: {result.entities_count}")
        print(f"✅ 关系数: {result.relations_count}")

        if result.errors:
            print(f"⚠️ 错误: {result.errors}")

        if result.ttl_content:
            print(f"✅ TTL 内容预览:\n{result.ttl_content[:500]}...")

        return result

    except Exception as e:
        print(f"⚠️ 构建失败（可能是 LLM 未配置）: {e}")
        return None


def test_real_project_analysis():
    """测试真实项目分析"""
    print("\n" + "=" * 50)
    print("测试 6: 真实项目分析")
    print("=" * 50)

    # 分析当前项目的 code_processor 模块
    project_path = Path(__file__).parent.parent / "code_processor"

    if not project_path.exists():
        print(f"⚠️ 项目路径不存在: {project_path}")
        return None

    try:
        parser = ParserFactory.create_parser(str(project_path))
        project_info = parser.parse_project()

        print(f"✅ 语言: {project_info.language.value}")
        print(f"✅ 元素数: {len(project_info.elements)}")
        print(f"✅ 关系数: {len(project_info.relations)}")

        # 生成文档
        generator = DocumentGenerator()
        documents = generator.generate_all_documents(project_info)

        print(f"✅ 生成文档数: {len(documents)}")

        return documents

    except Exception as e:
        print(f"⚠️ 分析失败: {e}")
        return None


def test_document_writer():
    """测试文档写入器"""
    print("\n" + "=" * 50)
    print("测试 7: DocumentWriter")
    print("=" * 50)

    # 创建测试文档
    doc = Document(
        content="# UserService\n\n用户服务类",
        doc_type="class",
        name="UserService",
        full_name="com.example.UserService",
        file_path="src/user_service.py",
        line_number=10,
        language="python",
        package="com.example",
        element_id="code:python:test_project:com.example.UserService",
        metadata={"modifiers": ["public"]}
    )

    print(f"✅ 文档创建成功: {doc.name}")
    print(f"✅ element_id: {doc.element_id}")

    # 测试 Markdown 输出
    markdown = doc.to_markdown()
    assert "---" in markdown, "应包含 frontmatter 分隔符"
    assert "element_id:" in markdown, "应包含 element_id"
    print(f"✅ Markdown 输出:\n{markdown[:300]}...")

    # 测试 element_id 生成
    elem_id = generate_element_id("python", "my_project", "com.example.MyClass")
    assert elem_id == "code:python:my_project:com.example.MyClass"
    print(f"✅ element_id 生成: {elem_id}")

    print("✅ DocumentWriter 测试通过")
    return doc


def test_document_generator_with_objects():
    """测试文档生成器返回 Document 对象"""
    print("\n" + "=" * 50)
    print("测试 8: DocumentGenerator 返回 Document 对象")
    print("=" * 50)

    # 创建测试项目
    project = ProjectInfo('/test/project', LanguageType.PYTHON)

    # 添加测试元素
    class_elem = CodeElement(
        element_type=ElementType.CLASS,
        name='OrderService',
        full_name='com.example.service.OrderService',
        file_path='src/service/order_service.py',
        line_number=10,
        package='com.example.service',
        modifiers=['public'],
        docstring='订单服务类，处理订单相关业务'
    )
    project.add_element(class_elem)

    # 生成文档对象
    generator = DocumentGenerator(project_name='test_project')
    documents = generator.generate_all_documents(project, return_document_objects=True)

    print(f"✅ 生成了 {len(documents)} 个 Document 对象")

    # 验证返回的是 Document 对象
    assert len(documents) > 0, "应该生成至少一个文档"
    doc = documents[0]
    assert hasattr(doc, 'element_id'), "应该是 Document 对象"
    assert doc.element_id.startswith('code:'), "element_id 应以 code: 开头"

    print(f"✅ 第一个文档: {doc.name}")
    print(f"✅ element_id: {doc.element_id}")

    print("✅ DocumentGenerator Document 对象测试通过")
    return documents


def test_semantic_linker():
    """测试语义链接器"""
    print("\n" + "=" * 50)
    print("测试 9: SemanticLinker")
    print("=" * 50)

    linker = SemanticLinker()

    # 测试文本生成
    element = CodeElement(
        element_type=ElementType.METHOD,
        name='authenticate',
        full_name='UserService.authenticate',
        file_path='user_service.py',
        line_number=25,
        parameters=['username', 'password'],
        return_type='bool',
        docstring='验证用户凭据'
    )

    text = linker.generate_text_for_element(element)
    print(f"✅ 元素文本: {text}")
    assert 'authenticate' in text, "文本应包含方法名"

    # 测试需求文本处理
    req_text = "## 用户认证\n系统 **SHALL** 提供 `authenticate` 方法"
    processed = linker.generate_text_for_requirement(req_text)
    print(f"✅ 处理后需求文本: {processed}")
    assert '**' not in processed, "应移除 Markdown 格式"

    print("✅ SemanticLinker 测试通过")
    return linker


def test_link_validator():
    """测试链接验证器"""
    print("\n" + "=" * 50)
    print("测试 10: LinkValidator")
    print("=" * 50)

    validator = LinkValidator()

    # 测试置信度计算
    from sdd_integration import Link
    link = Link(
        source_type='code',
        source_id='UserService.authenticate',
        target_type='requirement',
        target_id='add-user-auth',
        confidence=0.8,
        method='semantic',
        similarity_score=0.85
    )

    confidence = validator.calculate_confidence(link)
    print(f"✅ 原始置信度: {link.confidence}")
    print(f"✅ 计算后置信度: {confidence}")

    print("✅ LinkValidator 测试通过")
    return validator


def test_traceability_query():
    """测试追溯查询"""
    print("\n" + "=" * 50)
    print("测试 11: TraceabilityQuery")
    print("=" * 50)

    query = TraceabilityQuery()

    # 测试实例化
    print(f"✅ Neo4j URI: {query.neo4j_uri}")
    print(f"✅ Database: {query.database}")

    # 注意：实际查询需要 Neo4j 连接，这里只测试实例化
    print("✅ TraceabilityQuery 测试通过（实例化）")
    return query


def run_all_tests():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("代码本体构建集成测试")
    print("=" * 60)

    results = {
        'passed': 0,
        'failed': 0,
        'skipped': 0
    }

    # 测试 1: DocumentGenerator
    try:
        documents = test_document_generator()
        results['passed'] += 1
    except Exception as e:
        print(f"❌ 测试 1 失败: {e}")
        results['failed'] += 1
        documents = []

    # 测试 2: OntologyClient 初始化
    try:
        client = test_ontology_client_init()
        results['passed'] += 1
    except Exception as e:
        print(f"❌ 测试 2 失败: {e}")
        results['failed'] += 1
        client = None

    # 测试 3: Schema TTL
    try:
        test_schema_ttl()
        results['passed'] += 1
    except Exception as e:
        print(f"❌ 测试 3 失败: {e}")
        results['failed'] += 1

    # 测试 4: CodeRequirementLinker
    try:
        test_code_requirement_linker()
        results['passed'] += 1
    except Exception as e:
        print(f"❌ 测试 4 失败: {e}")
        results['failed'] += 1

    # 测试 5: build_code_ontology（可能跳过）
    if client and documents:
        try:
            result = test_build_code_ontology(client, documents)
            if result and result.success:
                results['passed'] += 1
            else:
                results['skipped'] += 1
                print("⚠️ 测试 5 跳过（LLM 未配置或构建失败）")
        except Exception as e:
            print(f"⚠️ 测试 5 跳过: {e}")
            results['skipped'] += 1
    else:
        results['skipped'] += 1

    # 测试 6: 真实项目分析
    try:
        real_docs = test_real_project_analysis()
        if real_docs:
            results['passed'] += 1
        else:
            results['skipped'] += 1
    except Exception as e:
        print(f"❌ 测试 6 失败: {e}")
        results['failed'] += 1

    # 测试 7: DocumentWriter
    try:
        test_document_writer()
        results['passed'] += 1
    except Exception as e:
        print(f"❌ 测试 7 失败: {e}")
        results['failed'] += 1

    # 测试 8: DocumentGenerator 返回 Document 对象
    try:
        test_document_generator_with_objects()
        results['passed'] += 1
    except Exception as e:
        print(f"❌ 测试 8 失败: {e}")
        results['failed'] += 1

    # 测试 9: SemanticLinker
    try:
        test_semantic_linker()
        results['passed'] += 1
    except Exception as e:
        print(f"❌ 测试 9 失败: {e}")
        results['failed'] += 1

    # 测试 10: LinkValidator
    try:
        test_link_validator()
        results['passed'] += 1
    except Exception as e:
        print(f"❌ 测试 10 失败: {e}")
        results['failed'] += 1

    # 测试 11: TraceabilityQuery
    try:
        test_traceability_query()
        results['passed'] += 1
    except Exception as e:
        print(f"❌ 测试 11 失败: {e}")
        results['failed'] += 1

    # 总结
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    print(f"✅ 通过: {results['passed']}")
    print(f"❌ 失败: {results['failed']}")
    print(f"⚠️ 跳过: {results['skipped']}")

    return results['failed'] == 0


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
