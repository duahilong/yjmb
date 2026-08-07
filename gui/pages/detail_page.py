"""
gui/pages/detail_page.py - 通用硬件详情页

根据数据结构自动选择渲染方式：
- 纯 dict（如 cpu、os）→ InfoTable 键值对表格
- 含列表的 dict（如 memory 有"插槽"列表）→ 上方表格 + 下方设备卡片
- 纯列表（如 gpu、storage）→ DeviceCardList 多设备卡片
"""
from PySide6.QtWidgets import QLabel, QScrollArea, QWidget, QVBoxLayout

from gui.pages.base_page import BasePage
from gui.widgets.info_table import InfoTable
from gui.widgets.device_card import DeviceCardList


# 列表型类别：数据本身是 list[dict]
LIST_CATEGORIES = {"gpu", "storage", "network", "audio", "monitor"}

# 列表型数据的标题字段
TITLE_FIELDS = {
    "gpu": "名称",
    "storage": "型号",
    "network": "名称",
    "audio": "名称",
    "monitor": "型号",
    "memory": "插槽",
}


class DetailPage(BasePage):
    """通用硬件详情页"""

    def __init__(self, category: str, label: str, parent=None):
        super().__init__(parent)
        self._category = category
        self._label = label

        # 标题（样式由全局 QSS #pageTitle 控制）
        title = self._make_title(label)

        # 内容区（可滚动）
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

    def update_data(self, data) -> None:
        """接收数据并渲染"""
        self._clear_content()

        if data is None:
            self._content_layout.insertWidget(
                0, self._make_placeholder(f"{self._label} 数据暂未采集")
            )
            return

        if isinstance(data, list):
            # 纯列表型（gpu、storage 等）
            self._render_list(data)
        elif isinstance(data, dict):
            self._render_dict(data)
        else:
            self._content_layout.insertWidget(0, self._make_placeholder("未知数据格式"))

    def _render_dict(self, data: dict) -> None:
        """渲染 dict 型数据"""
        # 分离：标量字段 vs 列表字段
        scalar_fields = {}
        list_fields = {}

        for key, value in data.items():
            if isinstance(value, list) and value and isinstance(value[0], dict):
                list_fields[key] = value
            else:
                scalar_fields[key] = value

        # 标量部分 → InfoTable
        if scalar_fields:
            table = InfoTable()
            table.set_data(scalar_fields)
            self._content_layout.insertWidget(0, table)

        # 列表部分 → DeviceCardList
        for key, items in list_fields.items():
            section_label = QLabel(f"▎{key}")
            section_label.setObjectName("sectionTitle")
            self._content_layout.addWidget(section_label)

            card_list = DeviceCardList()
            title_field = TITLE_FIELDS.get(self._category, "名称")
            card_list.set_devices(items, title_field)
            self._content_layout.addWidget(card_list)

    def _render_list(self, data: list) -> None:
        """渲染纯列表型数据"""
        if not data:
            self._content_layout.insertWidget(0, self._make_placeholder("未检测到设备"))
            return

        card_list = DeviceCardList()
        title_field = TITLE_FIELDS.get(self._category, "名称")
        card_list.set_devices(data, title_field)
        self._content_layout.insertWidget(0, card_list)

    def _clear_content(self) -> None:
        """清空内容区"""
        while self._content_layout.count() > 1:  # 保留末尾 stretch
            item = self._content_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
