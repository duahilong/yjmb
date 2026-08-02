"""
gui/main_window.py - 主窗口
"""
from PySide6.QtWidgets import (
    QMainWindow, QTreeWidget, QTreeWidgetItem,
    QStackedWidget, QSplitter, QStatusBar, QToolBar,
    QLabel, QWidget, QVBoxLayout,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QAction

from core.constants import ALL_CATEGORIES, ORDER_MAP
from core.manager import CollectResult


# 类别中文名映射
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


class MainWindow(QMainWindow):
    """HWInfo 主窗口"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("HWInfo - Windows 硬件检测工具")
        self.resize(1000, 700)

        self._worker = None
        self._result: CollectResult | None = None

        self._setup_ui()
        self._setup_toolbar()
        self._setup_statusbar()

        # 启动后自动采集
        self._start_collect()

    def _setup_ui(self) -> None:
        """构建主界面布局"""
        # 中心分割器：左侧树 + 右侧页面
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # 左侧导航树
        self._tree = QTreeWidget()
        self._tree.setHeaderHidden(True)
        self._tree.setMinimumWidth(160)
        self._tree.setMaximumWidth(220)

        # 右侧页面栈（先于树构建，避免信号触发时页面未就绪）
        self._stack = QStackedWidget()
        self._build_pages()

        # 构建树并连接信号
        self._build_tree()
        self._tree.currentItemChanged.connect(self._on_tree_selection)

        splitter.addWidget(self._tree)
        splitter.addWidget(self._stack)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)

        self.setCentralWidget(splitter)

    def _build_tree(self) -> None:
        """构建左侧导航树"""
        # 总览节点
        overview_item = QTreeWidgetItem(["总览"])
        overview_item.setData(0, Qt.ItemDataRole.UserRole, "overview")
        self._tree.addTopLevelItem(overview_item)

        # 硬件类别节点（按 order 排序）
        hw_parent = QTreeWidgetItem(["硬件信息"])
        hw_parent.setExpanded(True)
        self._tree.addTopLevelItem(hw_parent)

        for cat in ALL_CATEGORIES:
            label = CATEGORY_LABELS.get(cat, cat)
            item = QTreeWidgetItem([label])
            item.setData(0, Qt.ItemDataRole.UserRole, cat)
            hw_parent.addChild(item)

        # 设置节点
        settings_item = QTreeWidgetItem(["设置"])
        settings_item.setData(0, Qt.ItemDataRole.UserRole, "settings")
        self._tree.addTopLevelItem(settings_item)

        # 默认选中总览
        self._tree.setCurrentItem(overview_item)

    def _build_pages(self) -> None:
        """构建右侧页面栈"""
        from gui.pages.overview import OverviewPage
        from gui.pages.detail_page import DetailPage
        from gui.pages.settings import SettingsPage

        # 总览页
        self._overview_page = OverviewPage()
        self._stack.addWidget(self._overview_page)

        # 每个硬件类别一个详情页
        self._detail_pages: dict[str, DetailPage] = {}
        for cat in ALL_CATEGORIES:
            page = DetailPage(cat, CATEGORY_LABELS.get(cat, cat))
            self._detail_pages[cat] = page
            self._stack.addWidget(page)

        # 设置页
        self._settings_page = SettingsPage()
        self._stack.addWidget(self._settings_page)

    def _setup_toolbar(self) -> None:
        """工具栏"""
        toolbar = QToolBar("主工具栏")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        self._refresh_action = QAction("刷新", self)
        self._refresh_action.setShortcut("F5")
        self._refresh_action.triggered.connect(self._start_collect)
        toolbar.addAction(self._refresh_action)

        self._export_action = QAction("导出 JSON", self)
        self._export_action.triggered.connect(self._export_json)
        toolbar.addAction(self._export_action)

    def _setup_statusbar(self) -> None:
        """状态栏"""
        self._status_label = QLabel("就绪")
        self.statusBar().addWidget(self._status_label)

    def _on_tree_selection(self, current: QTreeWidgetItem, _previous) -> None:
        """树节点切换 → 切换右侧页面"""
        if not current:
            return
        key = current.data(0, Qt.ItemDataRole.UserRole)
        if key == "overview":
            self._stack.setCurrentWidget(self._overview_page)
        elif key == "settings":
            self._stack.setCurrentWidget(self._settings_page)
        elif key in self._detail_pages:
            self._stack.setCurrentWidget(self._detail_pages[key])

    def _start_collect(self) -> None:
        """启动后台采集"""
        if self._worker and self._worker.isRunning():
            return

        from gui.worker import CollectWorker

        self._refresh_action.setEnabled(False)
        self._status_label.setText("正在采集...")

        self._worker = CollectWorker(parent=self)
        self._worker.progress.connect(self._on_progress)
        self._worker.finished.connect(self._on_collect_done)
        self._worker.start()

    def _on_progress(self, msg: str) -> None:
        """采集进度更新"""
        self._status_label.setText(msg)

    def _on_collect_done(self, result: CollectResult) -> None:
        """采集完成，分发数据到各页面"""
        self._result = result
        self._refresh_action.setEnabled(True)

        # 更新状态栏
        err_count = len(result.errors)
        warn_count = len(result.warnings)
        status = f"采集完成 | 耗时 {result.elapsed_seconds}s | {err_count} 错误 | {warn_count} 警告"
        self._status_label.setText(status)

        # 分发数据到详情页
        for cat, page in self._detail_pages.items():
            data = result.data.get(cat)
            page.update_data(data)

        # 更新总览页
        self._overview_page.update_data(result.data)

    def _export_json(self) -> None:
        """导出 JSON 到文件"""
        if not self._result:
            return

        from PySide6.QtWidgets import QFileDialog
        import json

        path, _ = QFileDialog.getSaveFileName(
            self, "导出 JSON", "hwinfo_report.json", "JSON 文件 (*.json)"
        )
        if not path:
            return

        from formatters.json_fmt import JsonFormatter
        formatter = JsonFormatter()
        output = formatter.render(self._result, brief=False)

        with open(path, "w", encoding="utf-8") as f:
            f.write(output)

        self._status_label.setText(f"已导出: {path}")
