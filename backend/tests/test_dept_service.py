"""部门服务单元测试：使用 SQLite 内存数据库测试递归 CTE 和循环引用检测。

覆盖场景：
- 单层部门树（根部门无子部门）
- 多层部门树（A→B→C，查询 A 返回 [A,B,C]）
- 循环引用检测（A→B→C，将 A 的 parent 设为 C 应检测到循环）
- 非循环更新（将 C 的 parent 改为 D 应允许）
- 深度限制（超过 10 层的部门树应在第 10 层截止）
"""

import uuid

import pytest
from sqlalchemy import Column, String, ForeignKey, Integer, text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

from drp.scope.dept_service import (
    get_dept_subtree,
    check_circular_reference,
    MAX_RECURSION_DEPTH,
)


# ---------------------------------------------------------------------------
# 测试用的轻量 ORM 模型（SQLite 兼容，不依赖 PostgreSQL UUID 类型）
# ---------------------------------------------------------------------------

class _Base(DeclarativeBase):
    pass


class DeptTest(_Base):
    """SQLite 兼容的部门表，使用 String 类型代替 UUID。"""
    __tablename__ = "department"

    id = Column(String(36), primary_key=True)
    tenant_id = Column(String(36), nullable=False)
    name = Column(String(255), nullable=False)
    parent_id = Column(String(36), ForeignKey("department.id"), nullable=True)
    sort_order = Column(Integer, nullable=False, default=0)
    status = Column(String(50), nullable=False, default="active")


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
async def engine():
    """创建 SQLite 异步内存引擎。"""
    eng = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with eng.begin() as conn:
        await conn.run_sync(_Base.metadata.create_all)
    yield eng
    await eng.dispose()


@pytest.fixture
async def session(engine):
    """提供异步会话。"""
    factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as sess:
        yield sess


# ---------------------------------------------------------------------------
# 辅助函数
# ---------------------------------------------------------------------------

def make_dept(dept_id: uuid.UUID, tenant_id: uuid.UUID, name: str, parent_id: uuid.UUID | None = None) -> DeptTest:
    return DeptTest(
        id=str(dept_id),
        tenant_id=str(tenant_id),
        name=name,
        parent_id=str(parent_id) if parent_id else None,
    )


async def insert_depts(session: AsyncSession, depts: list[DeptTest]):
    """批量插入部门记录。"""
    for dept in depts:
        session.add(dept)
    await session.commit()


# ---------------------------------------------------------------------------
# 测试用例
# ---------------------------------------------------------------------------

class TestGetDeptSubtree:
    """get_dept_subtree 递归 CTE 查询测试。"""

    async def test_single_root_no_children(self, session: AsyncSession):
        """单层部门树：根部门无子部门，返回仅包含自身的列表。"""
        tenant = uuid.uuid4()
        root = uuid.uuid4()
        await insert_depts(session, [make_dept(root, tenant, "根部门")])

        result = await get_dept_subtree(session, root)
        assert set(result) == {root}

    async def test_multi_level_tree(self, session: AsyncSession):
        """多层部门树：A→B→C，查询 A 返回 [A, B, C]。"""
        tenant = uuid.uuid4()
        a, b, c = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
        await insert_depts(session, [
            make_dept(a, tenant, "部门A"),
            make_dept(b, tenant, "部门B", parent_id=a),
            make_dept(c, tenant, "部门C", parent_id=b),
        ])

        result = await get_dept_subtree(session, a)
        assert set(result) == {a, b, c}

    async def test_subtree_from_middle(self, session: AsyncSession):
        """从中间节点查询：A→B→C，查询 B 返回 [B, C]，不包含 A。"""
        tenant = uuid.uuid4()
        a, b, c = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
        await insert_depts(session, [
            make_dept(a, tenant, "部门A"),
            make_dept(b, tenant, "部门B", parent_id=a),
            make_dept(c, tenant, "部门C", parent_id=b),
        ])

        result = await get_dept_subtree(session, b)
        assert set(result) == {b, c}

    async def test_branching_tree(self, session: AsyncSession):
        """分叉树：A 有两个子部门 B 和 C，B 有子部门 D。"""
        tenant = uuid.uuid4()
        a, b, c, d = uuid.uuid4(), uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
        await insert_depts(session, [
            make_dept(a, tenant, "部门A"),
            make_dept(b, tenant, "部门B", parent_id=a),
            make_dept(c, tenant, "部门C", parent_id=a),
            make_dept(d, tenant, "部门D", parent_id=b),
        ])

        result = await get_dept_subtree(session, a)
        assert set(result) == {a, b, c, d}

    async def test_leaf_node(self, session: AsyncSession):
        """叶子节点查询：返回仅包含自身。"""
        tenant = uuid.uuid4()
        a, b = uuid.uuid4(), uuid.uuid4()
        await insert_depts(session, [
            make_dept(a, tenant, "部门A"),
            make_dept(b, tenant, "部门B", parent_id=a),
        ])

        result = await get_dept_subtree(session, b)
        assert set(result) == {b}

    async def test_depth_limit(self, session: AsyncSession):
        """深度限制：超过 10 层的部门树应在第 10 层截止。

        构建 12 层深的链式部门树，查询根节点应只返回前 10 层。
        """
        tenant = uuid.uuid4()
        total_depth = 12
        dept_ids = [uuid.uuid4() for _ in range(total_depth)]

        depts = [make_dept(dept_ids[0], tenant, "层级0")]
        for i in range(1, total_depth):
            depts.append(make_dept(dept_ids[i], tenant, f"层级{i}", parent_id=dept_ids[i - 1]))
        await insert_depts(session, depts)

        result = await get_dept_subtree(session, dept_ids[0])

        # 根节点 depth=1，最大 depth=10，所以返回前 10 层（索引 0-9）
        expected = set(dept_ids[:MAX_RECURSION_DEPTH])
        assert set(result) == expected
        # 第 11、12 层不应出现
        assert dept_ids[10] not in result
        assert dept_ids[11] not in result

    async def test_nonexistent_dept(self, session: AsyncSession):
        """查询不存在的部门 ID，返回空列表。"""
        result = await get_dept_subtree(session, uuid.uuid4())
        assert result == []


