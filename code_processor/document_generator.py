# -*- coding: utf-8 -*-
"""
Document Generator

将代码分析结果转换为描述文档，用于 ontology 服务的本体构建输入。
支持 LLM 增强的业务意图描述生成。
"""

import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Union

from .base_parser import (
    CodeElement, CodeRelation, ProjectInfo,
    ElementType, RelationType, LanguageType
)
from .nlp_generator import NLPGenerator
from .document_writer import Document, DocumentWriter, generate_element_id

logger = logging.getLogger(__name__)


class DocumentGenerator:
    """
    文档生成器

    将代码分析结果（CodeElement、CodeRelation、ProjectInfo）转换为
    自然语言描述文档，用于 ontology 服务的 LLM 辅助本体构建。

    支持两种模式：
    1. 基础模式：生成结构化的 Markdown 文档
    2. LLM 增强模式：使用 NLPGenerator 生成业务意图描述
    """

    def __init__(
        self,
        output_dir: Optional[str] = None,
        llm_client: Optional[Any] = None,
        enable_llm: bool = False,
        project_name: Optional[str] = None
    ):
        """
        初始化文档生成器

        Args:
            output_dir: 可选的输出目录，如果指定则保存文档到文件
            llm_client: LLM 客户端实例（可选）
            enable_llm: 是否启用 LLM 增强
            project_name: 项目名称（用于生成 element_id）
        """
        self.output_dir = Path(output_dir) if output_dir else None
        if self.output_dir:
            self.output_dir.mkdir(parents=True, exist_ok=True)

        self.project_name = project_name
        self.nlp_generator = NLPGenerator(llm_client, enable_llm)
        self.enable_llm = enable_llm and llm_client is not None

        self.stats = {
            'total_classes': 0,
            'total_interfaces': 0,
            'total_methods': 0,
            'total_functions': 0,
            'total_fields': 0,
            'total_modules': 0,
            'documents_generated': 0
        }

    def generate_all_documents(
        self,
        project: ProjectInfo,
        return_document_objects: bool = False
    ) -> Union[List[str], List[Document]]:
        """
        为整个项目生成所有文档

        Args:
            project: 项目信息对象
            return_document_objects: 是否返回 Document 对象（而非字符串）

        Returns:
            生成的文档内容列表或 Document 对象列表
        """
        # 设置项目名称
        if not self.project_name:
            self.project_name = Path(project.project_path).name

        documents: List[Document] = []

        # 1. 生成项目概览文档
        project_doc = self._generate_project_document(project)
        documents.append(project_doc)

        # 2. 按元素类型分类生成文档
        elements_by_type = self._group_elements_by_type(project.elements)

        # 生成类文档
        for element in elements_by_type.get(ElementType.CLASS, []):
            doc = self._generate_class_document(element, project.language)
            documents.append(doc)
            self.stats['total_classes'] += 1

        # 生成接口文档
        for element in elements_by_type.get(ElementType.INTERFACE, []):
            doc = self._generate_interface_document(element, project.language)
            documents.append(doc)
            self.stats['total_interfaces'] += 1

        # 生成模块文档
        for element in elements_by_type.get(ElementType.MODULE, []):
            doc = self._generate_module_document(element, project.language)
            documents.append(doc)
            self.stats['total_modules'] += 1

        # 生成独立函数文档（不属于类的函数）
        for element in elements_by_type.get(ElementType.FUNCTION, []):
            doc = self._generate_function_document(element, project.language)
            documents.append(doc)
            self.stats['total_functions'] += 1

        # 3. 生成关系文档
        if project.relations:
            relations_doc = self._generate_relations_document(project.relations, project.language)
            documents.append(relations_doc)

        self.stats['documents_generated'] = len(documents)
        logger.info(f"文档生成完成，共生成 {len(documents)} 个文档")

        if return_document_objects:
            return documents
        else:
            # 返回字符串列表（兼容旧接口）
            return [doc.to_markdown() for doc in documents]

    def _generate_project_document(self, project: ProjectInfo) -> Document:
        """生成项目概览文档"""
        project_name = Path(project.project_path).name

        lines = [
            f"# 项目概览: {project_name}",
            "",
            "## 基本信息",
            f"- **项目路径**: {project.project_path}",
            f"- **主要语言**: {project.language.value}",
            f"- **代码元素数量**: {len(project.elements)}",
            f"- **关系数量**: {len(project.relations)}",
            ""
        ]

        # 统计各类型元素数量
        type_counts = {}
        for element in project.elements:
            type_name = element.element_type.value
            type_counts[type_name] = type_counts.get(type_name, 0) + 1

        if type_counts:
            lines.append("## 元素统计")
            for type_name, count in sorted(type_counts.items()):
                lines.append(f"- **{type_name}**: {count}")
            lines.append("")

        # 包/模块结构
        if project.packages:
            lines.append("## 包/模块结构")
            for pkg_name in sorted(project.packages.keys()):
                lines.append(f"- {pkg_name}")
            lines.append("")

        # 依赖信息
        if project.dependencies:
            lines.append("## 外部依赖")
            for dep in project.dependencies[:20]:
                lines.append(f"- {dep}")
            if len(project.dependencies) > 20:
                lines.append(f"- ... 还有 {len(project.dependencies) - 20} 个依赖")
            lines.append("")

        return Document(
            content="\n".join(lines),
            doc_type="project",
            name=project_name,
            full_name=project_name,
            file_path=project.project_path,
            language=project.language.value,
            element_id=generate_element_id(
                project.language.value,
                self.project_name or project_name,
                project_name
            ),
            metadata={
                "element_count": len(project.elements),
                "relation_count": len(project.relations),
            }
        )

    def _generate_class_document(self, element: CodeElement, language: LanguageType) -> Document:
        """生成类描述文档"""
        lines = [
            f"# 类: {element.name}",
            "",
        ]

        # 业务意图描述（LLM 增强）
        if self.enable_llm or True:  # 始终生成业务描述
            business_desc = self.nlp_generator.generate_class_description(element)
            if business_desc:
                lines.extend([
                    "## 业务意图",
                    business_desc,
                    ""
                ])

        # 基本信息
        lines.extend([
            "## 基本信息",
            f"- **完整名称**: {element.full_name}",
            f"- **文件路径**: {element.file_path or '未知'}",
            f"- **行号**: {element.line_number or '未知'}",
        ])

        if element.package:
            lines.append(f"- **包/模块**: {element.package}")

        if element.modifiers:
            lines.append(f"- **修饰符**: {', '.join(element.modifiers)}")

        if element.annotations:
            lines.append(f"- **注解/装饰器**: {', '.join(element.annotations)}")

        lines.append("")

        # 文档字符串
        if element.docstring:
            lines.extend([
                "## 描述",
                element.docstring,
                ""
            ])

        # 继承信息
        extends = element.extra_attributes.get('extends')
        implements = element.extra_attributes.get('implements', [])

        if extends or implements:
            lines.append("## 继承关系")
            if extends:
                lines.append(f"- **继承自**: {extends}")
            if implements:
                lines.append(f"- **实现接口**: {', '.join(implements)}")
            lines.append("")

        # 子元素（方法和字段）
        methods = [c for c in element.children
                   if c.element_type in (ElementType.METHOD, ElementType.FUNCTION, ElementType.CONSTRUCTOR)]
        fields = [c for c in element.children
                  if c.element_type in (ElementType.FIELD, ElementType.VARIABLE, ElementType.PROPERTY)]

        if methods:
            lines.append("## 方法列表")
            for method in methods:
                signature = self._format_method_signature(method)
                desc = f"- **{method.name}**{signature}"
                if method.docstring:
                    short_desc = method.docstring.split('\n')[0][:100]
                    desc += f": {short_desc}"
                lines.append(desc)
            lines.append("")
            self.stats['total_methods'] += len(methods)

        if fields:
            lines.append("## 字段列表")
            for field in fields:
                field_type = field.extra_attributes.get('field_type', '未知类型')
                lines.append(f"- **{field.name}**: {field_type}")
            lines.append("")
            self.stats['total_fields'] += len(fields)

        return Document(
            content="\n".join(lines),
            doc_type="class",
            name=element.name,
            full_name=element.full_name,
            file_path=element.file_path,
            line_number=element.line_number,
            language=language.value,
            package=element.package,
            element_id=generate_element_id(
                language.value,
                self.project_name or "",
                element.full_name
            ),
            metadata={
                "modifiers": element.modifiers,
                "annotations": element.annotations,
                "extends": extends,
                "implements": implements,
            }
        )

    def _generate_interface_document(self, element: CodeElement, language: LanguageType) -> Document:
        """生成接口描述文档"""
        lines = [
            f"# 接口: {element.name}",
            "",
            "## 基本信息",
            f"- **完整名称**: {element.full_name}",
            f"- **文件路径**: {element.file_path or '未知'}",
            f"- **行号**: {element.line_number or '未知'}",
        ]

        if element.package:
            lines.append(f"- **包/模块**: {element.package}")

        if element.modifiers:
            lines.append(f"- **修饰符**: {', '.join(element.modifiers)}")

        lines.append("")

        # 文档字符串
        if element.docstring:
            lines.extend([
                "## 描述",
                element.docstring,
                ""
            ])

        # 继承的接口
        extends = element.extra_attributes.get('extends', [])
        if extends:
            if isinstance(extends, list):
                lines.append(f"## 继承接口: {', '.join(extends)}")
            else:
                lines.append(f"## 继承接口: {extends}")
            lines.append("")

        # 方法声明
        methods = [c for c in element.children
                   if c.element_type in (ElementType.METHOD, ElementType.FUNCTION)]
        if methods:
            lines.append("## 方法声明")
            for method in methods:
                signature = self._format_method_signature(method)
                lines.append(f"- **{method.name}**{signature}")
            lines.append("")

        return Document(
            content="\n".join(lines),
            doc_type="interface",
            name=element.name,
            full_name=element.full_name,
            file_path=element.file_path,
            line_number=element.line_number,
            language=language.value,
            package=element.package,
            element_id=generate_element_id(
                language.value,
                self.project_name or "",
                element.full_name
            ),
            metadata={
                "modifiers": element.modifiers,
                "extends": extends,
            }
        )

    def _generate_module_document(self, element: CodeElement, language: LanguageType) -> Document:
        """生成模块描述文档"""
        lines = [
            f"# 模块: {element.name}",
            "",
        ]

        # 业务意图描述
        business_desc = self.nlp_generator.generate_module_description(element)
        if business_desc:
            lines.extend([
                "## 业务意图",
                business_desc,
                ""
            ])

        lines.extend([
            "## 基本信息",
            f"- **完整名称**: {element.full_name}",
            f"- **文件路径**: {element.file_path or '未知'}",
        ])

        lines.append("")

        # 文档字符串
        if element.docstring:
            lines.extend([
                "## 描述",
                element.docstring,
                ""
            ])

        # 子元素
        classes = [c for c in element.children if c.element_type == ElementType.CLASS]
        functions = [c for c in element.children if c.element_type == ElementType.FUNCTION]
        variables = [c for c in element.children
                     if c.element_type in (ElementType.VARIABLE, ElementType.FIELD)]

        if classes:
            lines.append("## 类列表")
            for cls in classes:
                lines.append(f"- **{cls.name}**: 第 {cls.line_number or '?'} 行")
            lines.append("")

        if functions:
            lines.append("## 函数列表")
            for func in functions:
                lines.append(f"- **{func.name}**: 第 {func.line_number or '?'} 行")
            lines.append("")

        if variables:
            lines.append("## 变量/常量")
            for var in variables:
                lines.append(f"- **{var.name}**")
            lines.append("")

        return Document(
            content="\n".join(lines),
            doc_type="module",
            name=element.name,
            full_name=element.full_name,
            file_path=element.file_path,
            language=language.value,
            package=element.package,
            element_id=generate_element_id(
                language.value,
                self.project_name or "",
                element.full_name
            ),
        )

    def _generate_function_document(self, element: CodeElement, language: LanguageType) -> Document:
        """生成函数描述文档"""
        lines = [
            f"# 函数: {element.name}",
            "",
        ]

        # 业务意图描述
        business_desc = self.nlp_generator.generate_method_description(element)
        if business_desc:
            lines.extend([
                "## 业务意图",
                business_desc,
                ""
            ])

        lines.extend([
            "## 基本信息",
            f"- **完整名称**: {element.full_name}",
            f"- **文件路径**: {element.file_path or '未知'}",
            f"- **行号**: {element.line_number or '未知'}",
        ])

        if element.modifiers:
            lines.append(f"- **修饰符**: {', '.join(element.modifiers)}")

        if element.annotations:
            lines.append(f"- **装饰器**: {', '.join(element.annotations)}")

        lines.append("")

        # 函数签名
        signature = self._format_method_signature(element)
        if signature:
            lines.extend([
                "## 签名",
                f"`{element.name}{signature}`",
                ""
            ])

        # 文档字符串
        if element.docstring:
            lines.extend([
                "## 描述",
                element.docstring,
                ""
            ])

        # 参数
        if element.parameters:
            lines.append("## 参数")
            for param in element.parameters:
                param_name = param.get('name', '未知')
                param_type = param.get('type', '未知类型')
                lines.append(f"- **{param_name}**: {param_type}")
            lines.append("")

        # 返回类型
        if element.return_type:
            lines.extend([
                "## 返回类型",
                f"{element.return_type}",
                ""
            ])

        return Document(
            content="\n".join(lines),
            doc_type="function",
            name=element.name,
            full_name=element.full_name,
            file_path=element.file_path,
            line_number=element.line_number,
            language=language.value,
            package=element.package,
            element_id=generate_element_id(
                language.value,
                self.project_name or "",
                element.full_name
            ),
            metadata={
                "modifiers": element.modifiers,
                "annotations": element.annotations,
                "return_type": element.return_type,
            }
        )

    def _generate_relations_document(
        self,
        relations: List[CodeRelation],
        language: LanguageType
    ) -> Document:
        """生成关系描述文档"""
        lines = [
            "# 代码关系",
            "",
            f"共发现 {len(relations)} 个关系",
            ""
        ]

        # 按关系类型分组
        relations_by_type: Dict[str, List[CodeRelation]] = {}
        for rel in relations:
            type_name = rel.relation_type.value
            if type_name not in relations_by_type:
                relations_by_type[type_name] = []
            relations_by_type[type_name].append(rel)

        for type_name, rels in sorted(relations_by_type.items()):
            lines.append(f"## {type_name} ({len(rels)})")
            for rel in rels[:50]:
                lines.append(f"- {rel.source} → {rel.target}")
            if len(rels) > 50:
                lines.append(f"- ... 还有 {len(rels) - 50} 个")
            lines.append("")

        return Document(
            content="\n".join(lines),
            doc_type="relations",
            name="relations",
            full_name="relations",
            language=language.value,
            element_id=generate_element_id(
                language.value,
                self.project_name or "",
                "relations"
            ),
            metadata={
                "relation_count": len(relations),
                "relation_types": list(relations_by_type.keys()),
            }
        )

    def _group_elements_by_type(
        self,
        elements: List[CodeElement]
    ) -> Dict[ElementType, List[CodeElement]]:
        """按类型分组元素"""
        grouped: Dict[ElementType, List[CodeElement]] = {}
        for element in elements:
            if element.element_type not in grouped:
                grouped[element.element_type] = []
            grouped[element.element_type].append(element)
        return grouped

    def _format_method_signature(self, method: CodeElement) -> str:
        """格式化方法签名"""
        params = []
        for param in method.parameters or []:
            param_name = param.get('name', '')
            param_type = param.get('type', '')
            if param_type:
                params.append(f"{param_name}: {param_type}")
            else:
                params.append(param_name)

        signature = f"({', '.join(params)})"

        if method.return_type:
            signature += f" -> {method.return_type}"

        return signature

    # ========== 兼容旧接口 ==========

    def generate_project_document(self, project: ProjectInfo) -> str:
        """生成项目概览文档（兼容旧接口）"""
        doc = self._generate_project_document(project)
        return doc.to_markdown()

    def generate_class_document(self, element: CodeElement) -> str:
        """生成类描述文档（兼容旧接口）"""
        doc = self._generate_class_document(element, LanguageType.PYTHON)
        return doc.to_markdown()

    def generate_interface_document(self, element: CodeElement) -> str:
        """生成接口描述文档（兼容旧接口）"""
        doc = self._generate_interface_document(element, LanguageType.JAVA)
        return doc.to_markdown()

    def generate_module_document(self, element: CodeElement) -> str:
        """生成模块描述文档（兼容旧接口）"""
        doc = self._generate_module_document(element, LanguageType.PYTHON)
        return doc.to_markdown()

    def generate_function_document(self, element: CodeElement) -> str:
        """生成函数描述文档（兼容旧接口）"""
        doc = self._generate_function_document(element, LanguageType.PYTHON)
        return doc.to_markdown()

    def generate_method_document(self, element: CodeElement) -> str:
        """生成方法描述文档（兼容旧接口）"""
        return self.generate_function_document(element)

    def generate_relations_document(self, relations: List[CodeRelation]) -> str:
        """生成关系描述文档（兼容旧接口）"""
        doc = self._generate_relations_document(relations, LanguageType.PYTHON)
        return doc.to_markdown()

    def generate_element_document(self, element: CodeElement) -> str:
        """根据元素类型生成对应的文档（兼容旧接口）"""
        if element.element_type == ElementType.CLASS:
            return self.generate_class_document(element)
        elif element.element_type == ElementType.INTERFACE:
            return self.generate_interface_document(element)
        elif element.element_type == ElementType.MODULE:
            return self.generate_module_document(element)
        elif element.element_type in (ElementType.FUNCTION, ElementType.METHOD):
            return self.generate_function_document(element)
        else:
            return self._generate_generic_document(element)

    def _generate_generic_document(self, element: CodeElement) -> str:
        """生成通用元素文档"""
        lines = [
            f"# {element.element_type.value}: {element.name}",
            "",
            "## 基本信息",
            f"- **完整名称**: {element.full_name}",
            f"- **类型**: {element.element_type.value}",
            f"- **文件路径**: {element.file_path or '未知'}",
            f"- **行号**: {element.line_number or '未知'}",
        ]

        if element.docstring:
            lines.extend([
                "",
                "## 描述",
                element.docstring
            ])

        return "\n".join(lines)

    def save_documents(self, documents: List[str], prefix: str = "doc") -> List[str]:
        """
        保存文档到文件（兼容旧接口）

        Args:
            documents: 文档内容列表
            prefix: 文件名前缀

        Returns:
            保存的文件路径列表
        """
        if not self.output_dir:
            raise ValueError("未指定输出目录")

        saved_paths = []
        for i, doc in enumerate(documents):
            filename = f"{prefix}_{i:04d}.md"
            filepath = self.output_dir / filename
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(doc)
            saved_paths.append(str(filepath))

        logger.info(f"已保存 {len(saved_paths)} 个文档到 {self.output_dir}")
        return saved_paths

    def get_stats(self) -> Dict[str, int]:
        """获取统计信息"""
        return self.stats.copy()
