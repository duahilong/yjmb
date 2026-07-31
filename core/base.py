"""
core/base.py - 采集模块基类与自定义异常
"""
from abc import ABC, abstractmethod


class CollectorError(Exception):
    """采集模块级别的致命错误（整个模块无法工作）"""

    def __init__(self, collector_name: str, message: str):
        self.collector_name = collector_name
        super().__init__(f"[{collector_name}] {message}")


class BaseCollector(ABC):
    """所有硬件采集模块的基类"""

    # === 类属性（子类必须定义）===
    name: str = ""          # 模块标识符，如 "cpu"、"gpu"（用于命令行和配置）
    label: str = ""         # 中文显示名，如 "处理器"、"显卡"（用于输出标题）
    order: int = 0          # 显示排序权重（越小越靠前）

    @abstractmethod
    def collect(self) -> dict:
        """
        执行硬件信息采集。

        Returns:
            dict: 中文键名的采集结果字典。
                  成功时返回完整数据。
                  如果部分字段获取失败，该字段值设为 None 并在
                  结果中添加 "_警告" 键说明原因。

        Raises:
            CollectorError: 当整个模块完全无法采集时抛出。
        """
        ...

    def get_brief_fields(self) -> list[str]:
        """
        返回 brief 模式下应显示的键名列表。
        子类可覆写，默认返回全部键。
        """
        return []

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} name={self.name}>"
