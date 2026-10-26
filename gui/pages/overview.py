"""
gui/pages/overview.py - 单屏画板页

QScrollArea 只负责兜底：字号自适应已经保证一屏放下，
只有搜索结果超长时才会出现滚动条。
"""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QScrollArea, QVBoxLayout, QWidget

from gui.board import BoardWidget


class OverviewPage(QWidget):
    """单屏硬件信息画板"""

    def __init__(self, parent=None):
        super().__init__(parent)

        self.board = BoardWidget()

        self._scroll = QScrollArea()
        self._scroll.setObjectName("boardScroll")
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._scroll.setWidget(self.board)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)
        lay.addWidget(self._scroll)

    # ------------------------------------------------------------ 数据

    def set_data(self, data: dict | None) -> None:
        self.board.set_data(data)

    def update_category(self, name: str, data) -> None:
        self.board.update_category(name, data)

    def set_pending(self, categories: list[str] | None) -> None:
        self.board.set_pending(categories)

    # ------------------------------------------------------------ 视图开关

    def set_mode(self, mode: str) -> None:
        self.board.set_mode(mode)

    def set_labels(self, labels: bool) -> None:
        self.board.set_labels(labels)

    def set_query(self, query: str) -> None:
        self.board.set_query(query)

    def layout_metrics(self) -> dict:
        return self.board.layout_metrics()
