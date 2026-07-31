"""
core/registry.py - Collector 注册与发现机制
"""
from core.base import BaseCollector

_REGISTRY: dict[str, type] = {}


def register_collector(cls):
    """
    装饰器：将 Collector 类注册到全局注册表。
    用法：
        @register_collector
        class CPUCollector(BaseCollector):
            name = "cpu"
            ...
    """
    if not cls.name:
        raise ValueError(f"{cls.__name__} 必须定义 name 属性")
    _REGISTRY[cls.name] = cls
    return cls


def get_all_collectors() -> list[BaseCollector]:
    """实例化并返回所有已注册的 Collector（按 order 排序）"""
    instances = [cls() for cls in _REGISTRY.values()]
    return sorted(instances, key=lambda c: c.order)


def get_collector(name: str) -> BaseCollector | None:
    """按名称获取单个 Collector 实例"""
    cls = _REGISTRY.get(name)
    return cls() if cls else None


def get_registered_names() -> list[str]:
    """返回所有已注册的 Collector 名称列表"""
    return list(_REGISTRY.keys())
