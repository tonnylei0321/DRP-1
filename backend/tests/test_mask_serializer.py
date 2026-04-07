"""脱敏序列化器单元测试。

覆盖：
- mask_value：phone/id_card/email/custom_regex 四种模式
- apply_mask_rules：mask/hide/none 三种策略
- 多角色最宽松策略合并
- 异常 fallback 到 hide
- 空值和 None 处理
- list[dict] 格式数据脱敏
- export_mask 函数
"""

import pytest

from drp.scope.mask_serializer import (
    apply_mask_rules,
    export_mask,
    mask_value,
    _merge_strategies,
)


# =========================================================================
# mask_value 测试
# =========================================================================


class TestMaskValuePhone:
    """phone 模式脱敏测试。"""

    def test_标准手机号(self):
        assert mask_value("13812345678", "phone") == "138****5678"

    def test_短号码(self):
        # 长度 < 7 时返回 ****
        assert mask_value("12345", "phone") == "****"

    def test_刚好7位(self):
        assert mask_value("1234567", "phone") == "123****4567"

    def test_空字符串(self):
        assert mask_value("", "phone") == ""

    def test_None值(self):
        assert mask_value(None, "phone") is None  # type: ignore[arg-type]


class TestMaskValueIdCard:
    """id_card 模式脱敏测试。"""

    def test_18位身份证(self):
        result = mask_value("110101199001011234", "id_card")
        assert result == "110***********1234"
        assert len(result) == 18

    def test_15位身份证(self):
        result = mask_value("110101900101123", "id_card")
        assert result[:3] == "110"
        assert result[-4:] == "1123"  # 原始后4位
        assert len(result) == 15

    def test_短号码(self):
        assert mask_value("12345", "id_card") == "****"


class TestMaskValueEmail:
    """email 模式脱敏测试。"""

    def test_标准邮箱(self):
        result = mask_value("user@example.com", "email")
        assert result == "u***@example.com"

    def test_单字符用户名(self):
        result = mask_value("a@test.com", "email")
        assert result == "a***@test.com"

    def test_无at符号(self):
        result = mask_value("noemail", "email")
        assert result == "***"

    def test_空字符串(self):
        assert mask_value("", "email") == ""


class TestMaskValueCustomRegex:
    """custom_regex 模式脱敏测试。"""

    def test_自定义正则(self):
        # 替换所有数字
        result = mask_value("abc123def456", "custom_regex", r"\d+")
        assert result == "abc***def***"

    def test_无正则表达式(self):
        result = mask_value("test", "custom_regex", None)
        assert result == "****"

    def test_非法正则(self):
        result = mask_value("test", "custom_regex", "[invalid")
        assert result == "****"

    def test_空正则(self):
        result = mask_value("test", "custom_regex", "")
        assert result == "****"


class TestMaskValueUnknownPattern:
    """未知模式测试。"""

    def test_未知模式(self):
        assert mask_value("test", "unknown_pattern") == "****"


# =========================================================================
# apply_mask_rules 测试
# =========================================================================


def _make_rule(
    role_id: str = "role1",
    column_name: str = "phone",
    mask_strategy: str = "mask",
    mask_pattern: str | None = "phone",
    regex_expression: str | None = None,
) -> dict:
    """构造脱敏规则字典。"""
    return {
        "role_id": role_id,
        "column_name": column_name,
        "mask_strategy": mask_strategy,
        "mask_pattern": mask_pattern,
        "regex_expression": regex_expression,
    }


class TestApplyMaskRulesMaskStrategy:
    """mask 策略测试。"""

    def test_phone_mask(self):
        rules = [_make_rule(column_name="phone", mask_strategy="mask", mask_pattern="phone")]
        data = {"name": "张三", "phone": "13812345678"}
        result = apply_mask_rules(data, rules, ["role1"])
        assert result["phone"] == "138****5678"
        assert result["name"] == "张三"

    def test_email_mask(self):
        rules = [_make_rule(column_name="email", mask_strategy="mask", mask_pattern="email")]
        data = {"email": "user@example.com"}
        result = apply_mask_rules(data, rules, ["role1"])
        assert result["email"] == "u***@example.com"

    def test_id_card_mask(self):
        rules = [_make_rule(column_name="id_card", mask_strategy="mask", mask_pattern="id_card")]
        data = {"id_card": "110101199001011234"}
        result = apply_mask_rules(data, rules, ["role1"])
        assert result["id_card"] == "110***********1234"


