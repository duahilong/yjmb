"""
gui/widgets/info_table.py - 键值对表格组件
"""
from PySide6.QtWidgets import (
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
)
from PySide6.QtCore import Qt


class InfoTable(QTableWidget):
    """两列键值对表格：字段名 | 值"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setColumnCount(2)
        self.setHorizontalHeaderLabels(["字段", "值"])
        self.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setAlternatingRowColors(True)
        self.verticalHeader().setVisible(False)

    def set_data(self, data: dict) -> None:
        """从字典填充表格"""
        rows = self._flatten(data)
        self.setRowCount(len(rows))

        for i, (key, value) in enumerate(rows):
            key_item = QTableWidgetItem(str(key))
            key_item.setFont(self._bold_font())
            self.setItem(i, 0, key_item)
            self.setItem(i, 1, QTableWidgetItem(str(value)))

    def _flatten(self, data: dict, prefix: str = "") -> list[tuple[str, str]]:
        """将嵌套 dict 展平为 (key, value) 列表"""
        rows = []
        for key, value in data.items():
            display_key = f"{prefix}{key}" if not prefix else f"{prefix} > {key}"

            if isinstance(value, dict):
                # 嵌套 dict 递归展开
                rows.extend(self._flatten(value, display_key))
            elif isinstance(value, list):
                # 列表值：如果是简单列表，逗号分隔显示
                if all(not isinstance(v, (dict, list)) for v in value):
                    rows.append((display_key, ", ".join(str(v) for v in value)))
                else:
                    # 复杂列表，显示数量
                    rows.append((display_key, f"[{len(value)} 项]"))
            elif value is None:
                rows.append((display_key, "-"))
            else:
                rows.append((display_key, str(value)))

        return rows

    @staticmethod
    def _bold_font():
        from PySide6.QtGui import QFont
        font = QFont()
        font.setBold(True)
        return font
