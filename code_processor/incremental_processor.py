# -*- coding: utf-8 -*-
"""
增量处理器

用于检测代码文件变更并实现增量更新，参考 mcp-graphrag 项目的实现。

主要功能：
1. 文件变更检测（基于哈希值）
2. 元数据管理
3. 增量文档生成
4. 缓存管理
"""

import os
import json
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Set, Optional
import logging

logger = logging.getLogger(__name__)


class IncrementalProcessor:
    """
    增量处理器 - 检测文件变更并管理增量更新

    基于文件哈希值检测变更，支持：
    - 新增文件检测
    - 修改文件检测
    - 删除文件检测
    - 元数据持久化
    """

    def __init__(self, project_path: str, metadata_dir: Optional[str] = None):
        """
        初始化增量处理器

        Args:
            project_path: 项目路径
            metadata_dir: 元数据存储目录（默认为项目下的 .ontology_cache）
        """
        self.project_path = Path(project_path).resolve()

        if metadata_dir:
            self.metadata_dir = Path(metadata_dir)
        else:
            self.metadata_dir = self.project_path / ".ontology_cache"

        self.metadata_dir.mkdir(parents=True, exist_ok=True)
        self.metadata_file = self.metadata_dir / "file_metadata.json"

        # 初始化元数据
        self.metadata = self._load_metadata()

    def _calculate_file_hash(self, file_path: Path) -> str:
        """计算文件的 SHA256 哈希值"""
        try:
            with open(file_path, 'rb') as f:
                content = f.read()
                return hashlib.sha256(content).hexdigest()
        except Exception as e:
            logger.error(f"计算文件哈希失败 {file_path}: {e}")
            return ""

    def _load_metadata(self) -> Dict[str, Any]:
        """加载文件元数据"""
        if not self.metadata_file.exists():
            return {
                'files': {},
                'last_update': None,
                'version': '1.0',
                'project_path': str(self.project_path)
            }

        try:
            with open(self.metadata_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError) as e:
            logger.warning(f"加载元数据失败: {e}，使用空元数据")
            return {
                'files': {},
                'last_update': None,
                'version': '1.0',
                'project_path': str(self.project_path)
            }

    def _save_metadata(self) -> None:
        """保存文件元数据"""
        self.metadata['last_update'] = datetime.now().isoformat()
        self.metadata['project_path'] = str(self.project_path)

        try:
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(self.metadata, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存元数据失败: {e}")

    def detect_changes(self, source_files: List[Path]) -> Dict[str, List[Path]]:
        """
        检测文件变更

        Args:
            source_files: 源代码文件列表

        Returns:
            Dict 包含:
            - 'new': 新增文件列表
            - 'modified': 修改文件列表
            - 'deleted': 删除文件列表
            - 'unchanged': 未变更文件列表
        """
        logger.info(f"开始检测 {len(source_files)} 个源代码文件的变更...")

        current_files = {str(f.resolve()): f for f in source_files}
        old_files = set(self.metadata['files'].keys())
        new_files = set(current_files.keys())

        # 分类文件
        deleted_files = old_files - new_files

        new_file_paths = []
        modified_file_paths = []
        unchanged_file_paths = []

        for file_str, file_path in current_files.items():
            try:
                # 计算当前文件哈希
                current_hash = self._calculate_file_hash(file_path)

                if file_str in self.metadata['files']:
                    # 已存在的文件，检查是否修改
                    old_hash = self.metadata['files'][file_str].get('hash', '')
                    if current_hash != old_hash:
                        modified_file_paths.append(file_path)
                        logger.debug(f"检测到修改: {file_path.name}")
                    else:
                        unchanged_file_paths.append(file_path)
                else:
                    # 新文件
                    new_file_paths.append(file_path)
                    logger.debug(f"检测到新文件: {file_path.name}")

                # 更新元数据
                stat = file_path.stat()
                self.metadata['files'][file_str] = {
                    'hash': current_hash,
                    'mtime': stat.st_mtime,
                    'size': stat.st_size,
                    'last_checked': datetime.now().isoformat()
                }

            except Exception as e:
                logger.error(f"处理文件时出错 {file_path}: {e}")
                # 出错时当作修改处理
                modified_file_paths.append(file_path)

        # 清理已删除文件的元数据
        for deleted_file in deleted_files:
            if deleted_file in self.metadata['files']:
                del self.metadata['files'][deleted_file]
                logger.debug(f"清理已删除文件元数据: {deleted_file}")

        # 保存更新的元数据
        self._save_metadata()

        result = {
            'new': new_file_paths,
            'modified': modified_file_paths,
            'deleted': [Path(f) for f in deleted_files],
            'unchanged': unchanged_file_paths
        }

        logger.info(
            f"变更检测完成: 新增 {len(result['new'])} 个, "
            f"修改 {len(result['modified'])} 个, "
            f"删除 {len(result['deleted'])} 个, "
            f"未变更 {len(result['unchanged'])} 个"
        )

        return result

    def get_changed_files(self, source_files: List[Path]) -> List[Path]:
        """获取需要重新处理的文件列表（新增+修改）"""
        changes = self.detect_changes(source_files)
        return changes['new'] + changes['modified']

    def has_metadata(self) -> bool:
        """检查是否存在元数据文件"""
        return self.metadata_file.exists() and len(self.metadata.get('files', {})) > 0

    def is_incremental_update_needed(self, source_files: List[Path]) -> bool:
        """判断是否需要增量更新"""
        if not self.metadata_file.exists():
            logger.info("首次运行，需要全量处理")
            return False

        changes = self.detect_changes(source_files)
        has_changes = (
            len(changes['new']) > 0 or
            len(changes['modified']) > 0 or
            len(changes['deleted']) > 0
        )

        if has_changes:
            logger.info("检测到文件变更，启用增量更新")
            return True
        else:
            logger.info("未检测到文件变更，跳过处理")
            return False

    def get_statistics(self) -> Dict[str, Any]:
        """获取增量处理统计信息"""
        return {
            'total_files_tracked': len(self.metadata['files']),
            'last_update': self.metadata.get('last_update'),
            'metadata_version': self.metadata.get('version', '1.0'),
            'project_path': str(self.project_path),
            'metadata_dir': str(self.metadata_dir)
        }

    def clear_metadata(self) -> None:
        """清除元数据（强制全量重建）"""
        self.metadata = {
            'files': {},
            'last_update': None,
            'version': '1.0',
            'project_path': str(self.project_path)
        }
        self._save_metadata()
        logger.info("已清除元数据，下次将进行全量构建")

    def get_file_hash(self, file_path: str) -> Optional[str]:
        """获取文件的缓存哈希值"""
        return self.metadata['files'].get(file_path, {}).get('hash')

    def get_changed_elements(
        self,
        elements: List[Any],
        changes: Dict[str, List[Path]]
    ) -> Dict[str, List[Any]]:
        """
        根据文件变更过滤代码元素

        Args:
            elements: 代码元素列表
            changes: 文件变更结果

        Returns:
            Dict 包含:
            - 'new': 新增文件中的元素
            - 'modified': 修改文件中的元素
            - 'unchanged': 未变更文件中的元素
        """
        # 构建文件路径集合
        new_files = {str(f.resolve()) for f in changes['new']}
        modified_files = {str(f.resolve()) for f in changes['modified']}
        unchanged_files = {str(f.resolve()) for f in changes['unchanged']}

        result = {
            'new': [],
            'modified': [],
            'unchanged': []
        }

        for element in elements:
            if not hasattr(element, 'file_path') or not element.file_path:
                continue

            file_path = str(Path(element.file_path).resolve())

            if file_path in new_files:
                result['new'].append(element)
            elif file_path in modified_files:
                result['modified'].append(element)
            elif file_path in unchanged_files:
                result['unchanged'].append(element)

        return result
