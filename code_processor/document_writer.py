# -*- coding: utf-8 -*-
"""
Document Writer - 文档写入器

负责将生成的文档保存到磁盘，管理构建 ID。
"""

import hashlib
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)


class Document:
    """
    文档对象

    表示一个带有元数据的文档
    """

    def __init__(
        self,
        content: str,
        doc_type: str,
        name: str,
        full_name: str,
        file_path: Optional[str] = None,
        line_number: Optional[int] = None,
        language: str = "python",
        package: Optional[str] = None,
        element_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        初始化文档对象

        Args:
            content: 文档内容（Markdown 格式）
            doc_type: 文档类型（class, method, module, project, relations）
            name: 元素名称
            full_name: 完整名称
            file_path: 源文件路径
            line_number: 行号
            language: 编程语言
            package: 包/模块名
            element_id: 稳定实体 ID
            metadata: 额外元数据
        """
        self.content = content
        self.doc_type = doc_type
        self.name = name
        self.full_name = full_name
        self.file_path = file_path
        self.line_number = line_number
        self.language = language
        self.package = package
        self.element_id = element_id
        self.metadata = metadata or {}

    def to_markdown(self) -> str:
        """
        转换为带 frontmatter 的 Markdown 格式

        Returns:
            完整的 Markdown 文档
        """
        # 构建 frontmatter
        frontmatter_lines = [
            "---",
            f"doc_type: {self.doc_type}",
            f"name: {self.name}",
            f"full_name: {self.full_name}",
        ]

        if self.file_path:
            frontmatter_lines.append(f"file_path: {self.file_path}")

        if self.line_number:
            frontmatter_lines.append(f"line_number: {self.line_number}")

        frontmatter_lines.append(f"language: {self.language}")

        if self.package:
            frontmatter_lines.append(f"package: {self.package}")

        if self.element_id:
            frontmatter_lines.append(f"element_id: {self.element_id}")

        # 添加额外元数据
        for key, value in self.metadata.items():
            if isinstance(value, list):
                frontmatter_lines.append(f"{key}:")
                for item in value:
                    frontmatter_lines.append(f"  - \"{item}\"")
            elif isinstance(value, bool):
                frontmatter_lines.append(f"{key}: {str(value).lower()}")
            elif value is not None:
                frontmatter_lines.append(f"{key}: {value}")

        frontmatter_lines.append("---")
        frontmatter_lines.append("")

        # 组合 frontmatter 和内容
        return "\n".join(frontmatter_lines) + self.content


class DocumentWriter:
    """
    文档写入器

    负责将生成的文档保存到磁盘，管理构建 ID
    """

    def __init__(self, base_dir: str = "docs/ontology/code_docs"):
        """
        初始化文档写入器

        Args:
            base_dir: 基础输出目录
        """
        self.base_dir = Path(base_dir)

    def save(
        self,
        project_name: str,
        documents: List[Document],
        build_id: Optional[str] = None
    ) -> str:
        """
        保存文档到磁盘

        目录结构:
        docs/ontology/code_docs/<project>/<build_id>/
        ├── project.md
        ├── packages/
        │   └── <pkg>.md
        ├── elements/
        │   └── <full_name>.md
        └── relations.md

        Args:
            project_name: 项目名称
            documents: 文档列表
            build_id: 构建 ID（可选，不指定则自动生成）

        Returns:
            构建目录路径
        """
        # 生成构建 ID
        if not build_id:
            build_id = self._generate_build_id()

        # 创建目录结构
        build_dir = self.base_dir / project_name / build_id
        packages_dir = build_dir / "packages"
        elements_dir = build_dir / "elements"

        build_dir.mkdir(parents=True, exist_ok=True)
        packages_dir.mkdir(exist_ok=True)
        elements_dir.mkdir(exist_ok=True)

        # 保存文档
        saved_count = 0
        for doc in documents:
            try:
                filepath = self._get_document_path(doc, build_dir, packages_dir, elements_dir)
                self._write_document(doc, filepath)
                saved_count += 1
            except Exception as e:
                logger.error(f"保存文档失败 {doc.full_name}: {e}")

        # 写入构建元数据
        self._write_build_metadata(build_dir, project_name, build_id, saved_count)

        logger.info(f"已保存 {saved_count} 个文档到 {build_dir}")
        return str(build_dir)

    def _generate_build_id(self) -> str:
        """
        生成构建 ID

        格式: YYYYMMDD-HHMMSS-<short_hash>

        Returns:
            构建 ID
        """
        now = datetime.now()
        timestamp = now.strftime("%Y%m%d-%H%M%S")

        # 生成短哈希
        hash_input = f"{timestamp}-{now.microsecond}"
        short_hash = hashlib.md5(hash_input.encode()).hexdigest()[:6]

        return f"{timestamp}-{short_hash}"

    def _get_document_path(
        self,
        doc: Document,
        build_dir: Path,
        packages_dir: Path,
        elements_dir: Path
    ) -> Path:
        """
        获取文档保存路径

        Args:
            doc: 文档对象
            build_dir: 构建目录
            packages_dir: 包目录
            elements_dir: 元素目录

        Returns:
            文件路径
        """
        if doc.doc_type == "project":
            return build_dir / "project.md"
        elif doc.doc_type == "relations":
            return build_dir / "relations.md"
        elif doc.doc_type == "package" or doc.doc_type == "module":
            # 包/模块文档
            safe_name = self._safe_filename(doc.full_name)
            return packages_dir / f"{safe_name}.md"
        else:
            # 其他元素文档（class, method, function, interface）
            safe_name = self._safe_filename(doc.full_name)
            return elements_dir / f"{safe_name}.md"

    def _safe_filename(self, name: str) -> str:
        """
        将名称转换为安全的文件名

        Args:
            name: 原始名称

        Returns:
            安全的文件名
        """
        # 替换不安全字符
        safe = name.replace('/', '_').replace('\\', '_')
        safe = safe.replace('<', '_').replace('>', '_')
        safe = safe.replace(':', '_').replace('*', '_')
        safe = safe.replace('?', '_').replace('"', '_')
        safe = safe.replace('|', '_')

        # 限制长度
        if len(safe) > 200:
            # 保留前 100 和后 100 字符，中间用哈希替代
            hash_part = hashlib.md5(safe.encode()).hexdigest()[:8]
            safe = f"{safe[:100]}_{hash_part}_{safe[-100:]}"

        return safe

    def _write_document(self, doc: Document, filepath: Path) -> None:
        """
        写入文档到文件

        Args:
            doc: 文档对象
            filepath: 文件路径
        """
        content = doc.to_markdown()
        filepath.write_text(content, encoding='utf-8')
        logger.debug(f"已写入文档: {filepath}")

    def _write_build_metadata(
        self,
        build_dir: Path,
        project_name: str,
        build_id: str,
        document_count: int
    ) -> None:
        """
        写入构建元数据

        Args:
            build_dir: 构建目录
            project_name: 项目名称
            build_id: 构建 ID
            document_count: 文档数量
        """
        metadata = {
            "project_name": project_name,
            "build_id": build_id,
            "build_time": datetime.now().isoformat(),
            "document_count": document_count,
        }

        # 写入 YAML 格式的元数据
        metadata_path = build_dir / "build_metadata.yaml"
        lines = ["# 构建元数据"]
        for key, value in metadata.items():
            lines.append(f"{key}: {value}")

        metadata_path.write_text("\n".join(lines), encoding='utf-8')


def generate_element_id(
    language: str,
    project_name: str,
    full_name: str
) -> str:
    """
    生成稳定的实体 ID

    格式: code:<language>:<project>:<full_name>

    Args:
        language: 编程语言
        project_name: 项目名称
        full_name: 完整名称

    Returns:
        实体 ID
    """
    # 清理项目名称
    clean_project = project_name.replace(' ', '_').replace('/', '_')

    # 清理完整名称
    clean_full_name = full_name.replace(' ', '_')

    return f"code:{language}:{clean_project}:{clean_full_name}"
