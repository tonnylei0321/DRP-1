# -*- coding: utf-8 -*-
"""
Ontology Client

用于与 ontology 项目交互的客户端，支持：
- 调用 ontology 服务构建代码本体
- 调用 ontology 服务构建 SDD 本体
- TTL 文件上传
- Neo4j 查询
"""

import os
import sys
import json
import logging
import tempfile
import warnings
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass, field

from .config import OntologyConfig, get_config

logger = logging.getLogger(__name__)


@dataclass
class BuildResult:
    """本体构建结果"""
    success: bool
    ttl_content: str = ""
    entities_count: int = 0
    relations_count: int = 0
    links_count: int = 0
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    duration_ms: int = 0
    build_dir: str = ""  # 文档构建目录

    def to_dict(self) -> Dict[str, Any]:
        return {
            'success': self.success,
            'ttl_content': self.ttl_content,
            'stats': {
                'entities': self.entities_count,
                'relations': self.relations_count,
                'links': self.links_count
            },
            'errors': self.errors,
            'warnings': self.warnings,
            'duration_ms': self.duration_ms,
            'build_dir': self.build_dir
        }

    def summary(self) -> str:
        status = "✅ 成功" if self.success else "❌ 失败"
        lines = [
            "本体构建结果",
            f"状态: {status}",
            f"耗时: {self.duration_ms}ms",
            f"统计:",
            f"  - 实体: {self.entities_count}",
            f"  - 关系: {self.relations_count}",
            f"  - 链接: {self.links_count}"
        ]
        if self.build_dir:
            lines.append(f"文档目录: {self.build_dir}")
        if self.errors:
            lines.append(f"错误: {len(self.errors)}")
        if self.warnings:
            lines.append(f"警告: {len(self.warnings)}")
        return "\n".join(lines)


