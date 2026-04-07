import sys
from pathlib import Path

# 将 src/ 加入 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# 确保所有 ORM 模型在测试运行前注册到 SQLAlchemy registry，
# 避免跨模块 relationship 字符串引用解析失败
import drp.scope.models  # noqa: F401, E402
