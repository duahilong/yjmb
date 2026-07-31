"""
formatters/base.py - 格式化基类
"""
from abc import ABC, abstractmethod

from core.manager import CollectResult


class BaseFormatter(ABC):
    """输出格式化基类"""

    @abstractmethod
    def render(self, result: CollectResult, brief: bool = False) -> str:
        """
        将采集结果渲染为字符串。

        Args:
            result: CollectorManager 返回的采集结果
            brief: 是否使用简洁模式

        Returns:
            格式化后的完整输出字符串
        """
        ...
