"""
tests/test_registry.py - Collector 注册机制测试
"""
import pytest
from core.base import BaseCollector
from core import registry


class DummyCollector(BaseCollector):
    name = "dummy_test"
    label = "测试模块"
    order = 999

    def collect(self) -> dict:
        return {"测试": True}


class NoNameCollector(BaseCollector):
    name = ""
    label = "无名"
    order = 0

    def collect(self) -> dict:
        return {}


class TestRegisterCollector:
    def setup_method(self):
        """每个测试前清理注册表中的测试条目"""
        registry._REGISTRY.pop("dummy_test", None)

    def test_register_success(self):
        result = registry.register_collector(DummyCollector)
        assert result is DummyCollector
        assert "dummy_test" in registry._REGISTRY

    def test_register_no_name_raises(self):
        with pytest.raises(ValueError, match="必须定义 name"):
            registry.register_collector(NoNameCollector)

    def test_get_collector(self):
        registry.register_collector(DummyCollector)
        instance = registry.get_collector("dummy_test")
        assert instance is not None
        assert instance.name == "dummy_test"

    def test_get_collector_not_found(self):
        assert registry.get_collector("nonexistent_xyz") is None

    def test_get_registered_names(self):
        registry.register_collector(DummyCollector)
        names = registry.get_registered_names()
        assert "dummy_test" in names


class TestGetAllCollectors:
    def test_sorted_by_order(self):
        """get_all_collectors 应按 order 排序"""
        collectors = registry.get_all_collectors()
        orders = [c.order for c in collectors]
        assert orders == sorted(orders)
