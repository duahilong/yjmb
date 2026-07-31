"""
formatters/terminal.py - 终端美化输出格式化器
"""
from core.manager import CollectResult
from core.registry import get_all_collectors
from core.constants import VERSION, ORDER_MAP, BRIEF_FIELDS_MAP, ITEM_BRIEF_FIELDS_MAP
from formatters.base import BaseFormatter
from utils.format_utils import supports_unicode, supports_color, Colors, NoColors


class TerminalFormatter(BaseFormatter):
    """终端美化输出"""

    def __init__(self, use_color: bool = True, use_unicode: bool = True):
        self._color_enabled = use_color and supports_color()
        self._unicode_enabled = use_unicode and supports_unicode()
        self._c = Colors if self._color_enabled else NoColors

    def render(self, result: CollectResult, brief: bool = False) -> str:
        """渲染完整输出"""
        lines = []

        # 头部
        lines.append(self._render_header())
        lines.append("")

        # 获取 collector 标签映射
        label_map = {}
        try:
            for c in get_all_collectors():
                label_map[c.name] = c.label
        except Exception:
            pass

        # 按 order 排序输出各模块
        sorted_names = sorted(result.data.keys(), key=lambda n: self._get_order(n))

        for name in sorted_names:
            data = result.data[name]
            if data is None:
                continue
            label = label_map.get(name, name)
            lines.append(self._render_section(name, label, data, brief))
            lines.append("")

        # 底部摘要
        lines.append(self._render_footer(result))

        return "\n".join(lines)

    def _render_header(self) -> str:
        """渲染头部框线"""
        title = f"HWInfo - Windows 硬件检测工具 v{VERSION}"
        width = 58

        if self._unicode_enabled:
            top = "╔" + "═" * width + "╗"
            mid = "║" + title.center(width) + "║"
            bot = "╚" + "═" * width + "╝"
            return f"{self._c.CYAN_BOLD}{top}\n{mid}\n{bot}{self._c.RESET}"
        else:
            top = "+" + "=" * width + "+"
            mid = "|" + title.center(width) + "|"
            bot = "+" + "=" * width + "+"
            return f"{top}\n{mid}\n{bot}"

    def _render_section(self, name: str, label: str, data: dict, brief: bool) -> str:
        """渲染一个硬件类别区块"""
        lines = []

        # 分类标题
        if self._unicode_enabled:
            title_line = f"{'━' * 18} {label} {'━' * 18}"
        else:
            title_line = f"{'-' * 18} {label} {'-' * 18}"
        lines.append(f"{self._c.CYAN_BOLD}{title_line}{self._c.RESET}")

        # 判断是否为列表型数据（如显卡列表、磁盘列表）
        list_key = self._find_list_key(data)

        if list_key:
            # 列表型：先输出非列表字段，再逐条输出列表项
            brief_fields = self._get_brief_fields(name) if brief else []

            for key, value in data.items():
                if key == list_key or key.startswith("_"):
                    continue
                # brief 模式下只显示关键字段
                if brief and brief_fields and key not in brief_fields:
                    continue
                lines.append(self._format_kv(key, value))

            items = data[list_key]
            if isinstance(items, list):
                # brief 模式下获取列表项的关键字段
                item_brief_fields = self._get_item_brief_fields(name) if brief else []

                for i, item in enumerate(items):
                    lines.append("")
                    item_title = self._get_item_title(item, i)
                    lines.append(f"  {self._c.GREEN_BOLD}{item_title}{self._c.RESET}")
                    for k, v in item.items():
                        if k.startswith("_"):
                            continue
                        # brief 模式：列表项只显示关键字段
                        if brief and item_brief_fields and k not in item_brief_fields:
                            continue
                        lines.append(self._format_kv(k, v, indent=4))
        else:
            # 普通键值型
            if brief:
                # brief 模式只输出关键字段
                brief_fields = self._get_brief_fields(name)
                for key, value in data.items():
                    if key.startswith("_"):
                        continue
                    if brief_fields and key not in brief_fields:
                        continue
                    lines.append(self._format_kv(key, value))
            else:
                for key, value in data.items():
                    if key.startswith("_"):
                        continue
                    lines.append(self._format_kv(key, value))

        return "\n".join(lines)

    def _format_kv(self, key: str, value, indent: int = 2) -> str:
        """格式化单个键值对"""
        prefix = " " * indent
        key_width = 16

        # 格式化值
        value_str = self._format_value(value)

        # 对齐
        display_key = f"{key}:"
        # 计算中文字符宽度（中文占2个字符宽度）
        key_display_width = self._display_width(display_key)
        padding = max(1, key_width - key_display_width + 2)

        return f"{prefix}{display_key}{' ' * padding}{value_str}"

    def _format_value(self, value) -> str:
        """将值格式化为字符串"""
        if value is None:
            return f"{self._c.YELLOW}未知{self._c.RESET}"
        elif isinstance(value, bool):
            if value:
                return f"{self._c.GREEN}是{self._c.RESET}"
            else:
                return f"{self._c.YELLOW}否{self._c.RESET}"
        elif isinstance(value, list):
            if not value:
                return "无"
            # 如果是 dict 列表（如分区），逐条显示
            if isinstance(value[0], dict):
                parts = []
                for item in value:
                    parts.append(self._format_inline_dict(item))
                return "\n" + "\n".join(parts)
            return ", ".join(str(v) for v in value)
        elif isinstance(value, dict):
            return self._format_inline_dict(value)
        elif isinstance(value, float):
            # 去掉多余的 .0
            if value == int(value):
                return str(int(value))
            return str(value)
        else:
            return str(value)

    def _format_inline_dict(self, d: dict) -> str:
        """将字典格式化为内联显示（如分区信息）"""
        parts = []
        for k, v in d.items():
            if v is not None and not k.startswith("_"):
                parts.append(f"{k}: {v}")
        return "      " + " | ".join(parts)

    def _render_footer(self, result: CollectResult) -> str:
        """渲染底部摘要"""
        lines = []

        if self._unicode_enabled:
            lines.append(f"{'━' * 18} 采集完成 {'━' * 18}")
        else:
            lines.append(f"{'-' * 18} 采集完成 {'-' * 18}")

        # 统计
        total = len(result.data) + len(result.errors)
        error_count = len(result.errors)
        warning_count = len(result.warnings)

        summary = (
            f"  耗时: {result.elapsed_seconds}s | "
            f"共 {total} 个类别 | "
            f"{error_count} 错误 | "
            f"{warning_count} 警告"
        )
        lines.append(summary)

        # 错误详情
        if result.errors:
            lines.append("")
            for err in result.errors:
                lines.append(
                    f"  {self._c.RED_BOLD}✖ [{err['模块']}] {err['错误']}{self._c.RESET}"
                )

        # 警告详情
        if result.warnings:
            lines.append("")
            for warn in result.warnings:
                warn_symbol = "⚠" if self._unicode_enabled else "[!]"
                lines.append(f"  {self._c.YELLOW}{warn_symbol} {warn}{self._c.RESET}")

        return "\n".join(lines)

    # ============================================================
    # 辅助方法
    # ============================================================

    def _find_list_key(self, data: dict) -> str | None:
        """查找数据中的列表键（如 '显卡列表'、'磁盘列表'）"""
        for key, value in data.items():
            if isinstance(value, list) and value and isinstance(value[0], dict):
                return key
        return None

    def _get_item_title(self, item: dict, index: int) -> str:
        """获取列表项的标题"""
        # 尝试用常见字段作为标题
        for title_key in ["名称", "型号", "插槽", "盘符"]:
            if title_key in item and item[title_key]:
                prefix = ""
                if "类型" in item:
                    prefix = f"[{item['类型']}] "
                return f"{prefix}{item[title_key]}"
        return f"[{index}]"

    def _get_order(self, name: str) -> int:
        """获取模块排序权重"""
        return ORDER_MAP.get(name, 99)

    def _get_brief_fields(self, name: str) -> list[str]:
        """获取某模块的 brief 字段列表（顶层字段）"""
        return BRIEF_FIELDS_MAP.get(name, [])

    def _get_item_brief_fields(self, name: str) -> list[str]:
        """获取列表型数据中每个项的 brief 字段"""
        return ITEM_BRIEF_FIELDS_MAP.get(name, [])

    @staticmethod
    def _display_width(text: str) -> int:
        """计算字符串的显示宽度（中文字符占2格）"""
        width = 0
        for ch in text:
            if '\u4e00' <= ch <= '\u9fff' or '\u3000' <= ch <= '\u303f':
                width += 2
            elif '\uff00' <= ch <= '\uffef':
                width += 2
            else:
                width += 1
        return width
