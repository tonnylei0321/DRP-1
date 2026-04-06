"""端到端冒烟测试。"""
import subprocess
import sys
import os
from pathlib import Path

import yaml

# 项目根目录
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


class TestE2ESmoke:
    """端到端冒烟测试"""

    def test_generate_test_data_creates_files(self):
        """运行 generate_test_data.py 后生成预期文件"""
        script = PROJECT_ROOT / "scripts" / "generate_test_data.py"
        result = subprocess.run(
            [sys.executable, str(script)],
            capture_output=True, text=True, timeout=30,
        )
        assert result.returncode == 0, f"脚本执行失败: {result.stderr}"

        ddl_dir = PROJECT_ROOT / "backend" / "tests" / "fixtures" / "ddl"
        data_dir = PROJECT_ROOT / "backend" / "tests" / "fixtures" / "data"

        # 验证 7 个域文件 + all_tables.sql
        assert (ddl_dir / "all_tables.sql").exists()
        for i in range(1, 8):
            domain_files = list(ddl_dir.glob(f"{i:02d}_*.sql"))
            assert len(domain_files) >= 1, f"域 {i:02d} DDL 文件缺失"

        # 验证 7 个数据文件
        for i in range(1, 8):
            data_files = list(data_dir.glob(f"{i:02d}_*_data.sql"))
            assert len(data_files) >= 1, f"域 {i:02d} 数据文件缺失"

    def test_ddl_parser_can_parse_all_tables(self):
        """DDL_Parser 能解析 all_tables.sql"""
        from drp.mapping.ddl_parser import parse_ddl

        all_file = PROJECT_ROOT / "backend" / "tests" / "fixtures" / "ddl" / "all_tables.sql"
        if not all_file.exists():
            # 先生成
            script = PROJECT_ROOT / "scripts" / "generate_test_data.py"
            subprocess.run([sys.executable, str(script)], capture_output=True, timeout=30)

        ddl_content = all_file.read_text(encoding="utf-8")
        tables = parse_ddl(ddl_content)
        assert len(tables) >= 14, f"解析出的表数量不足: {len(tables)} < 14"