class OntologyClient:
    """
    Ontology 项目客户端

    提供与 ontology 项目交互的完整功能：
    - build_code_ontology(): 调用 ontology 服务构建代码本体（仅生成 TTL）
    - build_and_import_code_ontology(): 构建并导入到 Neo4j（使用 Pipeline）
    - build_sdd_ontology(): 调用 ontology 服务构建 SDD 本体
    - upload_ttl(): 上传 TTL 文件
    - query(): 执行 Neo4j 查询
    """

    def __init__(self, config: OntologyConfig = None):
        """
        初始化客户端

        Args:
            config: 配置对象，如果不提供则使用默认配置
        """
        self.config = config or get_config()
        self._neo4j_driver = None
        self._code_builder = None
        self._build_pipeline = None

    def _get_code_builder(self):
        """
        获取 CodeOntologyBuilder 实例（懒加载）

        Returns:
            CodeOntologyBuilder 实例
        """
        if self._code_builder is None:
            # 添加 ontology 项目到 Python 路径
            ontology_path = self.config.ontology_path
            if ontology_path and ontology_path not in sys.path:
                sys.path.insert(0, ontology_path)

            try:
                from ontology_build import CodeOntologyBuilder, LLMPluginManager, get_settings

                # 使用 ontology 服务内部的配置初始化 LLM 管理器
                settings = get_settings()
                llm_manager = LLMPluginManager(settings)
                self._code_builder = CodeOntologyBuilder(llm_manager=llm_manager)
                logger.info("CodeOntologyBuilder 初始化成功")

            except ImportError as e:
                logger.error(f"无法导入 ontology_build 模块: {e}")
                logger.error(f"请确保 ontology 项目路径正确: {ontology_path}")
                raise

        return self._code_builder

    def _get_build_pipeline(self):
        """
        获取 CodeOntologyBuildPipeline 实例（懒加载）

        Pipeline 会使用 ontology 服务内部的配置，包括 Neo4j 连接信息。

        Returns:
            CodeOntologyBuildPipeline 实例
        """
        if self._build_pipeline is None:
            # 添加 ontology 项目到 Python 路径
            ontology_path = self.config.ontology_path
            if ontology_path and ontology_path not in sys.path:
                sys.path.insert(0, ontology_path)

            try:
                from ontology_build.run_code_ontology_build import CodeOntologyBuildPipeline

                # Pipeline 内部会使用 ontology 服务的配置
                self._build_pipeline = CodeOntologyBuildPipeline()
                logger.info("CodeOntologyBuildPipeline 初始化成功")

            except ImportError as e:
                logger.error(f"无法导入 CodeOntologyBuildPipeline: {e}")
                logger.error(f"请确保 ontology 项目路径正确: {ontology_path}")
                raise

        return self._build_pipeline

    def _get_document_kg_pipeline(self, database: str = "ontologydevos"):
        """
        获取 DocumentKGPipeline 实例（懒加载）

        使用 ontology 项目的 DocumentKGPipeline 进行完整的文档到知识图谱构建。

        Args:
            database: Neo4j 数据库名称

        Returns:
            DocumentKGPipeline 实例
        """
        # 添加 ontology 项目到 Python 路径
        ontology_path = self.config.ontology_path
        if ontology_path and ontology_path not in sys.path:
            sys.path.insert(0, ontology_path)

        # 加载 ontology 项目的 .env 文件
        env_path = Path(ontology_path) / "ontology_build" / ".env"
        if env_path.exists():
            try:
                from dotenv import load_dotenv
                load_dotenv(env_path, override=True)
                logger.info(f"已加载 .env 文件: {env_path}")
            except ImportError:
                logger.warning("dotenv 未安装，跳过 .env 加载")

        try:
            from ontology_build.document_kg.pipeline import DocumentKGPipeline
            from ontology_build.llm_plugins.base import create_llm_client
            import os

            # 从环境变量获取配置（优先使用 .env 中的配置）
            neo4j_uri = os.getenv("ONTOLOGY_NEO4J_URI", "bolt://localhost:7687")
            neo4j_user = os.getenv("ONTOLOGY_NEO4J_USER", "neo4j")
            neo4j_password = os.getenv("ONTOLOGY_NEO4J_PASSWORD", "")

            llm_provider = os.getenv("ONTOLOGY_LLM_PROVIDER", "qwen")
            llm_api_key = os.getenv("ONTOLOGY_LLM_API_KEY", "")
            llm_model = os.getenv("ONTOLOGY_LLM_MODEL", "qwen-plus")

            # 创建 LLM 客户端
            llm_client = None
            if llm_api_key:
                llm_client = create_llm_client(
                    provider=llm_provider,
                    api_key=llm_api_key,
                    model=llm_model
                )
                logger.info(f"LLM 客户端已创建: {llm_provider}/{llm_model}")

            # 创建 Pipeline
            pipeline = DocumentKGPipeline(
                llm_client=llm_client,
                neo4j_uri=neo4j_uri,
                neo4j_user=neo4j_user,
                neo4j_password=neo4j_password,
                doc_database=database,
                merged_database=database
            )

            logger.info(f"DocumentKGPipeline 初始化成功，目标数据库: {database}")
            return pipeline

        except ImportError as e:
            logger.error(f"无法导入 DocumentKGPipeline: {e}")
            logger.error(f"请确保 ontology 项目路径正确: {ontology_path}")
            raise

    def build_code_ontology(
        self,
        documents: List[str],
        prompt: Optional[str] = None,
        domain: str = "rd",
        schema_ttl: Optional[str] = None,
        import_to_neo4j: bool = False
    ) -> BuildResult:
        """
        调用 ontology 服务构建代码本体

        注意：如果需要导入 Neo4j，建议使用 build_and_import_code_ontology() 方法，
        它使用 Pipeline 进行完整的构建和导入流程。

        Args:
            documents: 代码描述文档列表
            prompt: 自定义 prompt（可选）
            domain: 本体域名，默认 "rd"
            schema_ttl: 模式 TTL（可选，作为参考）
            import_to_neo4j: 是否导入 Neo4j（建议使用 build_and_import_code_ontology）

        Returns:
            BuildResult: 构建结果
        """
        try:
            builder = self._get_code_builder()

            # 调用 ontology 服务
            result = builder.build_from_documents(
                documents=documents,
                prompt=prompt,
                domain=domain,
                schema_ttl=schema_ttl,
                import_to_neo4j=import_to_neo4j
            )

            # 转换结果
            return BuildResult(
                success=result.success,
                ttl_content=result.ttl_content,
                entities_count=result.entities_count,
                relations_count=result.relations_count,
                errors=result.errors,
                warnings=result.warnings,
                duration_ms=result.duration_ms
            )

        except Exception as e:
            logger.error(f"构建代码本体失败: {e}")
            return BuildResult(
                success=False,
                errors=[str(e)]
            )

    def build_and_import_code_ontology(
        self,
        documents: List[str],
        output_dir: Optional[str] = None,
        domain: str = "rd",
        openspec_docs: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        构建代码本体并导入到 Neo4j（使用 Pipeline）

        这是推荐的方法，使用 CodeOntologyBuildPipeline 进行完整的构建流程：
        1. 加载文档
        2. 使用 LLM 提取实体和关系
        3. 生成 TTL 文件（版本化保存）
        4. 使用 TTLParser 解析
        5. 使用 V6Neo4jImporter 导入 Neo4j（MERGE 语义，支持增量更新）

        所有配置（LLM、Neo4j 等）都使用 ontology 服务内部的配置。

        Args:
            documents: 代码描述文档列表
            output_dir: 输出目录（可选，默认使用 ontology 服务的输出目录）
            domain: 本体域名，默认 "rd"
            openspec_docs: OpenSpec 文档（可选，用于 SDD 链接）

        Returns:
            构建结果统计，包含各阶段的详细信息
        """
        try:
            pipeline = self._get_build_pipeline()

            # 确定输出目录
            if output_dir is None:
                output_dir = str(self.config.get_ttl_path())

            # 将文档列表保存到临时目录
            import tempfile
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)

                # 保存文档到临时文件
                for i, doc in enumerate(documents):
                    doc_file = temp_path / f"doc_{i:03d}.md"
                    doc_file.write_text(doc, encoding='utf-8')

                # 运行 Pipeline
                result = pipeline.run(
                    input_dir=temp_path,
                    output_dir=Path(output_dir),
                    domain=domain,
                    import_to_neo4j=True,  # 使用 Pipeline 导入
                    openspec_docs=openspec_docs
                )

            return result

        except Exception as e:
            logger.error(f"构建并导入代码本体失败: {e}")
            return {
                'success': False,
                'errors': [str(e)]
            }

    def build_sdd_ontology(
        self,
        openspec_docs: Dict[str, str],
        code_elements: List[Dict[str, Any]],
        prompt: Optional[str] = None,
        import_to_neo4j: bool = False
    ) -> BuildResult:
        """
        调用 ontology 服务构建 SDD 本体（需求-代码链接）

        Args:
            openspec_docs: OpenSpec 文档 {"proposal.md": "...", "design.md": "..."}
            code_elements: 代码元素列表
            prompt: 自定义 prompt（可选）
            import_to_neo4j: 是否导入 Neo4j

        Returns:
            BuildResult: 构建结果
        """
        try:
            builder = self._get_code_builder()

            # 调用 ontology 服务
            result = builder.build_sdd_ontology(
                openspec_docs=openspec_docs,
                code_elements=code_elements,
                prompt=prompt,
                import_to_neo4j=import_to_neo4j
            )

            # 转换结果
            return BuildResult(
                success=result.success,
                ttl_content=result.ttl_content,
                links_count=result.links_count,
                errors=result.errors,
                warnings=result.warnings,
                duration_ms=result.duration_ms
            )

        except Exception as e:
            logger.error(f"构建 SDD 本体失败: {e}")
            return BuildResult(
                success=False,
                errors=[str(e)]
            )

    def build_and_import_from_docs_dir(
        self,
        docs_dir: str,
        database: str = "ontologydevos",
        clear_existing: bool = False
    ) -> BuildResult:
        """
        从文档目录构建代码本体并导入 Neo4j（在 ontology 项目中执行）

        这是推荐的完整流程方法：
        1. 将文档目录复制到 ontology 项目
        2. 在 ontology 项目中执行 DocumentKGPipeline
        3. 使用 LLM 抽取三元组
        4. 导入 Neo4j（MERGE 语义，支持增量更新）

        Args:
            docs_dir: 文档目录路径（由 DocumentWriter 生成）
            database: Neo4j 数据库名称，默认 "ontologydevos"
            clear_existing: 是否清空现有数据

        Returns:
            BuildResult: 构建结果
        """
        import time
        import shutil
        import subprocess
        start_time = time.time()

        try:
            ontology_path = self.config.ontology_path
            if not ontology_path:
                raise ValueError("Ontology 项目路径未配置")

            # 将文档目录复制到 ontology 项目的 input 目录
            docs_dir_path = Path(docs_dir)
            if not docs_dir_path.exists():
                raise ValueError(f"文档目录不存在: {docs_dir}")

            # 目标目录：ontology/ontology_build/input/code_docs/<project_name>
            input_dir = Path(ontology_path) / "ontology_build" / "input" / "code_docs"
            input_dir.mkdir(parents=True, exist_ok=True)

            # 复制文档目录
            target_dir = input_dir / docs_dir_path.name
            if target_dir.exists():
                shutil.rmtree(target_dir)
            shutil.copytree(docs_dir_path, target_dir)
            logger.info(f"文档已复制到: {target_dir}")

            # 在 ontology 项目中执行构建脚本
            build_script = Path(ontology_path) / "ontology_build" / "run_document_kg_build.py"

            if not build_script.exists():
                # 如果脚本不存在，创建一个
                self._create_build_script(build_script)

            # 使用 ontology 项目的 venv Python
            ontology_venv_python = Path(ontology_path) / "ontology_build" / "venv" / "bin" / "python"
            if not ontology_venv_python.exists():
                # 尝试 Windows 路径
                ontology_venv_python = Path(ontology_path) / "ontology_build" / "venv" / "Scripts" / "python.exe"
            if not ontology_venv_python.exists():
                raise ValueError(f"找不到 ontology 项目的 venv Python: {ontology_venv_python}")

            # 执行构建
            logger.info(f"在 ontology 项目中执行构建...")
            logger.info(f"使用 Python: {ontology_venv_python}")
            result = subprocess.run(
                [
                    str(ontology_venv_python),
                    str(build_script),
                    "--input-dir", str(target_dir),
                    "--database", database,
                ] + (["--clear-existing"] if clear_existing else []),
                cwd=str(Path(ontology_path) / "ontology_build"),
                capture_output=True,
                text=True,
                timeout=600  # 10 分钟超时
            )

            # 解析输出
            duration_ms = int((time.time() - start_time) * 1000)

            if result.returncode == 0:
                # 尝试从输出中解析统计信息
                entities_count = 0
                relations_count = 0
                for line in result.stdout.split('\n'):
                    if '创建实体' in line or 'entities_created' in line:
                        try:
                            entities_count = int(''.join(filter(str.isdigit, line.split(':')[-1])))
                        except:
                            pass
                    if '创建关系' in line or 'relationships_created' in line:
                        try:
                            relations_count = int(''.join(filter(str.isdigit, line.split(':')[-1])))
                        except:
                            pass

                return BuildResult(
                    success=True,
                    entities_count=entities_count,
                    relations_count=relations_count,
                    duration_ms=duration_ms,
                    build_dir=str(target_dir)
                )
            else:
                return BuildResult(
                    success=False,
                    errors=[result.stderr or result.stdout or "构建失败"],
                    duration_ms=duration_ms,
                    build_dir=str(target_dir)
                )

        except subprocess.TimeoutExpired:
            return BuildResult(
                success=False,
                errors=["构建超时（超过 10 分钟）"],
                duration_ms=int((time.time() - start_time) * 1000),
                build_dir=docs_dir
            )
        except Exception as e:
            logger.error(f"从文档目录构建本体失败: {e}")
            import traceback
            traceback.print_exc()
            return BuildResult(
                success=False,
                errors=[str(e)],
                build_dir=docs_dir
            )

    def _create_build_script(self, script_path: Path) -> None:
        """
        创建构建脚本

        Args:
            script_path: 脚本路径
        """
        script_content = '''#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
文档知识图谱构建脚本

从文档目录构建知识图谱并导入 Neo4j。
"""

import argparse
import logging
import os
import sys
from pathlib import Path

# 加载 .env 文件
from dotenv import load_dotenv
load_dotenv()

from document_kg.pipeline import DocumentKGPipeline
from llm_plugins.base import create_llm_client

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description='文档知识图谱构建')
    parser.add_argument('--input-dir', required=True, help='输入文档目录')
    parser.add_argument('--database', default='ontologydevos', help='Neo4j 数据库名称')
    parser.add_argument('--clear-existing', action='store_true', help='清空现有数据')
    args = parser.parse_args()

    # 从环境变量获取配置
    neo4j_uri = os.getenv("ONTOLOGY_NEO4J_URI", "bolt://localhost:7687")
    neo4j_user = os.getenv("ONTOLOGY_NEO4J_USER", "neo4j")
    neo4j_password = os.getenv("ONTOLOGY_NEO4J_PASSWORD", "")

    llm_provider = os.getenv("ONTOLOGY_LLM_PROVIDER", "qwen")
    llm_api_key = os.getenv("ONTOLOGY_LLM_API_KEY", "")
    llm_model = os.getenv("ONTOLOGY_LLM_MODEL", "qwen-plus")

    # 创建 LLM 客户端
    llm_client = None
    if llm_api_key:
        llm_client = create_llm_client(
            provider=llm_provider,
            api_key=llm_api_key,
            model=llm_model
        )
        logger.info(f"LLM 客户端已创建: {llm_provider}/{llm_model}")

    # 创建 Pipeline
    pipeline = DocumentKGPipeline(
        llm_client=llm_client,
        neo4j_uri=neo4j_uri,
        neo4j_user=neo4j_user,
        neo4j_password=neo4j_password,
        doc_database=args.database,
        merged_database=args.database
    )

    # 执行构建
    logger.info(f"开始从 {args.input_dir} 构建知识图谱...")
    result = pipeline.run_document_only(
        document_dirs=[args.input_dir],
        clear_existing=args.clear_existing
    )

    # 输出结果
    print(result.summary())
    print(f"entities_created: {result.entities_created}")
    print(f"relationships_created: {result.relationships_created}")

    pipeline.close()

    return 0 if result.success else 1