class TestCheckCircularReference:
    """check_circular_reference 循环引用检测测试。"""

    async def test_circular_detected(self, session: AsyncSession):
        """循环引用检测：A→B→C，将 A 的 parent 设为 C 应检测到循环。"""
        tenant = uuid.uuid4()
        a, b, c = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
        await insert_depts(session, [
            make_dept(a, tenant, "部门A"),
            make_dept(b, tenant, "部门B", parent_id=a),
            make_dept(c, tenant, "部门C", parent_id=b),
        ])

        # 将 A 的 parent 设为 C → 形成 A→B→C→A 循环
        is_circular = await check_circular_reference(session, a, c)
        assert is_circular is True

    async def test_no_circular_sibling(self, session: AsyncSession):
        """非循环更新：将 C 的 parent 改为 A 的兄弟节点 D 应允许。"""
        tenant = uuid.uuid4()
        root, a, b, c, d = uuid.uuid4(), uuid.uuid4(), uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
        await insert_depts(session, [
            make_dept(root, tenant, "根部门"),
            make_dept(a, tenant, "部门A", parent_id=root),
            make_dept(b, tenant, "部门B", parent_id=a),
            make_dept(c, tenant, "部门C", parent_id=b),
            make_dept(d, tenant, "部门D", parent_id=root),  # D 是 A 的兄弟
        ])

        # 将 C 的 parent 改为 D → 不形成循环
        is_circular = await check_circular_reference(session, c, d)
        assert is_circular is False

    async def test_self_reference(self, session: AsyncSession):
        """自引用检测：将部门的 parent 设为自身应检测到循环。"""
        tenant = uuid.uuid4()
        a = uuid.uuid4()
        await insert_depts(session, [make_dept(a, tenant, "部门A")])

        is_circular = await check_circular_reference(session, a, a)
        assert is_circular is True

    async def test_move_to_root(self, session: AsyncSession):
        """将子部门移到根部门下不应产生循环。"""
        tenant = uuid.uuid4()
        root, a, b = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
        await insert_depts(session, [
            make_dept(root, tenant, "根部门"),
            make_dept(a, tenant, "部门A", parent_id=root),
            make_dept(b, tenant, "部门B", parent_id=a),
        ])

        # 将 B 的 parent 改为 root → 不形成循环
        is_circular = await check_circular_reference(session, b, root)
        assert is_circular is False

    async def test_deep_chain_circular(self, session: AsyncSession):
        """深层链路循环检测：长链中将根节点 parent 设为末端节点。"""
        tenant = uuid.uuid4()
        dept_ids = [uuid.uuid4() for _ in range(6)]

        depts = [make_dept(dept_ids[0], tenant, "层级0")]
        for i in range(1, 6):
            depts.append(make_dept(dept_ids[i], tenant, f"层级{i}", parent_id=dept_ids[i - 1]))
        await insert_depts(session, depts)

        # 将根节点的 parent 设为最末端节点 → 循环
        is_circular = await check_circular_reference(session, dept_ids[0], dept_ids[5])
        assert is_circular is True

    async def test_no_circular_unrelated(self, session: AsyncSession):
        """不相关的两棵树之间移动不应产生循环。"""
        tenant = uuid.uuid4()
        a, b, x, y = uuid.uuid4(), uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
        await insert_depts(session, [
            make_dept(a, tenant, "树1-A"),
            make_dept(b, tenant, "树1-B", parent_id=a),
            make_dept(x, tenant, "树2-X"),
            make_dept(y, tenant, "树2-Y", parent_id=x),
        ])

        # 将 B 的 parent 改为 X → 跨树移动，不循环
        is_circular = await check_circular_reference(session, b, x)
        assert is_circular is False
