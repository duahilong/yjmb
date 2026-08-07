"""
gui/pages/overview.py - 总览页（配置清单）

每个类别一行纯值摘要，如：
    主板    Micro-Star International Co., Ltd. | Z790MPOWER (MS-7E01) | P.60
    处理器  Genuine Intel(R) 0000 | 24 | 24 | 1690 MHz
"""
from PySide6.QtWidgets import (
    QScrollArea, QWidget, QVBoxLayout,
    QTreeWidget, QTreeWidgetItem, QHeaderView, QAbstractItemView,
)
from PySide6.QtCore import QSize
from PySide6.QtGui import QBrush, QColor, QFont

from gui.pages.base_page import BasePage
from gui.zoom import scaled
from core.constants import (
    CATEGORY_LABELS, BRIEF_FIELDS_MAP, ITEM_BRIEF_FIELDS_MAP,
)


# 总览页显示类别及顺序（不包含显示器）
OVERVIEW_ORDER = ["os", "cpu", "motherboard", "memory", "gpu", "storage", "network", "audio"]


class OverviewPage(BasePage):
    """总览页：每个类别一行纯值摘要"""

    def __init__(self, parent=None):
        super().__init__(parent)

        title = self._make_title("配置概览")

        # 可滚动内容区
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        self._content = QWidget()
        self._content.setStyleSheet("background-color: #f5f5f5;")
        self._content_layout = QVBoxLayout(self._content)
        self._content_layout.setContentsMargins(4, 4, 4, 4)
        self._content_layout.setSpacing(12)
        self._content_layout.addStretch()
        self._scroll.setWidget(self._content)
        self._layout.addWidget(self._scroll)

    def update_data(self, data: dict) -> None:
        """接收全部采集数据，生成紧凑摘要列表"""
        self._clear_content()

        if not data:
            self._content_layout.insertWidget(0, self._make_placeholder("正在采集..."))
            return

        # 紧凑两列表：类别名 | 一行摘要
        table = QTreeWidget()
        table.setObjectName("overviewTable")
        table.setColumnCount(2)
        table.setHeaderHidden(True)
        table.setRootIsDecorated(False)
        table.setUniformRowHeights(True)
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        # 类别列固定宽度，摘要列拉伸（不依赖 ResizeToContents，隐藏表头时不可靠）
        table.header().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        table.header().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        table.setColumnWidth(0, scaled(90))

        # 样式：类别名蓝色加粗，摘要深灰
        cat_font = QFont()
        cat_font.setBold(True)
        cat_brush = QBrush(QColor("#1a6dff"))
        val_brush = QBrush(QColor("#333333"))

        row_count = 0
        for cat in OVERVIEW_ORDER:
            cat_data = data.get(cat)
            if cat_data is None:
                continue

            lines = self._extract_summary_lines(cat, cat_data)
            if not lines:
                continue

            for idx, line in enumerate(lines):
                # 同类别多行时，只在第一行显示类别名
                label = CATEGORY_LABELS.get(cat, cat) if idx == 0 else ""
                item = QTreeWidgetItem([label, line])
                item.setSizeHint(0, QSize(0, scaled(32)))
                item.setForeground(1, val_brush)
                if idx == 0:
                    item.setFont(0, cat_font)
                    item.setForeground(0, cat_brush)
                table.addTopLevelItem(item)
                row_count += 1

        if row_count == 0:
            self._content_layout.insertWidget(0, self._make_placeholder("暂无数据"))
            return

        # 表格高度 = 行数 × 行高，避免内部滚动条
        table.setFixedHeight(row_count * scaled(32) + scaled(8))
        self._content_layout.insertWidget(0, table)

    # ========================================================
    # 摘要提取
    # ========================================================

    def _extract_summary_lines(self, cat: str, cat_data) -> list[str]:
        """提取类别摘要行（每行一个设备/一组纯值）"""
        if isinstance(cat_data, dict):
            # 检查是否为「设备列表型」dict（如 {"显卡列表": [{...}, ...]}）
            device_list = self._find_device_list(cat_data)
            if device_list is not None:
                return self._device_lines(cat, device_list)

            # 纯标量 dict（cpu、os、motherboard、memory）→ 单行
            fields = BRIEF_FIELDS_MAP.get(cat, [])
            values = []
            for f in fields:
                v = cat_data.get(f)
                if v is None or v == "":
                    continue
                if isinstance(v, list):
                    values.append(", ".join(str(x) for x in v))
                elif isinstance(v, dict):
                    continue
                else:
                    values.append(self._format_value(f, v, cat))
            return [" | ".join(values)] if values else []

        elif isinstance(cat_data, list):
            return self._device_lines(cat, cat_data)

        return []

    def _device_lines(self, cat: str, devices: list) -> list[str]:
        """设备列表 → 每个设备一行"""
        item_fields = ITEM_BRIEF_FIELDS_MAP.get(cat, [])
        lines = []

        for item in devices:
            if not isinstance(item, dict):
                continue

            values = []
            if item_fields:
                for f in item_fields:
                    v = item.get(f)
                    if v is None or v == "":
                        continue
                    if isinstance(v, (dict, list)):
                        continue
                    values.append(self._format_value(f, v, cat))
            else:
                # 未配置字段时，取设备名 + 前几个标量值
                name = item.get("名称") or item.get("型号")
                if name:
                    values.append(str(name))
                for k, v in item.items():
                    if k in ("名称", "型号"):
                        continue
                    if v is None or isinstance(v, (dict, list)):
                        continue
                    values.append(self._format_value(k, v, cat))
                    if len(values) >= 4:
                        break

            if values:
                lines.append(" · ".join(values))

        return lines

    @staticmethod
    def _find_device_list(data: dict) -> list | None:
        """从 dict 中找到第一个 list[dict] 值（设备列表）"""
        for value in data.values():
            if isinstance(value, list) and value and isinstance(value[0], dict):
                return value
        return None

    @staticmethod
    def _format_value(field: str, value, cat: str = "") -> str:
        """值格式化：单位换算、数量词补充等"""
        # 数量类字段补充量词，避免纯数字不直观
        if field == "核心数" and isinstance(value, (int, float)):
            return f"{int(value)} 核"
        if field == "线程数" and isinstance(value, (int, float)):
            return f"{int(value)} 线程"
        if field == "已用插槽" and isinstance(value, (int, float)):
            return f"{int(value)} 插槽"
        if field == "CL" and isinstance(value, (int, float)):
            return f"CL{int(value)}"
        if field.endswith("_V") and isinstance(value, (int, float)):
            return f"{value:g}V"
        # 频率：内存保留 MHz，CPU 类换算为 GHz
        if field.endswith("_MHz") and isinstance(value, (int, float)):
            if cat != "memory" and value >= 1000:
                ghz = value / 1000
                return f"{ghz:.2f}".rstrip("0").rstrip(".") + " GHz"
            return f"{int(value)} MHz"
        if field.endswith("_GB") and isinstance(value, float):
            return f"{value:.1f} GB"
        if field.endswith("_MB") and isinstance(value, (int, float)):
            if value >= 1024:
                return f"{value / 1024:.1f} GB"
            return f"{int(value)} MB"
        return str(value)

    def _clear_content(self) -> None:
        """清空内容区"""
        while self._content_layout.count() > 1:
            item = self._content_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
