# -*- coding: utf-8 -*-
"""
Code Ontology CLI

命令行工具，用于代码分析和本体构建。

支持的命令：
- analyze: 分析项目并提取代码元素
- docs: 生成代码描述文档
- build: 调用 ontology 服务构建本体
- info: 显示支持的语言和功能
"""

import argparse
import json
import logging
import sys
from pathlib import Path

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from code_processor import (
    ParserFactory, MultiLanguageProjectAnalyzer,
    LanguageType, DocumentGenerator
)

logger = logging.getLogger(__name__)


def setup_logging(verbose: bool = False):
    """设置日志配置"""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def cmd_analyze(args):
    """analyze 命令：解析项目并输出结果"""
    project_path = Path(args.project_path)

    if not project_path.exists():
        print(f"错误: 项目路径不存在: {project_path}")
        return 1

    # 确定语言
    language = None
    if args.language:
        try:
            language = LanguageType(args.language)
        except ValueError:
            print(f"错误: 未知语言: {args.language}")
            print(f"支持的语言: {[l.value for l in LanguageType if l != LanguageType.UNKNOWN]}")
            return 1

    try:
        if args.mixed:
            # 多语言分析
            analyzer = MultiLanguageProjectAnalyzer(str(project_path))
            results = analyzer.analyze_all_languages()
            overview = analyzer.get_project_overview()

            print(f"\n项目分析完成")
            print(f"============")
            print(f"语言数量: {overview['total_languages']}")
            print(f"元素总数: {overview['total_elements']}")
            print(f"关系总数: {overview['total_relations']}")
            print(f"文件总数: {overview['total_files']}")

            for lang_info in overview['languages']:
                print(f"\n  {lang_info['language']}:")
                print(f"    元素: {lang_info['elements']}")
                print(f"    关系: {lang_info['relations']}")
                print(f"    文件: {lang_info['files']}")

            if args.output:
                analyzer.save_combined_results(args.output)
                print(f"\n结果已保存到: {args.output}")

        else:
            # 单语言分析
            parser = ParserFactory.create_parser(str(project_path), language)
            project_info = parser.parse_project()

            stats = project_info.statistics
            print(f"\n项目分析完成")
            print(f"============")
            print(f"语言: {project_info.language.value}")
            print(f"元素总数: {stats.get('total_elements', 0)}")
            print(f"关系总数: {stats.get('total_relations', 0)}")
            print(f"文件总数: {stats.get('total_files', 0)}")
            print(f"包数量: {stats.get('packages_count', 0)}")

            if stats.get('element_types'):
                print(f"\n元素类型:")
                for etype, count in stats['element_types'].items():
                    print(f"  {etype}: {count}")

            if args.output:
                with open(args.output, 'w', encoding='utf-8') as f:
                    json.dump(project_info.to_dict(), f, ensure_ascii=False, indent=2)
                print(f"\n结果已保存到: {args.output}")

        return 0

    except Exception as e:
        print(f"错误: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


def cmd_docs(args):
    """docs 命令：生成代码描述文档"""
    project_path = Path(args.project_path)

    if not project_path.exists():
        print(f"错误: 项目路径不存在: {project_path}")
        return 1

    try:
        # 解析项目
        parser = ParserFactory.create_parser(str(project_path))
        project_info = parser.parse_project()

        # 生成文档
        output_dir = args.output or "output/documents"
        generator = DocumentGenerator(output_dir)
        documents = generator.generate_all_documents(project_info)

        print(f"\n文档生成完成")
        print(f"============")
        print(f"生成文档数: {len(documents)}")
        print(f"输出目录: {output_dir}")

        stats = generator.get_stats()
        print(f"\n统计:")
        print(f"  类: {stats['total_classes']}")
        print(f"  接口: {stats['total_interfaces']}")
        print(f"  方法: {stats['total_methods']}")
        print(f"  函数: {stats['total_functions']}")

        if args.save:
            saved_paths = generator.save_documents(documents, prefix=args.prefix or "doc")
            print(f"\n已保存 {len(saved_paths)} 个文档文件")

        return 0

    except Exception as e:
        print(f"错误: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


def cmd_build(args):
    """build 命令：调用 ontology 服务构建本体"""
    project_path = Path(args.project_path)

    if not project_path.exists():
        print(f"错误: 项目路径不存在: {project_path}")
        return 1

    try:
        # 导入 ontology_client
        from ontology_client import OntologyClient
        from ontology_client.config import get_config

        # 加载 ontology 项目的 .env 文件
        config = get_config()
        if config.ontology_path:
            env_path = Path(config.ontology_path) / "ontology_build" / ".env"
            if env_path.exists():
                try:
                    from dotenv import load_dotenv
                    load_dotenv(env_path)
                except ImportError:
                    pass  # dotenv 未安装，跳过

        # 创建客户端
        client = OntologyClient()

        # 判断使用哪种构建方式
        if args.use_pipeline:
            # 使用完整 Pipeline 流程（推荐）
            print("正在使用完整 Pipeline 构建本体...")

            # 增量构建选项
            incremental = not args.full_rebuild

            result = client.build_complete_code_ontology(
                project_path=str(project_path),
                project_name=args.project_name,
                database=args.database or "ontologydevos",
                save_docs=args.save_docs,
                enable_llm_enhance=args.llm_enhance,
                clear_existing=args.clear_existing,
                incremental=incremental,
                include_wiki_docs=args.include_wiki
            )

            print(f"\n本体构建完成")
            print(f"============")
            print(result.summary())

            if result.success and args.output:
                # 如果指定了输出文件，复制 TTL
                print(f"\n文档目录: {result.build_dir}")

            return 0 if result.success else 1

        else:
            # 使用旧的构建方式（兼容）
            print("正在解析项目...")
            parser = ParserFactory.create_parser(str(project_path))
            project_info = parser.parse_project()

            print("正在生成文档...")
            generator = DocumentGenerator()
            documents = generator.generate_all_documents(project_info)

            print(f"生成了 {len(documents)} 个文档")

            print("正在调用 ontology 服务构建本体...")

            # 读取 schema TTL（如果指定）
            schema_ttl = None
            if args.schema:
                schema_path = Path(args.schema)
                if schema_path.exists():
                    schema_ttl = schema_path.read_text(encoding='utf-8')

            result = client.build_code_ontology(
                documents=documents,
                domain=args.domain or "rd",
                schema_ttl=schema_ttl,
                import_to_neo4j=args.import_neo4j
            )

            print(f"\n本体构建完成")
            print(f"============")
            print(result.summary())

            if result.success and args.output:
                with open(args.output, 'w', encoding='utf-8') as f:
                    f.write(result.ttl_content)
                print(f"\nTTL 已保存到: {args.output}")

            return 0 if result.success else 1

    except ImportError as e:
        print(f"错误: 无法导入 ontology_client: {e}")
        print("请确保 ontology 项目路径已正确配置")
        return 1
    except Exception as e:
        print(f"错误: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


def cmd_info(args):
    """info 命令：显示支持的语言和功能"""
    print("Code Ontology CLI")
    print("=================")
    print()
    print("支持的语言:")
    for lang in ParserFactory.get_supported_languages():
        print(f"  - {lang.value}")
    print()
    print("命令:")
    print("  analyze  - 分析项目并提取代码元素")
    print("  docs     - 生成代码描述文档")
    print("  build    - 调用 ontology 服务构建本体")
    print("  info     - 显示此信息")
    print()
    print("示例:")
    print("  # 分析项目")
    print("  python -m code_processor.cli analyze /path/to/project")
    print("  python -m code_processor.cli analyze /path/to/project --output result.json")
    print()
    print("  # 生成文档")
    print("  python -m code_processor.cli docs /path/to/project --output docs/")
    print()
    print("  # 构建本体（调用 ontology 服务）")
    print("  python -m code_processor.cli build /path/to/project --output ontology.ttl")
    print("  python -m code_processor.cli build /path/to/project --import-neo4j")
    print()
    print("  # 多语言项目")
    print("  python -m code_processor.cli analyze /path/to/project --mixed")

    return 0


def main():
    """主入口"""
    parser = argparse.ArgumentParser(
        description='Code Ontology CLI - 分析代码并构建 R&D 本体',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument('-v', '--verbose', action='store_true',
                       help='启用详细输出')

    subparsers = parser.add_subparsers(dest='command', help='可用命令')

    # analyze 命令
    analyze_parser = subparsers.add_parser('analyze', help='分析项目')
    analyze_parser.add_argument('project_path', help='项目目录路径')
    analyze_parser.add_argument('-l', '--language', help='强制指定语言 (java, python, javascript, typescript)')
    analyze_parser.add_argument('-o', '--output', help='输出文件路径')
    analyze_parser.add_argument('--mixed', action='store_true',
                               help='作为多语言项目分析')
    analyze_parser.set_defaults(func=cmd_analyze)

    # docs 命令
    docs_parser = subparsers.add_parser('docs', help='生成代码描述文档')
    docs_parser.add_argument('project_path', help='项目目录路径')
    docs_parser.add_argument('-o', '--output', help='输出目录路径')
    docs_parser.add_argument('--save', action='store_true',
                            help='保存文档到文件')
    docs_parser.add_argument('--prefix', default='doc',
                            help='文档文件名前缀 (默认: doc)')
    docs_parser.set_defaults(func=cmd_docs)

    # build 命令
    build_parser = subparsers.add_parser('build', help='调用 ontology 服务构建本体')
    build_parser.add_argument('project_path', help='项目目录路径')
    build_parser.add_argument('-o', '--output', help='输出 TTL 文件路径')
    build_parser.add_argument('-d', '--domain', default='rd',
                             help='本体域名 (默认: rd)')
    build_parser.add_argument('--schema', help='模式 TTL 文件路径')
    build_parser.add_argument('--import-neo4j', action='store_true',
                             help='导入到 Neo4j（旧方式）')
    # 新增选项
    build_parser.add_argument('--use-pipeline', action='store_true', default=True,
                             help='使用完整 Pipeline 构建（推荐，默认启用）')
    build_parser.add_argument('--no-pipeline', action='store_false', dest='use_pipeline',
                             help='不使用 Pipeline，使用旧方式构建')
    build_parser.add_argument('--project-name', help='项目名称（默认使用目录名）')
    build_parser.add_argument('--database', default='ontologydevos',
                             help='Neo4j 数据库名称 (默认: ontologydevos)')
    build_parser.add_argument('--save-docs', action='store_true', default=True,
                             help='保存文档到磁盘（默认启用）')
    build_parser.add_argument('--no-save-docs', action='store_false', dest='save_docs',
                             help='不保存文档到磁盘')
    build_parser.add_argument('--llm-enhance', action='store_true',
                             help='启用 LLM 增强文档生成')
    build_parser.add_argument('--clear-existing', action='store_true',
                             help='清空现有数据后再导入')
    build_parser.add_argument('--full-rebuild', action='store_true',
                             help='强制全量重建（禁用增量构建）')
    build_parser.add_argument('--include-wiki', action='store_true', default=True,
                             help='包含项目 wiki 文档（.qoder/repowiki 等，默认启用）')
    build_parser.add_argument('--no-wiki', action='store_false', dest='include_wiki',
                             help='不包含 wiki 文档')
    build_parser.set_defaults(func=cmd_build)

    # info 命令
    info_parser = subparsers.add_parser('info', help='显示信息')
    info_parser.set_defaults(func=cmd_info)

    args = parser.parse_args()

    setup_logging(args.verbose)

    if args.command is None:
        parser.print_help()
        return 0

    return args.func(args)


if __name__ == '__main__':
    sys.exit(main())
