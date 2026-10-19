"""
gui/main_window.py - 主窗口（便当格）

结构：

    顶栏：品牌 · 主机名 · 采集状态 · 缩放 · 时间 · 刷新 · 导出
    导航：总览 / 已启用的类别 / 设置
    内容：堆叠页面（总览、各类别详情、设置）

采集在后台线程执行，逐类回填；关闭全部类别时不会退化成「采集全部」。
"""
import json
import os
import platform
import socket
from datetime import datetime

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QApplication, QFileDialog, QFrame, QHBoxLayout, QLabel, QMainWindow,
    QPushButton, QStackedWidget, QVBoxLayout, QWidget,
)

from core.constants import ALL_CATEGORIES, CATEGORY_LABELS
from core.manager import CollectResult
from gui import icons, prefs, theme
from gui.components import action_button, clear_layout, icon_button, label
from gui.icons import qicon, rgba
from gui.pages.detail import DetailPage
from gui.pages.overview import OverviewPage
from gui.pages.settings import SettingsPage
from gui.worker import CollectWorker
from gui.zoom import ZOOM_MAX, ZOOM_MIN, ZOOM_STEP, get_zoom, set_zoom


class MainWindow(QMainWindow):
    """HWInfo 主窗口"""

    def __init__(self, auto_collect: bool = True):
        super().__init__()
        self.setWindowTitle("HWInfo")
        self.setMinimumSize(1080, 700)
        self._apply_default_geometry()
        self.setWindowIcon(qicon("cpu", theme.accent("cpu"), 64))

        self._worker: CollectWorker | None = None
        self._result: CollectResult | None = None
        self._pages: dict[str, QWidget] = {}
        self._nav_buttons: dict[str, QPushButton] = {}
        self._enabled: list[str] = prefs.enabled_categories()
        self._current = "overview"
        self._done = 0

        self._build_ui()
        self._apply_on_top(prefs.gui_prefs().get("on_top", False))
        self._install_shortcuts()
        if auto_collect:
            QTimer.singleShot(60, self.start_collect)

    # ------------------------------------------------------------ 界面

    def _build_ui(self) -> None:
        self._enabled = prefs.enabled_categories()
        app = QApplication.instance()
        if app is not None:
            app.setStyleSheet(theme.build_qss())

        root = QWidget()
        root.setObjectName("root")
        root.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setCentralWidget(root)

        outer = QVBoxLayout(root)
        outer.setContentsMargins(theme.sp(24), theme.sp(18), theme.sp(24), theme.sp(20))
        outer.setSpacing(0)

        outer.addWidget(self._build_top_bar())
        outer.addSpacing(theme.sp(10))
        outer.addWidget(self._build_nav())

        self._stack = QStackedWidget()
        outer.addSpacing(theme.sp(4))
        outer.addWidget(self._stack, 1)

        self._build_pages()
        self._goto(self._current if self._current in self._pages else "overview")

    def _build_top_bar(self) -> QWidget:
        bar = QWidget()
        lay = QHBoxLayout(bar)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(theme.sp(12))

        brand = QLabel("HWINFO")
        brand.setObjectName("brand")
        lay.addWidget(brand)

        host = QLabel(socket.gethostname().upper())
        host.setObjectName("hostText")
        lay.addWidget(host, 0, Qt.AlignmentFlag.AlignVCenter)

        self._status = QLabel()
        lay.addWidget(self._status)
        self._set_status("等待采集", theme.P["muted"])

        lay.addStretch()

        # 缩放
        lay.addWidget(icon_button("minus", "缩小界面", on_click=lambda: self._zoom(-ZOOM_STEP)))
        self._zoom_label = QLabel()
        self._zoom_label.setObjectName("metaText")
        self._zoom_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._zoom_label.setFixedWidth(theme.sp(44))
        lay.addWidget(self._zoom_label)
        lay.addWidget(icon_button("plus", "放大界面", on_click=lambda: self._zoom(ZOOM_STEP)))
        self._refresh_zoom_label()

        self._meta = QLabel("")
        self._meta.setObjectName("metaText")
        lay.addWidget(self._meta, 0, Qt.AlignmentFlag.AlignVCenter)

        lay.addWidget(action_button("刷新", "refresh", on_click=self.start_collect))
        lay.addWidget(action_button("导出", "export", on_click=self.export_json))
        return bar

    def _build_nav(self) -> QWidget:
        bar = QWidget()
        row = QHBoxLayout(bar)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(theme.sp(6))

        self._nav_buttons = {}
        keys = ["overview"] + [c for c in ALL_CATEGORIES if c in self._enabled] + ["settings"]
        for key in keys:
            text = "总览" if key == "overview" else (
                "设置" if key == "settings" else CATEGORY_LABELS.get(key, key))
            btn = QPushButton(text)
            btn.setObjectName("navItem")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda _=False, k=key: self._goto(k))
            row.addWidget(btn)
            self._nav_buttons[key] = btn
        row.addStretch()
        return bar

    def _build_pages(self) -> None:
        self._pages = {}
        while self._stack.count():
            widget = self._stack.widget(0)
            self._stack.removeWidget(widget)
            widget.deleteLater()

        overview = OverviewPage()
        overview.set_pending([])
        self._pages["overview"] = overview
        self._stack.addWidget(overview)

        for cat in self._enabled:
            page = DetailPage(cat)
            page.refresh_requested.connect(lambda name: self.start_collect())
            self._pages[cat] = page
            self._stack.addWidget(page)

        settings = SettingsPage()
        settings.settings_saved.connect(self._on_settings_saved)
        settings.appearance_changed.connect(self._on_appearance_changed)
        settings.on_top_changed.connect(self._apply_on_top)
        self._pages["settings"] = settings
        self._stack.addWidget(settings)

    def _goto(self, key: str) -> None:
        page = self._pages.get(key)
        if page is None:
            # 类别被关闭后导航项不存在，退回总览
            key = "overview"
            page = self._pages["overview"]
        self._current = key
        self._stack.setCurrentWidget(page)
        for name, btn in self._nav_buttons.items():
            btn.setObjectName("navActive" if name == key else "navItem")
            btn.style().unpolish(btn)
            btn.style().polish(btn)

    # ------------------------------------------------------------ 采集

    def start_collect(self) -> None:
        if self._worker is not None and self._worker.isRunning():
            return

        enabled = prefs.enabled_categories()
        self._enabled = enabled

        if not enabled:
            # 明确「全部关闭」：不采集任何类别，而不是退化为采集全部
            overview: OverviewPage = self._pages["overview"]
            overview.set_pending([])
            overview.set_meta("已在设置中关闭全部类别")
            self._result = CollectResult()
            self._set_status("已关闭全部类别", theme.P["warn"])
            return

        overview = self._pages["overview"]
        overview.set_pending(enabled)
        for cat in enabled:
            page = self._pages.get(cat)
            if isinstance(page, DetailPage):
                page.set_pending()

        self._set_status("采集中", theme.accent("cpu"))
        self._meta.setText("")

        self._worker = CollectWorker(enabled, timeout=prefs.get_timeout(), parent=self)
        self._worker.started_categories.connect(self._on_started)
        self._worker.category_done.connect(self._on_category_done)
        self._worker.collect_finished.connect(self._on_collect_finished)
        self._worker.error.connect(self._on_collect_error)
        self._worker.start()

    def _on_started(self, categories: list) -> None:
        self._done = 0
        self._set_status(f"采集中 0 / {len(categories)}", theme.accent("cpu"))

    def _on_category_done(self, name: str, data, elapsed: float) -> None:
        overview: OverviewPage = self._pages.get("overview")
        if isinstance(overview, OverviewPage):
            overview.update_category(name, data)
        page = self._pages.get(name)
        if isinstance(page, DetailPage):
            page.update_category(name, data)
        self._done += 1
        self._set_status(f"采集中 {self._done} / {len(self._enabled)}",
                         theme.accent("cpu"))

    def _on_collect_finished(self, result: CollectResult) -> None:
        self._result = result
        overview: OverviewPage = self._pages.get("overview")
        if isinstance(overview, OverviewPage):
            overview.update_result(result)
        for cat in self._enabled:
            page = self._pages.get(cat)
            if isinstance(page, DetailPage):
                page.update_result(result)

        ok = len(result.data)
        total = ok + len(result.errors)
        if result.errors:
            self._set_status(f"完成 {ok}/{total} · {len(result.errors)} 个失败",
                             theme.P["warn"])
        else:
            self._set_status(f"完成 {ok}/{total}", theme.P["ok"])
        self._meta.setText(f"采集于 {datetime.now().strftime('%H:%M')} · "
                           f"{result.elapsed_seconds:.2f}s")
        self._finish_worker()

    def _on_collect_error(self, message: str) -> None:
        self._set_status("采集失败", theme.P["err"])
        self._meta.setText(message[:60])
        self._finish_worker()

    def _finish_worker(self) -> None:
        worker = self._worker
        self._worker = None
        if worker is not None:
            worker.wait(500)
            worker.deleteLater()

    # ------------------------------------------------------------ 设置 / 外观

    def _on_settings_saved(self) -> None:
        QTimer.singleShot(0, lambda: self._rebuild(recollect=True))

    def _on_appearance_changed(self) -> None:
        QTimer.singleShot(0, lambda: self._rebuild(recollect=False))

    def _apply_on_top(self, value: bool) -> None:
        visible = self.isVisible()
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, bool(value))
        if visible:
            self.show()

    def _rebuild(self, recollect: bool = False) -> None:
        """重建整个界面（主题 / 密度 / 缩放 / 类别开关变化后调用）"""
        key = self._current
        self._pages = {}
        self._nav_buttons = {}
        self._build_ui()
        self._goto(key)
        self._restore_result()
        if recollect:
            self.start_collect()
        elif self._result is not None:
            self._set_status(f"完成 {len(self._result.data)} 类", theme.P["ok"])

    def _restore_result(self) -> None:
        if self._result is None:
            return
        overview = self._pages.get("overview")
        if isinstance(overview, OverviewPage):
            overview.update_result(self._result)
        for cat in self._enabled:
            page = self._pages.get(cat)
            if isinstance(page, DetailPage):
                page.update_result(self._result)

    # ------------------------------------------------------------ 缩放 / 导出

    def _zoom(self, delta: float) -> None:
        value = round(min(ZOOM_MAX, max(ZOOM_MIN, get_zoom() + delta)), 2)
        if abs(value - get_zoom()) < 1e-6:
            return
        set_zoom(value)
        prefs.set_gui_pref("zoom", value)
        self._refresh_zoom_label()
        QTimer.singleShot(0, lambda: self._rebuild(recollect=False))

    def _refresh_zoom_label(self) -> None:
        self._zoom_label.setText(f"{round(get_zoom() * 100)}%")

    def export_json(self) -> None:
        if self._result is None:
            self._flash_status("暂无可导出的数据", theme.P["warn"])
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "导出采集结果", f"hwinfo-{datetime.now():%Y%m%d-%H%M}.json",
            "JSON 文件 (*.json);;所有文件 (*.*)")
        if not path:
            return
        payload = {
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "elapsed_seconds": self._result.elapsed_seconds,
            "data": self._result.data,
            "errors": self._result.errors,
            "warnings": self._result.warnings,
            "timings": self._result.timings,
        }
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(payload, f, ensure_ascii=False, indent=2, default=str)
        except OSError as exc:
            self._flash_status(f"导出失败：{exc}", theme.P["err"])
            return
        self._flash_status(f"已导出 {os.path.basename(path)}", theme.P["ok"])

    def _set_status(self, text: str, color: str) -> None:
        self._status.setText(text)
        self._status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._status.setMinimumHeight(theme.sp(22))
        self._status.setStyleSheet(
            f"background-color: {rgba(color, 0.12)}; color: {color};"
            f"border-radius: {theme.sp(9)}px; font-size: {theme.sp(11)}px;"
            f"padding: 0 {theme.sp(10)}px;"
        )

    def _flash_status(self, text: str, color: str) -> None:
        self._set_status(text, color)
        QTimer.singleShot(2600, lambda: self._set_status(
            "就绪" if self._result else "等待采集", theme.P["muted"]))

    def _install_shortcuts(self) -> None:
        QShortcut(QKeySequence("F5"), self, activated=self.start_collect)
        QShortcut(QKeySequence("Ctrl+E"), self, activated=self.export_json)
        QShortcut(QKeySequence("Ctrl+Plus"), self, activated=lambda: self._zoom(ZOOM_STEP))
        QShortcut(QKeySequence("Ctrl+Minus"), self, activated=lambda: self._zoom(-ZOOM_STEP))

    def _apply_default_geometry(self) -> None:
        """默认窗口尺寸：按可用屏幕自适应。

        高 DPI 下 1360×860 逻辑像素只占屏幕一小块，把尺寸写死会让总览
        的最后一行挤出可视区（必须滚动才能看全）。
        """
        preferred_w, preferred_h = 1360, 920
        screen = QApplication.primaryScreen()
        available = screen.availableGeometry() if screen is not None else None
        if available is None:
            self.resize(preferred_w, preferred_h)
            return
        width = min(preferred_w, max(1080, available.width() - 120))
        height = min(preferred_h, max(700, available.height() - 90))
        self.resize(width, height)
        self.move(available.x() + (available.width() - width) // 2,
                  available.y() + (available.height() - height) // 2)

    def closeEvent(self, event) -> None:  # noqa: N802
        if self._worker is not None and self._worker.isRunning():
            self._worker.requestInterruption()
            self._worker.wait(1500)
        super().closeEvent(event)
