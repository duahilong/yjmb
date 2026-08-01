"""
formatters/json_fmt.py - JSON 输出格式化器
"""
import json
from datetime import datetime

from core.manager import CollectResult
from core.constants import VERSION, ORDER_MAP, BRIEF_FIELDS_MAP, ITEM_BRIEF_FIELDS_MAP
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
        """brief 模式过滤（支持顶层字段 + 列表型数据）"""
        fields = BRIEF_FIELDS_MAP.get(name)
        item_fields = ITEM_BRIEF_FIELDS_MAP.get(name)

        # 如果没有定义任何 brief 字段，返回全部
        if not fields and not item_fields:
            return data

        result = {}
        for k, v in data.items():
            if k.startswith("_"):
                result[k] = v
                continue

            # 列表型数据（如显卡列表、磁盘列表）
            if isinstance(v, list) and v and isinstance(v[0], dict):
                if item_fields:
                    result[k] = [
                        {ik: iv for ik, iv in item.items() if ik in item_fields or ik.startswith("_")}
                        for item in v
                    ]
                elif not fields:
                    # 有 item_fields 但无顶层 fields，保留列表
                    result[k] = v
                # 如果有顶层 fields 但列表键不在其中，跳过
                elif k in fields:
                    result[k] = v
            else:
                # 普通字段
                if fields and k in fields:
                    result[k] = v
                elif not fields:
                    result[k] = v

        return result

    @staticmethod
    def _get_order(name: str) -> int:
        return ORDER_MAP.get(name, 99)
