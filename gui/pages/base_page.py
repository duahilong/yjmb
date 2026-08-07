"""
gui/pages/base_page.py - 页面基类
"""
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Qt


class BasePage(QWidget):
    """所有页面的基类"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(16, 16, 16, 16)

    def update_data(self, data) -> None:
        """子类重写：接收数据并刷新 UI"""
        raise NotImplementedError

    def _make_title(self, text: str) -> QLabel:
        """创建页面标题（样式统一由全局 QSS #pageTitle 控制，随缩放同步）"""
        label = QLabel(text)
        label.setObjectName("pageTitle")
        self._layout.addWidget(label)
        return label

    def _clear_layout(self) -> None:
        """清空当前布局中的所有组件"""
        while self._layout.count():
            item = self._layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
            elif item.layout():
                self._clear_sub_layout(item.layout())

    def _clear_sub_layout(self, layout) -> None:
        """递归清空子布局"""
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
            elif item.layout():
                self._clear_sub_layout(item.layout())

    def _make_placeholder(self, text: str = "暂无数据") -> QLabel:
        """创建占位提示标签（样式由全局 QSS #placeholder 控制）"""
        label = QLabel(text)
        label.setObjectName("placeholder")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        return label