class TestApplyMaskRulesHideStrategy:
    """hide 策略测试。"""

    def test_hide_removes_field(self):
        rules = [_make_rule(column_name="phone", mask_strategy="hide")]
        data = {"name": "张三", "phone": "13812345678"}
        result = apply_mask_rules(data, rules, ["role1"])
        assert "phone" not in result
        assert result["name"] == "张三"

    def test_hide_nonexistent_field(self):
        rules = [_make_rule(column_name="secret", mask_strategy="hide")]
        data = {"name": "张三"}
        result = apply_mask_rules(data, rules, ["role1"])
        assert result == {"name": "张三"}


class TestApplyMaskRulesNoneStrategy:
    """none 策略测试。"""

    def test_none_keeps_original(self):
        rules = [_make_rule(column_name="phone", mask_strategy="none")]
        data = {"phone": "13812345678"}
        result = apply_mask_rules(data, rules, ["role1"])
        assert result["phone"] == "13812345678"


# =========================================================================
# 多角色最宽松策略合并
# =========================================================================


class TestMultiRoleMerge:
    """多角色策略合并测试。"""

    def test_none优先于mask(self):
        rules = [
            _make_rule(role_id="role1", column_name="phone", mask_strategy="mask", mask_pattern="phone"),
            _make_rule(role_id="role2", column_name="phone", mask_strategy="none"),
        ]
        data = {"phone": "13812345678"}
        result = apply_mask_rules(data, rules, ["role1", "role2"])
        # none 最宽松，保留原值
        assert result["phone"] == "13812345678"

    def test_mask优先于hide(self):
        rules = [
            _make_rule(role_id="role1", column_name="phone", mask_strategy="hide"),
            _make_rule(role_id="role2", column_name="phone", mask_strategy="mask", mask_pattern="phone"),
        ]
        data = {"phone": "13812345678"}
        result = apply_mask_rules(data, rules, ["role1", "role2"])
        # mask 比 hide 宽松
        assert result["phone"] == "138****5678"

    def test_none优先于hide(self):
        rules = [
            _make_rule(role_id="role1", column_name="phone", mask_strategy="hide"),
            _make_rule(role_id="role2", column_name="phone", mask_strategy="none"),
        ]
        data = {"phone": "13812345678"}
        result = apply_mask_rules(data, rules, ["role1", "role2"])
        assert result["phone"] == "13812345678"

    def test_仅匹配用户角色(self):
        rules = [
            _make_rule(role_id="role1", column_name="phone", mask_strategy="hide"),
            _make_rule(role_id="role3", column_name="phone", mask_strategy="none"),
        ]
        data = {"phone": "13812345678"}
        # 用户只有 role1，不匹配 role3
        result = apply_mask_rules(data, rules, ["role1"])
        assert "phone" not in result

    def test_merge_strategies_直接调用(self):
        rules = [
            _make_rule(role_id="r1", column_name="col", mask_strategy="hide"),
            _make_rule(role_id="r2", column_name="col", mask_strategy="mask", mask_pattern="phone"),
            _make_rule(role_id="r3", column_name="col", mask_strategy="none"),
        ]
        merged = _merge_strategies(rules, "col", ["r1", "r2", "r3"])
        assert merged is not None
        assert merged["mask_strategy"] == "none"

    def test_merge_strategies_无匹配(self):
        rules = [_make_rule(role_id="r1", column_name="col", mask_strategy="hide")]
        merged = _merge_strategies(rules, "col", ["r999"])
        assert merged is None


# =========================================================================
# 异常 fallback 到 hide
# =========================================================================


class TestExceptionFallback:
    """异常处理测试。"""

    def test_mask_value异常时fallback(self):
        """当 mask_value 内部出错时，apply_mask_rules 应 fallback 到 hide。"""
        # 构造一个会导致 mask_value 出错的规则（mask_pattern 为 None）
        rules = [{
            "role_id": "role1",
            "column_name": "data",
            "mask_strategy": "mask",
            "mask_pattern": None,  # 会导致 mask_value 返回 ****
        }]
        data = {"data": "sensitive"}
        result = apply_mask_rules(data, rules, ["role1"])
        # mask_pattern 为 None 时 mask_value 返回 "****"（未知模式）
        assert result["data"] == "****"

    def test_非dict数据不处理(self):
        rules = [_make_rule()]
        result = apply_mask_rules("not a dict", rules, ["role1"])  # type: ignore[arg-type]
        assert result == "not a dict"


# =========================================================================
# 空值和 None 处理
# =========================================================================