if __name__ == '__main__':
    sys.exit(main())
'''
        script_path.write_text(script_content, encoding='utf-8')
        script_path.chmod(0o755)
        logger.info(f"已创建构建脚本: {script_path}")

    def build_complete_code_ontology(
        self,
        project_path: str,
        project_name: Optional[str] = None,
        database: str = "ontologydevos",
        save_docs: bool = True,
        enable_llm_enhance: bool = False,
        clear_existing: bool = False,
        incremental: bool = True,
        include_wiki_docs: bool = True
    ) -> BuildResult:
        """
        完整的代码本体构建流程（推荐使用）

        这是最完整的方法，执行以下步骤：
        1. 解析项目代码
        2. 检测文件变更（增量模式）
        3. 生成带 frontmatter 的文档（可选 LLM 增强）
        4. 保存文档到磁盘
        4.5. 整合项目 wiki 文档（.qoder/repowiki 等）
        5. 使用 DocumentKGPipeline 构建本体
        6. 导入 Neo4j

        Args:
            project_path: 项目路径
            project_name: 项目名称（可选，默认使用目录名）
            database: Neo4j 数据库名称
            save_docs: 是否保存文档到磁盘
            enable_llm_enhance: 是否启用 LLM 增强文档生成
            clear_existing: 是否清空现有数据
            incremental: 是否启用增量构建（默认 True）
            include_wiki_docs: 是否包含项目 wiki 文档（.qoder/repowiki 等，默认 True）

        Returns:
            BuildResult: 构建结果
        """
        import time
        from pathlib import Path as PathLib
        start_time = time.time()

        try:
            # 1. 解析项目
            logger.info(f"正在解析项目: {project_path}")

            # 导入 code_processor
            from code_processor import (
                ParserFactory, DocumentGenerator, DocumentWriter,
                IncrementalProcessor
            )

            parser = ParserFactory.create_parser(project_path)
            project_info = parser.parse_project()

            if not project_name:
                project_name = PathLib(project_path).name

            logger.info(f"解析完成: {len(project_info.elements)} 个元素, {len(project_info.relations)} 个关系")

            # 2. 增量检测
            elements_to_process = project_info.elements
            is_incremental = False

            if incremental and not clear_existing:
                incremental_processor = IncrementalProcessor(project_path)

                # 获取所有源文件
                source_files = []
                for element in project_info.elements:
                    if element.file_path:
                        file_path = PathLib(element.file_path)
                        if file_path.exists() and file_path not in source_files:
                            source_files.append(file_path)

                # 检测变更
                changes = incremental_processor.detect_changes(source_files)

                if incremental_processor.has_metadata():
                    # 非首次构建，只处理变更的文件
                    changed_elements = incremental_processor.get_changed_elements(
                        project_info.elements, changes
                    )
                    elements_to_process = changed_elements['new'] + changed_elements['modified']
                    is_incremental = True

                    if not elements_to_process:
                        logger.info("没有检测到变更，跳过构建")
                        return BuildResult(
                            success=True,
                            entities_count=0,
                            relations_count=0,
                            duration_ms=int((time.time() - start_time) * 1000),
                            warnings=["没有检测到变更，跳过构建"]
                        )

                    logger.info(
                        f"增量构建: 处理 {len(elements_to_process)} 个变更元素 "
                        f"(新增: {len(changed_elements['new'])}, "
                        f"修改: {len(changed_elements['modified'])})"
                    )

            # 3. 生成文档
            logger.info("正在生成文档...")
            generator = DocumentGenerator(
                project_name=project_name,
                enable_llm=enable_llm_enhance
            )

            # 创建临时 ProjectInfo 只包含需要处理的元素
            if is_incremental:
                from code_processor import ProjectInfo, LanguageType
                temp_project = ProjectInfo(project_path, project_info.language)
                for elem in elements_to_process:
                    temp_project.add_element(elem)
                documents = generator.generate_all_documents(
                    temp_project,
                    return_document_objects=True
                )
            else:
                documents = generator.generate_all_documents(
                    project_info,
                    return_document_objects=True
                )

            logger.info(f"生成了 {len(documents)} 个文档")

            # 4. 保存文档
            if save_docs:
                logger.info("正在保存文档...")
                writer = DocumentWriter()
                build_dir = writer.save(project_name, documents)
                logger.info(f"文档已保存到: {build_dir}")
            else:
                # 使用临时目录
                import tempfile
                temp_dir = tempfile.mkdtemp(prefix="code_docs_")
                writer = DocumentWriter(base_dir=temp_dir)
                build_dir = writer.save(project_name, documents)

            # 4.5. 整合项目 wiki 文档
            if include_wiki_docs:
                wiki_docs_count = self._copy_wiki_docs_to_build_dir(
                    project_path=project_path,
                    build_dir=build_dir
                )
                if wiki_docs_count > 0:
                    logger.info(f"已整合 {wiki_docs_count} 个 wiki 文档到构建目录")

            # 5. 使用 Pipeline 构建本体
            logger.info("正在构建本体...")

            # 增量模式不清空现有数据
            should_clear = clear_existing and not is_incremental

            result = self.build_and_import_from_docs_dir(
                docs_dir=build_dir,
                database=database,
                clear_existing=should_clear
            )

            # 更新结果
            result.duration_ms = int((time.time() - start_time) * 1000)
            result.build_dir = build_dir

            if is_incremental:
                result.warnings.append(f"增量构建: 处理了 {len(elements_to_process)} 个变更元素")

            # 6. 创建检索索引（全文索引和向量索引）
            if result.success:
                logger.info("正在创建检索索引...")
                index_result = self.setup_retrieval_indexes(database)
                if index_result.get('errors'):
                    result.warnings.extend(index_result['errors'])
                else:
                    logger.info(f"检索索引创建完成: {index_result}")

            return result

        except Exception as e:
            logger.error(f"完整代码本体构建失败: {e}")
            import traceback
            traceback.print_exc()
            return BuildResult(
                success=False,
                errors=[str(e)],
                duration_ms=int((time.time() - start_time) * 1000)
            )

    def setup_retrieval_indexes(
        self,
        database: str = "ontologydevos",
        embedding_dim: int = 1024
    ) -> Dict[str, Any]:
        """
        创建检索所需的索引（全文索引和向量索引）

        在构建完成后调用此方法，确保 MCP 插件的检索功能可用。

        创建的索引：
        - node_name_fulltext: 全文索引，用于关键词搜索
        - node_embedding_index: 向量索引，用于语义搜索（Entity 节点）
        - class_embedding_idx: 向量索引（Class 节点）

        Args:
            database: Neo4j 数据库名称
            embedding_dim: 向量维度，默认 1024

        Returns:
            创建结果，包含成功和失败的索引列表
        """
        result = {
            'fulltext_indexes': [],
            'vector_indexes': [],
            'errors': []
        }

        if not self.config.neo4j_uri:
            result['errors'].append("Neo4j 未配置")
            return result

        try:
            from neo4j import GraphDatabase

            if self._neo4j_driver is None:
                self._neo4j_driver = GraphDatabase.driver(
                    self.config.neo4j_uri,
                    auth=(self.config.neo4j_user, self.config.neo4j_password)
                )

            with self._neo4j_driver.session(database=database) as session:
                # 1. 创建全文索引
                fulltext_indexes = [
                    # 主全文索引 - 用于 HybridRetriever
                    ("node_name_fulltext", ["Entity", "Document", "Class"], ["name", "label", "title", "comment"]),
                ]

                for index_name, labels, properties in fulltext_indexes:
                    try:
                        # 先检查索引是否存在
                        check_result = session.run(
                            "SHOW INDEXES WHERE name = $name",
                            {"name": index_name}
                        )
                        if check_result.peek():
                            logger.info(f"全文索引已存在: {index_name}")
                            result['fulltext_indexes'].append(f"{index_name} (已存在)")
                            continue

                        # 创建全文索引
                        labels_str = "|".join(labels)
                        props_str = ", ".join([f"n.{p}" for p in properties])
                        cypher = f"""
                        CREATE FULLTEXT INDEX {index_name} IF NOT EXISTS
                        FOR (n:{labels_str})
                        ON EACH [{props_str}]
                        """
                        session.run(cypher)
                        logger.info(f"全文索引创建成功: {index_name}")
                        result['fulltext_indexes'].append(index_name)
                    except Exception as e:
                        error_msg = f"创建全文索引 {index_name} 失败: {e}"
                        logger.warning(error_msg)
                        result['errors'].append(error_msg)

                # 2. 创建向量索引
                vector_indexes = [
                    # SDK 期望的索引名称
                    ("node_embedding_index", "Entity", "embedding"),
                    ("class_embedding_idx", "Class", "embedding"),
                ]

                for index_name, label, property_name in vector_indexes:
                    try:
                        # 先检查索引是否存在
                        check_result = session.run(
                            "SHOW INDEXES WHERE name = $name",
                            {"name": index_name}
                        )
                        if check_result.peek():
                            logger.info(f"向量索引已存在: {index_name}")
                            result['vector_indexes'].append(f"{index_name} (已存在)")
                            continue

                        # 创建向量索引
                        cypher = f"""
                        CREATE VECTOR INDEX {index_name} IF NOT EXISTS
                        FOR (n:{label}) ON (n.{property_name})
                        OPTIONS {{
                            indexConfig: {{
                                `vector.dimensions`: {embedding_dim},
                                `vector.similarity_function`: 'cosine'
                            }}
                        }}
                        """
                        session.run(cypher)
                        logger.info(f"向量索引创建成功: {index_name}")
                        result['vector_indexes'].append(index_name)
                    except Exception as e:
                        error_msg = f"创建向量索引 {index_name} 失败: {e}"
                        logger.warning(error_msg)
                        result['errors'].append(error_msg)

                # 3. 创建基础属性索引（加速查询）
                basic_indexes = [
                    ("Entity", "name"),
                    ("Entity", "type"),
                    ("Document", "title"),
                    ("Class", "name"),
                ]

                for label, prop in basic_indexes:
                    try:
                        index_name = f"idx_{label.lower()}_{prop}"
                        session.run(
                            f"CREATE INDEX {index_name} IF NOT EXISTS FOR (n:{label}) ON (n.{prop})"
                        )
                    except Exception:
                        pass  # 忽略基础索引创建失败

            logger.info(f"检索索引设置完成: {len(result['fulltext_indexes'])} 全文, {len(result['vector_indexes'])} 向量")

        except ImportError:
            result['errors'].append("neo4j 包未安装")
        except Exception as e:
            result['errors'].append(f"设置索引失败: {e}")

        return result

    def _copy_wiki_docs_to_build_dir(
        self,
        project_path: str,
        build_dir: str
    ) -> int:
        """
        复制项目 wiki 文档到构建目录

        支持以下 wiki 文档来源：
        - .qoder/repowiki: Qoder 生成的项目文档
        - docs/wiki: 项目自带的 wiki 文档
        - wiki/: 项目根目录的 wiki 文档

        Args:
            project_path: 项目路径
            build_dir: 构建目录路径

        Returns:
            复制的文档数量
        """
        import shutil
        from pathlib import Path as PathLib

        project_dir = PathLib(project_path)
        build_path = PathLib(build_dir)
        total_copied = 0

        # 定义 wiki 文档来源（按优先级）
        wiki_sources = [
            # Qoder 生成的 repowiki（中文版）
            (project_dir / ".qoder" / "repowiki" / "zh" / "content", "qoder_wiki"),
            # Qoder 生成的 repowiki（英文版）
            (project_dir / ".qoder" / "repowiki" / "en" / "content", "qoder_wiki_en"),
            # 项目 docs/wiki 目录
            (project_dir / "docs" / "wiki", "project_wiki"),
            # 项目根目录 wiki
            (project_dir / "wiki", "wiki"),
        ]

        for source_dir, target_name in wiki_sources:
            if source_dir.exists() and source_dir.is_dir():
                # 目标目录
                target_dir = build_path / target_name

                # 递归复制所有 .md 文件
                md_count = 0
                for md_file in source_dir.rglob("*.md"):
                    # 计算相对路径
                    rel_path = md_file.relative_to(source_dir)
                    target_file = target_dir / rel_path

                    # 创建目标目录
                    target_file.parent.mkdir(parents=True, exist_ok=True)

                    # 复制文件
                    shutil.copy2(md_file, target_file)
                    md_count += 1

                if md_count > 0:
                    logger.info(f"从 {source_dir.name} 复制了 {md_count} 个 wiki 文档到 {target_name}/")
                    total_copied += md_count

        return total_copied

    def upload_ttl(self, ttl_content: str, name: str = None, version: int = None) -> str:
        """
        上传 TTL 内容到 ontology 项目

        Args:
            ttl_content: TTL 内容
            name: 文件名（不含扩展名）
            version: 版本号

        Returns:
            保存的文件路径
        """
        if not self.config.ontology_path:
            raise ValueError("Ontology path not configured")

        ttl_dir = self.config.get_ttl_path()
        ttl_dir.mkdir(parents=True, exist_ok=True)

        # 生成文件名
        if name is None:
            name = self.config.domain
        if version is None:
            version = self._get_next_version(ttl_dir, name)

        filename = f"{name}_v{version}.ttl"
        output_path = ttl_dir / filename

        # 写入文件
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(ttl_content)

        logger.info(f"TTL 已上传到: {output_path}")
        return str(output_path)

    def _get_next_version(self, ttl_dir: Path, name: str) -> int:
        """获取下一个版本号"""
        import re

        pattern = re.compile(rf'{re.escape(name)}_v(\d+)\.ttl')
        max_version = 0

        for file in ttl_dir.glob(f"{name}_v*.ttl"):
            match = pattern.match(file.name)
            if match:
                version = int(match.group(1))
                max_version = max(max_version, version)

        return max_version + 1

    def list_ttl_files(self) -> List[Dict[str, Any]]:
        """列出 ontology 项目中的所有 TTL 文件"""
        if not self.config.ontology_path:
            return []

        ttl_dir = self.config.get_ttl_path()
        if not ttl_dir.exists():
            return []

        files = []
        for file in ttl_dir.glob("*.ttl"):
            stat = file.stat()
            files.append({
                'name': file.name,
                'path': str(file),
                'size': stat.st_size,
                'modified': datetime.fromtimestamp(stat.st_mtime).isoformat()
            })

        return sorted(files, key=lambda x: x['modified'], reverse=True)

    def query(self, cypher: str) -> List[Dict]:
        """
        执行 Cypher 查询

        Args:
            cypher: Cypher 查询语句

        Returns:
            查询结果列表
        """
        if not self.config.neo4j_uri:
            logger.warning("Neo4j 未配置，查询未执行")
            return []

        try:
            from neo4j import GraphDatabase

            if self._neo4j_driver is None:
                self._neo4j_driver = GraphDatabase.driver(
                    self.config.neo4j_uri,
                    auth=(self.config.neo4j_user, self.config.neo4j_password)
                )

            with self._neo4j_driver.session() as session:
                result = session.run(cypher)
                return [dict(record) for record in result]

        except ImportError:
            logger.error("neo4j 包未安装。请运行: pip install neo4j")
            return []
        except Exception as e:
            logger.error(f"查询失败: {e}")
            return []

    def search_code_by_requirement(self, requirement_name: str) -> List[Dict]:
        """
        按需求搜索代码元素

        Args:
            requirement_name: 需求名称或 ID

        Returns:
            匹配的代码元素列表
        """
        cypher = """
        MATCH (c:CodeElement)-[:implementsRequirement]->(r:Requirement)
        WHERE r.name CONTAINS $name OR r.changeId CONTAINS $name
        RETURN c.fullName as code, c.filePath as file, c.lineNumber as line, r.name as requirement
        """
        return self.query(cypher.replace('$name', f'"{requirement_name}"'))

    def search_tests_for_code(self, code_name: str) -> List[Dict]:
        """
        搜索代码的测试

        Args:
            code_name: 代码元素名称

        Returns:
            匹配的测试列表
        """
        cypher = """
        MATCH (t:Test)-[:testsCode]->(c:CodeElement)
        WHERE c.fullName CONTAINS $name OR c.name CONTAINS $name
        RETURN t.fullName as test, t.filePath as file, c.fullName as code
        """
        return self.query(cypher.replace('$name', f'"{code_name}"'))

    def analyze_change_impact(self, file_paths: List[str]) -> Dict[str, Any]:
        """
        分析变更影响

        Args:
            file_paths: 变更的文件路径列表

        Returns:
            影响分析结果
        """
        if not file_paths:
            return {'affected_requirements': [], 'affected_tests': []}

        # 构建文件路径条件
        conditions = ' OR '.join([f'c.filePath CONTAINS "{p}"' for p in file_paths])

        # 查找受影响的需求
        req_cypher = f"""
        MATCH (c:CodeElement)-[:implementsRequirement]->(r:Requirement)
        WHERE {conditions}
        RETURN DISTINCT r.name as requirement, r.changeId as changeId
        """

        # 查找受影响的测试
        test_cypher = f"""
        MATCH (t:Test)-[:testsCode]->(c:CodeElement)
        WHERE {conditions}
        RETURN DISTINCT t.fullName as test, t.filePath as testFile
        """

        return {
            'affected_requirements': self.query(req_cypher),
            'affected_tests': self.query(test_cypher)
        }

    def get_statistics(self) -> Dict[str, Any]:
        """获取本体统计信息"""
        stats = {
            'ttl_files': len(self.list_ttl_files()),
            'neo4j_connected': False,
            'elements': 0,
            'relations': 0,
            'requirements': 0
        }

        if self.config.neo4j_uri:
            try:
                # 统计节点数
                result = self.query("MATCH (n) RETURN count(n) as count")
                if result:
                    stats['elements'] = result[0].get('count', 0)

                # 统计关系数
                result = self.query("MATCH ()-[r]->() RETURN count(r) as count")
                if result:
                    stats['relations'] = result[0].get('count', 0)

                # 统计需求数
                result = self.query("MATCH (r:Requirement) RETURN count(r) as count")
                if result:
                    stats['requirements'] = result[0].get('count', 0)

                stats['neo4j_connected'] = True
            except Exception:
                pass

        return stats

    def close(self):
        """关闭连接"""
        if self._neo4j_driver:
            self._neo4j_driver.close()
            self._neo4j_driver = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
