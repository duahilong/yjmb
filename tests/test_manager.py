"""
tests/test_manager.py - CollectorManager 调度测试
"""
import pytest
from core.base import BaseCollector, CollectorError
from core.manager import CollectorManager, CollectResult


class FakeCollectorA(BaseCollector):
    name = "fake_a"
    label = "假模块A"
    order = 10

    def collect(self) -> dict:
        return {"数据": "A"}


class FakeCollectorB(BaseCollector):
    name = "fake_b"
    label = "假模块B"
    order = 20

    def collect(self) -> dict:
        return {"数据": "B", "_警告": ["B有警告"]}


class FakeCollectorError(BaseCollector):
    name = "fake_err"
    label = "错误模块"
    order = 30

    def collect(self) -> dict:
        raise CollectorError(self.name, "模拟致命错误")


class FakeCollectorException(BaseCollector):
    name = "fake_exc"
    label = "异常模块"
    order = 40

    def collect(self) -> dict:
        raise RuntimeError("意外异常")


@pytest.fixture
def manager():
    mgr = CollectorManager()
    mgr.register(FakeCollectorA())
    mgr.register(FakeCollectorB())
    return mgr


class TestCollectorManager:
    def test_collect_all(self, manager):
        result = manager.collect(parallel=False)
        assert "fake_a" in result.data
        assert "fake_b" in result.data
        assert result.data["fake_a"] == {"数据": "A"}

    def test_warnings_extracted(self, manager):
        """_警告 应从数据中提取到 result.warnings"""
        result = manager.collect(parallel=False)
        assert "B有警告" in result.warnings
        assert "_警告" not in result.data["fake_b"]

    def test_filter_by_category(self, manager):
        result = manager.collect(categories=["fake_a"], parallel=False)
        assert "fake_a" in result.data
        assert "fake_b" not in result.data

    def test_exclude(self, manager):
        result = manager.collect(exclude=["fake_b"], parallel=False)
        assert "fake_a" in result.data
        assert "fake_b" not in result.data

    def test_empty_targets(self, manager):
        result = manager.collect(categories=["nonexistent"], parallel=False)
        assert result.data == {}
        assert result.elapsed_seconds >= 0

    def test_collector_error(self):
        mgr = CollectorManager()
        mgr.register(FakeCollectorError())
        result = mgr.collect(parallel=False)
        assert len(result.errors) == 1
        assert "模拟致命错误" in result.errors[0]["错误"]

    def test_unexpected_exception(self):
        mgr = CollectorManager()
        mgr.register(FakeCollectorException())
        result = mgr.collect(parallel=False)
        assert len(result.errors) == 1
        assert "意外异常" in result.errors[0]["错误"]

    def test_parallel_collect(self, manager):
        """并行模式应产生相同结果"""
        result = manager.collect(parallel=True)
        assert "fake_a" in result.data
        assert "fake_b" in result.data

    def test_elapsed_time(self, manager):
        result = manager.collect(parallel=False)
        assert result.elapsed_seconds >= 0
        assert result.elapsed_seconds < 5  # 假模块应该很快

    def test_list_collectors(self, manager):
        listing = manager.list_collectors()
        assert len(listing) == 2
        assert listing[0]["name"] == "fake_a"
        assert listing[1]["name"] == "fake_b"


class TestCollectResult:
    def test_default_values(self):
        r = CollectResult()
        assert r.data == {}
        assert r.errors == []
        assert r.warnings == []
        assert r.elapsed_seconds == 0.0
