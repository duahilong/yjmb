"""
gui/pages/overview.py - 总览页（配置概览）
"""
from PySide6.QtWidgets import (
    QLabel, QScrollArea, QWidget, QVBoxLayout, QGroupBox, QFormLayout,
)
from PySide6.QtCore import Qt

from gui.pages.base_page import BasePage
from core.constants import ALL_CATEGORIES, BRIEF_FIELDS_MAP, ITEM_BRIEF_FIELDS_MAP


# 类别中文名
CATEGORY_LABELS = {
    "os": "操作系统",
    "motherboard": "主板",
    "cpu": "处理器",
    "memory": "内存",
    "gpu": "显卡",
    "storage": "存储",
    "network": "网络",
    "audio": "音频",
    "monitor": "显示器",
}


class OverviewPage(BasePage):
    """总览页：每个类别取关键字段组成摘要"""

    def __init__(self, parent=None):
        super().__init__(parent)

        title = QLabel("配置概览")
        title.setStyleSheet("font-size: 18px; font-weight: bold; margin-bottom: 8px;")
        self._layout.addWidget(title)

        # 可滚动内容区
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        self._content = QWidget()
        self._content_layout = QVBoxLayout(self._content)
        self._content_layout.setContentsMargins(0, 0, 0, 0)
        self._content_layout.addStretch()
        self._scroll.setWidget(self._content)
        self._layout.addWidget(self._scroll)

    def update_data(self, data: dict) -> None:
        """接收全部采集数据，生成摘要"""
        self._clear_content()

        if not data:
            self._content_layout.insertWidget(0, self._make_placeholder("正在采集..."))
            return

        for cat in ALL_CATEGORIES:
            cat_data = data.get(cat)
            if cat_data is None:
                continue

            label = CATEGORY_LABELS.get(cat, cat)
            summary = self._extract_summary(cat, cat_data)

            if summary:
                group = QGroupBox(label)
                form = QFormLayout(group)
                for key, value in summary:
                    key_label = QLabel(f"{key}:")
                    key_label.setStyleSheet("font-weight: bold;")
                    form.addRow(key_label, QLabel(str(value)))
                self._content_layout.insertWidget(
                    self._content_layout.count() - 1, group
                )

    def _extract_summary(self, cat: str, cat_data) -> list[tuple[str, str]]:
        """提取类别摘要字段"""
        result = []

        if isinstance(cat_data, dict):
            # 检查是否为「设备列表型」dict（如 {"显卡列表": [{...}, ...]}）
            device_list = self._find_device_list(cat_data)
            if device_list is not None:
                return self._extract_device_list_summary(cat, device_list)

            # 纯标量 dict（cpu、os、motherboard、memory）
            fields = BRIEF_FIELDS_MAP.get(cat, [])
            if fields:
                for f in fields:
                    if f in cat_data and cat_data[f] is not None:
                        result.append((f, cat_data[f]))
            else:
                for i, (k, v) in enumerate(cat_data.items()):
                    if i >= 3:
                        break
                    if v is not None and not isinstance(v, (dict, list)):
                        result.append((k, v))

        elif isinstance(cat_data, list):
            return self._extract_device_list_summary(cat, cat_data)

        return result

    def _find_device_list(self, data: dict) -> list | None:
        """从 dict 中找到第一个 list[dict] 值（设备列表）"""
        for value in data.values():
            if isinstance(value, list) and value and isinstance(value[0], dict):
                return value
        return None

    def _extract_device_list_summary(self, cat: str, devices: list) -> list[tuple[str, str]]:
        """从设备列表中提取摘要：名称 + 驱动版本"""
        result = []
        item_fields = ITEM_BRIEF_FIELDS_MAP.get(cat, [])

        for i, item in enumerate(devices):
            if not isinstance(item, dict):
                continue

            # 确定设备名称
            name = (
                item.get("名称")
                or item.get("型号")
                or f"设备 {i + 1}"
            )

            # 组装附加信息
            details = []
            # 驱动版本（如果有）
            if item.get("驱动版本"):
                details.append(f"驱动: {item['驱动版本']}")
            # 其余 brief 字段
            if item_fields:
                for f in item_fields[1:]:  # 跳过第一个（通常是名称字段）
                    if f == "驱动版本":
                        continue  # 已单独处理
                    if f in item and item[f] is not None:
                        details.append(f"{f}: {item[f]}")
            else:
                # 没有定义 brief 字段，取几个有意义的
                for f in ["容量_GB", "显存_MB", "分辨率", "状态", "接口"]:
                    if f in item and item[f] is not None:
                        details.append(f"{f}: {item[f]}")
                        if len(details) >= 3:
                            break

            result.append((str(name), " | ".join(details) if details else ""))

        return result

    def _clear_content(self) -> None:
        """清空内容区"""
        while self._content_layout.count() > 1:
            item = self._content_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