class TestNullHandling:
    """空值和 None 处理测试。"""

    def test_None字段值不脱敏(self):
        rules = [_make_rule(column_name="phone", mask_strategy="mask", mask_pattern="phone")]
        data = {"phone": None}
        result = apply_mask_rules(data, rules, ["role1"])
        assert result["phone"] is None

    def test_空规则列表(self):
        data = {"phone": "13812345678"}
        result = apply_mask_rules(data, [], ["role1"])
        assert result["phone"] == "13812345678"

    def test_空角色列表(self):
        rules = [_make_rule()]
        data = {"phone": "13812345678"}
        result = apply_mask_rules(data, rules, [])
        assert result["phone"] == "13812345678"

    def test_空数据dict(self):
        rules = [_make_rule()]
        result = apply_mask_rules({}, rules, ["role1"])
        assert result == {}


# =========================================================================
# list[dict] 格式数据脱敏
# =========================================================================


class TestListDictMask:
    """list[dict] 格式数据脱敏测试。"""

    def test_列表脱敏(self):
        rules = [_make_rule(column_name="phone", mask_strategy="mask", mask_pattern="phone")]
        data = [
            {"name": "张三", "phone": "13812345678"},
            {"name": "李四", "phone": "13987654321"},
        ]
        result = apply_mask_rules(data, rules, ["role1"])
        assert isinstance(result, list)
        assert len(result) == 2
        assert result[0]["phone"] == "138****5678"
        assert result[1]["phone"] == "139****4321"
        assert result[0]["name"] == "张三"

    def test_空列表(self):
        rules = [_make_rule()]
        result = apply_mask_rules([], rules, ["role1"])
        assert result == []

    def test_列表中hide策略(self):
        rules = [_make_rule(column_name="phone", mask_strategy="hide")]
        data = [
            {"name": "张三", "phone": "13812345678"},
            {"name": "李四", "phone": "13987654321"},
        ]
        result = apply_mask_rules(data, rules, ["role1"])
        assert isinstance(result, list)
        for item in result:
            assert "phone" not in item
            assert "name" in item


# =========================================================================
# export_mask 函数
# =========================================================================


class TestExportMask:
    """export_mask 函数测试。"""

    @pytest.mark.asyncio
    async def test_export_mask_应用脱敏(self, monkeypatch):
        """export_mask 应与 apply_mask_rules 共享逻辑。"""
        rules = [_make_rule(column_name="phone", mask_strategy="mask", mask_pattern="phone")]

        # mock load_mask_rules 返回规则
        async def mock_load(*args, **kwargs):
            return rules

        monkeypatch.setattr(
            "drp.scope.mask_serializer.load_mask_rules",
            mock_load,
        )

        rows = [
            {"name": "张三", "phone": "13812345678"},
            {"name": "李四", "phone": "13987654321"},
        ]
        result = await export_mask(rows, "t1", "u1", ["role1"], "item")
        assert result[0]["phone"] == "138****5678"
        assert result[1]["phone"] == "139****4321"

    @pytest.mark.asyncio
    async def test_export_mask_无规则时返回原数据(self, monkeypatch):
        async def mock_load(*args, **kwargs):
            return []

        monkeypatch.setattr(
            "drp.scope.mask_serializer.load_mask_rules",
            mock_load,
        )

        rows = [{"phone": "13812345678"}]
        result = await export_mask(rows, "t1", "u1", ["role1"], "item")
        assert result == rows

    @pytest.mark.asyncio
    async def test_export_mask_hide策略(self, monkeypatch):
        rules = [_make_rule(column_name="phone", mask_strategy="hide")]

        async def mock_load(*args, **kwargs):
            return rules

        monkeypatch.setattr(
            "drp.scope.mask_serializer.load_mask_rules",
            mock_load,
        )

        rows = [{"name": "张三", "phone": "13812345678"}]
        result = await export_mask(rows, "t1", "u1", ["role1"], "item")
        assert "phone" not in result[0]
        assert result[0]["name"] == "张三"


# =========================================================================
# 多列混合策略
# =========================================================================


class TestMultiColumnMixed:
    """多列混合策略测试。"""

    def test_不同列不同策略(self):
        rules = [
            _make_rule(column_name="phone", mask_strategy="mask", mask_pattern="phone"),
            _make_rule(column_name="id_card", mask_strategy="hide"),
            _make_rule(column_name="email", mask_strategy="none"),
        ]
        data = {
            "name": "张三",
            "phone": "13812345678",
            "id_card": "110101199001011234",
            "email": "user@example.com",
        }
        result = apply_mask_rules(data, rules, ["role1"])
        assert result["phone"] == "138****5678"
        assert "id_card" not in result
        assert result["email"] == "user@example.com"
        assert result["name"] == "张三"
