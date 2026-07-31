"""
formatters/json_fmt.py - JSON 输出格式化器
"""
import json
from datetime import datetime

from core.manager import CollectResult
from core.constants import VERSION, ORDER_MAP, BRIEF_FIELDS_MAP
from formatters.base import BaseFormatter


class JsonFormatter(BaseFormatter):
    """JSON 格式输出"""

    def render(self, result: CollectResult, brief: bool = False) -> str:
        """渲染为 JSON 字符串"""
        output = {
            "_元信息": {
                "工具版本": VERSION,
                "采集时间": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
                "耗时_秒": result.elapsed_seconds,
                "错误数": len(result.errors),
                "警告数": len(result.warnings),
            }
        }

        # 按 order 排序添加数据
        sorted_names = sorted(result.data.keys(), key=lambda n: self._get_order(n))
        for name in sorted_names:
            data = result.data[name]
            if data is not None:
                if brief:
                    data = self._filter_brief(name, data)
                output[name] = data

        # 错误和警告
        if result.errors:
            output["_错误"] = result.errors
        if result.warnings:
            output["_警告"] = result.warnings

        return json.dumps(output, ensure_ascii=False, indent=2)

    def _filter_brief(self, name: str, data: dict) -> dict:
        """brief 模式过滤"""
        fields = BRIEF_FIELDS_MAP.get(name)
        if not fields:
            return data
        return {k: v for k, v in data.items() if k in fields or k.startswith("_")}

    @staticmethod
    def _get_order(name: str) -> int:
        return ORDER_MAP.get(name, 99)
