"""
gui/main_window.py - 主窗口
"""
import os

from PySide6.QtWidgets import (
    QMainWindow, QListWidget, QListWidgetItem,
    QStackedWidget, QSplitter, QStatusBar, QToolBar,
    QLabel, QWidget, QVBoxLayout, QToolButton,
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QAction

from core.constants import ALL_CATEGORIES, CATEGORY_LABELS
from core.manager import CollectResult
from config.settings import Settings
from gui.app import resource_path
from gui.zoom import (
    ZOOM_MIN, ZOOM_MAX, ZOOM_STEP, scaled, scale_qss, set_zoom,
)


# 导航图标（Unicode 符号）
NAV_ICONS = {
    "overview": "🏠",
    "os": "💻",
    "motherboard": "🔧",
    "cpu": "⚡",
    "memory": "📦",
    "gpu": "🎮",
    "storage": "💾",
    "network": "🌐",
    "audio": "🔊",
    "monitor": "🖥️",
    "settings": "⚙️",
}

# 导航尺寸基准（缩放系数为 1.0 时的值）
NAV_WIDTH = 180
NAV_ITEM_HEIGHT = 38


class MainWindow(QMainWindow):
    """HWInfo 主窗口"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("HWInfo - Windows 硬件检测工具")
        # 始终置顶显示（浮于其他窗口之上）
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, True)
        # 默认窗口尺寸（基准 1000x700，随缩放系数放大，120% 时为 1200x840）
        self.resize(scaled(1000), scaled(700))

        self._worker = None
        self._result: CollectResult | None = None
        self._settings = Settings()
        self._zoom = 1.2  # 默认 120%，不持久化，每次启动恢复默认

        self._setup_ui()
        self._setup_toolbar()
        self._setup_statusbar()

        # 应用默认缩放（120%）：确保 QSS 与固定尺寸初始一致
        self._apply_zoom(1.2)

        # 设置页保存后：重建导航 + 重新采集
        self._settings_page.settings_saved.connect(self._on_settings_saved)

        # 启动后自动采集
        self._start_collect()

    def _setup_ui(self) -> None:
        """构建主界面布局"""
        # 中心分割器：左侧导航 + 右侧页面
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(0)  # 无可见分割线

        # 左侧导航列表
        self._nav = QListWidget()
        self._nav.setObjectName("navList")
        self._nav.setFixedWidth(scaled(NAV_WIDTH))
        self._nav.setIconSize(QSize(scaled(20), scaled(20)))
        self._nav.setSpacing(scaled(2))

        # 右侧页面栈（先于导航构建，避免信号触发时页面未就绪）
        self._stack = QStackedWidget()
        self._build_pages()

        # 构建导航并连接信号
        self._rebuild_nav()
        self._nav.currentRowChanged.connect(self._on_nav_selection)

        splitter.addWidget(self._nav)
        splitter.addWidget(self._stack)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)

        self.setCentralWidget(splitter)

    def _enabled_categories(self) -> list[str]:
        """当前配置中启用的硬件类别（按 order 排序）"""
        return [c for c in ALL_CATEGORIES if self._settings.is_display_enabled(c)]

    def _current_nav_key(self) -> str | None:
        """当前选中的导航项 key"""
        row = self._nav.currentRow()
        if 0 <= row < len(self._nav_keys):
            return self._nav_keys[row]
        return None

    def _rebuild_nav(self) -> None:
        """构建左侧扁平导航列表（按当前显示配置过滤）"""
        current_key = self._current_nav_key()

        self._nav.blockSignals(True)
        self._nav.clear()
        self._nav_keys = []

        # 导航项顺序：总览 + 启用的硬件类别 + 设置
        nav_items = [("overview", "总览")]
        for cat in self._enabled_categories():
            nav_items.append((cat, CATEGORY_LABELS.get(cat, cat)))
        nav_items.append(("settings", "设置"))

        for key, label in nav_items:
            icon_text = NAV_ICONS.get(key, "•")
            item = QListWidgetItem(f"  {icon_text}  {label}")
            item.setSizeHint(QSize(scaled(NAV_WIDTH - 20), scaled(NAV_ITEM_HEIGHT)))
            self._nav.addItem(item)
            self._nav_keys.append(key)

        # 恢复之前的选中页（缩放重建时保持当前页面）
        if current_key in self._nav_keys:
            self._nav.setCurrentRow(self._nav_keys.index(current_key))
        else:
            self._nav.setCurrentRow(0)
        self._nav.blockSignals(False)

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
        """状态栏：左侧缩放控制（− / 百分比 / +），右侧状态信息"""
        self._status_label = QLabel("就绪")
        self.statusBar().addWidget(self._status_label)

        # 左下角缩放控制
        self._zoom_out_btn = QToolButton()
        self._zoom_out_btn.setText("-")
        self._zoom_out_btn.setToolTip("缩小界面 (Ctrl+-)")
        self._zoom_out_btn.clicked.connect(lambda: self._zoom_by(-ZOOM_STEP))

        self._zoom_label = QLabel("100%")
        self._zoom_label.setObjectName("zoomLabel")
        self._zoom_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._zoom_in_btn = QToolButton()
        self._zoom_in_btn.setText("+")
        self._zoom_in_btn.setToolTip("放大界面 (Ctrl+=)")
        self._zoom_in_btn.clicked.connect(lambda: self._zoom_by(ZOOM_STEP))

        self.statusBar().addWidget(self._zoom_out_btn)
        self.statusBar().addWidget(self._zoom_label)
        self.statusBar().addWidget(self._zoom_in_btn)

        # 快捷键：Ctrl+= 放大 / Ctrl+- 缩小 / Ctrl+0 恢复默认
        zoom_in_action = QAction("放大界面", self)
        zoom_in_action.setShortcut("Ctrl+=")
        zoom_in_action.triggered.connect(lambda: self._zoom_by(ZOOM_STEP))
        self.addAction(zoom_in_action)

        zoom_out_action = QAction("缩小界面", self)
        zoom_out_action.setShortcut("Ctrl+-")
        zoom_out_action.triggered.connect(lambda: self._zoom_by(-ZOOM_STEP))
        self.addAction(zoom_out_action)

        reset_zoom_action = QAction("恢复默认缩放", self)
        reset_zoom_action.setShortcut("Ctrl+0")
        reset_zoom_action.triggered.connect(self._reset_zoom)
        self.addAction(reset_zoom_action)

    def _on_nav_selection(self, row: int) -> None:
        """导航切换 → 切换右侧页面"""
        if row < 0 or row >= len(self._nav_keys):
            return
        key = self._nav_keys[row]
        if key == "overview":
            self._stack.setCurrentWidget(self._overview_page)
        elif key == "settings":
            self._stack.setCurrentWidget(self._settings_page)
        elif key in self._detail_pages:
            self._stack.setCurrentWidget(self._detail_pages[key])

    def _start_collect(self) -> None:
        """启动后台采集（仅采集配置中启用的类别）"""
        if self._worker and self._worker.isRunning():
            return

        from gui.worker import CollectWorker

        self._refresh_action.setEnabled(False)
        self._status_label.setText("正在采集...")

        self._worker = CollectWorker(categories=self._enabled_categories(), parent=self)
        self._worker.progress.connect(self._on_progress)
        self._worker.collect_finished.connect(self._on_collect_done)
        self._worker.error.connect(self._on_collect_error)
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

    def _on_collect_error(self, msg: str) -> None:
        """采集线程异常兜底"""
        self._refresh_action.setEnabled(True)
        self._status_label.setText(f"采集失败: {msg}")

    def _on_settings_saved(self) -> None:
        """设置页保存后：重新加载配置、重建导航、重新采集"""
        self._settings = Settings()
        self._rebuild_nav()
        self._start_collect()

    # ========================================================
    # 界面缩放控制
    # ========================================================

    def _zoom_by(self, delta: float) -> None:
        """按步进调整缩放系数"""
        new_zoom = round((self._zoom + delta) * 10) / 10
        new_zoom = min(ZOOM_MAX, max(ZOOM_MIN, new_zoom))
        self._apply_zoom(new_zoom)

    def _reset_zoom(self) -> None:
        """恢复默认缩放（120%）"""
        self._apply_zoom(1.2)

    def _apply_zoom(self, zoom: float) -> None:
        """应用缩放：全局 QSS + Python 侧固定尺寸同步换算，保持布局协调"""
        self._zoom = zoom
        set_zoom(zoom)

        # 1. 全局 QSS 重新生成（字体、间距、控件尺寸全部按比例缩放）
        qss_text = self._load_base_qss()
        app = self._app()
        if qss_text:
            app.setStyleSheet(scale_qss(qss_text, zoom))

        # 2. Python 侧固定尺寸
        self._nav.setFixedWidth(scaled(NAV_WIDTH))
        self._nav.setIconSize(QSize(scaled(20), scaled(20)))
        self._nav.setSpacing(scaled(2))
        self._rebuild_nav()

        # 3. 总览表格按新尺寸重渲染（行高/列宽随缩放）
        if self._result:
            self._overview_page.update_data(self._result.data)

        # 4. 状态栏显示与边界
        self._zoom_label.setText(f"{int(round(zoom * 100))}%")
        self._zoom_out_btn.setEnabled(zoom > ZOOM_MIN)
        self._zoom_in_btn.setEnabled(zoom < ZOOM_MAX)

    @staticmethod
    def _app():
        """获取当前 QApplication 实例"""
        from PySide6.QtWidgets import QApplication
        return QApplication.instance()

    def _load_base_qss(self) -> str:
        """读取原始 QSS 文本（打包环境经 _MEIPASS 定位）"""
        qss_path = resource_path(os.path.join("gui", "resources", "style.qss"))
        if os.path.exists(qss_path):
            with open(qss_path, "r", encoding="utf-8") as f:
                return f.read()
        return ""

    def closeEvent(self, event) -> None:
        """窗口关闭时安全停止后台采集线程。

        采集线程可能被 WMI COM 调用阻塞（最长约 15s，由 manager 超时兜底），
        wait() 超时后不能直接放行关闭——QThread 对象随窗口销毁会触发
        "QThread: Destroyed while thread is still running" 崩溃。
        此时拒绝本次关闭并挂接线程结束回调，待线程退出后自动关窗。
        """
        if self._worker and self._worker.isRunning():
            self._worker.requestInterruption()
            if not self._worker.wait(3000):
                if not getattr(self, "_close_pending", False):
                    self._close_pending = True
                    # QThread 内建 finished：run() 返回时发出，队列连接回主线程
                    self._worker.finished.connect(self.close)
                event.ignore()
                return
        event.accept()

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
