"""
gui/main_window.py - 主窗口（单页画板）

结构：

    顶栏：HWInfo · 主机 / 系统 · 采集状态 · 全部|精简 · 标签 · 搜索 · 计数 · 刷新/导出/设置
    内容：一张画板，9 个类别一屏放下，不滚动

采集在后台线程执行，逐类回填；关闭全部类别时不会退化成「采集全部」。
"""
import json
import os
import socket
from datetime import datetime

from PySide6.QtCore import QEvent, QSize, Qt, QTimer
from PySide6.QtGui import QFontMetrics, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QApplication, QButtonGroup, QDialog, QFileDialog, QHBoxLayout, QLabel,
    QLineEdit, QMainWindow, QPushButton, QSizePolicy, QToolButton, QVBoxLayout,
    QWidget,
)

from core.manager import CollectResult
from gui import prefs, theme
from gui.icons import app_icon, qicon
from gui.pages.overview import OverviewPage
from gui.pages.settings import SettingsDialog
from gui.worker import CollectWorker
from gui.zoom import ZOOM_MAX, ZOOM_MIN, ZOOM_STEP, get_zoom, set_zoom


class ElidedLabel(QLabel):
    """单行标签：太窄时中间省略，不让顶栏被长主机名撑开"""

    def __init__(self, text: str = "", parent=None):
        super().__init__(parent)
        self._full = ""
        self.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        self.setMinimumWidth(0)
        self.setText(text)

    def setText(self, text: str) -> None:  # noqa: N802
        self._full = text or ""
        self._apply()

    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)
        self._apply()

    def changeEvent(self, event) -> None:  # noqa: N802
        super().changeEvent(event)
        if event.type() == QEvent.Type.FontChange and hasattr(self, "_full"):
            self._apply()

    def _apply(self) -> None:
        metrics = QFontMetrics(self.font())
        width = max(0, self.width() - 2)
        super().setText(metrics.elidedText(
            self._full, Qt.TextElideMode.ElideRight, width) if width else "")


class MainWindow(QMainWindow):
    """HWInfo 主窗口"""

    def __init__(self, auto_collect: bool = True):
        super().__init__()
        self.setWindowTitle("HWInfo")
        self.setMinimumSize(1080, 700)
        self._apply_default_geometry()
        self.setWindowIcon(app_icon())

        self._worker: CollectWorker | None = None
        self._result: CollectResult | None = None
        self._pages: dict[str, QWidget] = {}
        self._enabled: list[str] = prefs.enabled_categories()
        self._done = 0
        self._tools: list[tuple[QToolButton, str]] = []

        self._build_ui()
        self._apply_on_top(prefs.gui_prefs().get("on_top", False))
        self._install_shortcuts()
        if auto_collect:
            QTimer.singleShot(60, self.start_collect)

    # ------------------------------------------------------------ 界面

    def _build_ui(self) -> None:
        app = QApplication.instance()
        if app is not None:
            app.setStyleSheet(theme.build_qss())

        root = QWidget()
        root.setObjectName("root")
        root.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setCentralWidget(root)

        outer = QVBoxLayout(root)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        outer.addWidget(self._build_top_bar())

        overview = OverviewPage()
        overview.set_pending([])
        overview.board.counts_changed.connect(self._count.setText)
        self._pages = {"overview": overview}
        outer.addWidget(overview, 1)
        self._count.setText("0 项")
        self._update_host()

    def _build_top_bar(self) -> QWidget:
        bar = QWidget()
        bar.setObjectName("topbar")
        bar.setFixedHeight(theme.sp(44))
        self._bar = bar
        lay = QHBoxLayout(bar)
        lay.setContentsMargins(theme.sp(26), 0, theme.sp(26), 0)
        lay.setSpacing(theme.sp(10))
        self._bar_lay = lay

        brand = QLabel("HWInfo")
        brand.setObjectName("brand")
        lay.addWidget(brand)

        sub = QLabel("配置概览")
        sub.setObjectName("brandSub")
        lay.addWidget(sub)

        self._host = ElidedLabel("")
        self._host.setObjectName("hostText")
        lay.addWidget(self._host, 1)

        self._status = QLabel("等待采集")
        self._status.setObjectName("statusText")
        lay.addWidget(self._status, 0, Qt.AlignmentFlag.AlignVCenter)

        self._meta = QLabel("")
        self._meta.setObjectName("metaText")
        lay.addWidget(self._meta, 0, Qt.AlignmentFlag.AlignVCenter)

        # 信息量：全部 / 精简
        self._mode_group = QButtonGroup(self)
        self._mode_group.setExclusive(True)
        self._mode_all = self._seg_button("全部")
        self._mode_brief = self._seg_button("精简")
        self._mode_brief.setChecked(True)
        self._mode_group.addButton(self._mode_all)
        self._mode_group.addButton(self._mode_brief)
        self._mode_all.clicked.connect(lambda: self._set_mode("all"))
        self._mode_brief.clicked.connect(lambda: self._set_mode("brief"))
        lay.addWidget(self._mode_all)
        lay.addWidget(self._mode_brief)

        self._labels_btn = self._seg_button("标签")
        self._labels_btn.setChecked(True)
        self._labels_btn.setToolTip("显示 / 隐藏左侧字段名")
        self._labels_btn.toggled.connect(self._on_labels_toggled)
        lay.addWidget(self._labels_btn)

        self._search = QLineEdit()
        self._search.setObjectName("searchBox")
        self._search.setPlaceholderText("搜索字段或设备")
        self._search.setClearButtonEnabled(True)
        self._search.setFixedWidth(theme.sp(190))
        self._search.setToolTip("Ctrl+K 聚焦，Esc 清空")
        self._search.textChanged.connect(self._on_search)
        lay.addWidget(self._search)

        self._count = QLabel("")
        self._count.setObjectName("countText")
        lay.addWidget(self._count)

        lay.addWidget(self._tool_button("refresh", "重新采集 (F5)", self.start_collect))
        lay.addWidget(self._tool_button("export", "导出 JSON (Ctrl+E)", self.export_json))
        lay.addWidget(self._tool_button("settings", "设置 (Ctrl+,)", self.open_settings))
        return bar

    def _seg_button(self, text: str) -> QPushButton:
        btn = QPushButton(text)
        btn.setObjectName("segItem")
        btn.setCheckable(True)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        return btn

    def _tool_button(self, icon: str, tip: str, slot) -> QToolButton:
        btn = QToolButton()
        btn.setObjectName("toolIcon")
        btn.setIcon(qicon(icon, theme.P["muted"], theme.sp(16)))
        btn.setIconSize(QSize(theme.sp(16), theme.sp(16)))
        btn.setFixedSize(theme.sp(24), theme.sp(24))
        btn.setAutoRaise(True)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setToolTip(tip)
        btn.clicked.connect(slot)
        self._tools.append((btn, icon))
        return btn

    # ------------------------------------------------------------ 视图开关

    def _board(self):
        return self._pages["overview"].board

    def _set_mode(self, mode: str) -> None:
        self._board().set_mode(mode)
        self._mode_all.setChecked(mode == "all")
        self._mode_brief.setChecked(mode == "brief")

    def _on_labels_toggled(self, checked: bool) -> None:
        self._board().set_labels(bool(checked))

    def _on_search(self, text: str) -> None:
        self._board().set_query(text)

    def focus_search(self) -> None:
        self._search.setFocus(Qt.FocusReason.ShortcutFocusReason)
        self._search.selectAll()

    def clear_search(self) -> None:
        if self._search.text():
            self._search.clear()
        elif self._search.hasFocus():
            self._board().setFocus()

    # ------------------------------------------------------------ 采集

    def start_collect(self) -> None:
        if self._worker is not None and self._worker.isRunning():
            return

        enabled = prefs.enabled_categories()
        self._enabled = enabled
        board = self._board()

        if not enabled:
            # 明确「全部关闭」：不采集任何类别，而不是退化为采集全部
            board.set_data({})
            self._result = CollectResult()
            self._set_status("已关闭全部类别", theme.P["warn"])
            self._meta.setText("")
            self._update_host()
            return

        board.set_pending(enabled)
        self._set_status(f"采集中 0 / {len(enabled)}", theme.P["accent"])
        self._meta.setText("")

        self._worker = CollectWorker(enabled, timeout=prefs.get_timeout(), parent=self)
        self._worker.started_categories.connect(self._on_started)
        self._worker.category_done.connect(self._on_category_done)
        self._worker.collect_finished.connect(self._on_collect_finished)
        self._worker.error.connect(self._on_collect_error)
        self._worker.start()

    def _on_started(self, categories: list) -> None:
        self._done = 0
        self._set_status(f"采集中 0 / {len(categories)}", theme.P["accent"])

    def _on_category_done(self, name: str, data, elapsed: float) -> None:
        self._board().update_category(name, data)
        self._done += 1
        self._set_status(f"采集中 {self._done} / {len(self._enabled)}", theme.P["accent"])

    def _on_collect_finished(self, result: CollectResult) -> None:
        self._result = result
        self._board().set_data(result.data)
        self._update_host()

        ok = len(result.data)
        total = ok + len(result.errors)
        if result.errors:
            self._set_status(f"完成 {ok}/{total} · {len(result.errors)} 个失败",
                             theme.P["warn"])
        else:
            self._set_status(f"完成 {ok}/{total}", theme.P["ok"])
        self._meta.setText(
            f"采集于 {datetime.now().strftime('%H:%M')} · {result.elapsed_seconds:.2f}s")
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

    def _update_host(self) -> None:
        system = ""
        if self._result is not None:
            os_data = self._result.data.get("os") or {}
            system = str(os_data.get("系统名称") or "")
            system = system.replace("Microsoft ", "", 1)
        host = ""
        try:
            host = socket.gethostname()
        except OSError:
            host = ""
        parts = [part for part in (host, system) if part]
        self._host.setText("  ·  ".join(parts))

    # ------------------------------------------------------------ 设置 / 外观

    def open_settings(self) -> None:
        dialog = SettingsDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self._enabled = prefs.enabled_categories()
            self._apply_on_top(prefs.gui_prefs().get("on_top", False))
            self._result = None
            self._board().set_data({})
            self.start_collect()

    def _apply_on_top(self, value: bool) -> None:
        visible = self.isVisible()
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, bool(value))
        if visible:
            self.show()

    # ------------------------------------------------------------ 导出

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

    # ------------------------------------------------------------ 状态 / 快捷键

    def _set_status(self, text: str, color: str) -> None:
        self._status.setText(text)
        self._status.setStyleSheet(f"color: {color};")

    def _flash_status(self, text: str, color: str) -> None:
        self._set_status(text, color)
        QTimer.singleShot(2600, lambda: self._set_status(
            "完成" if self._result else "等待采集", theme.P["muted"]))

    def _install_shortcuts(self) -> None:
        QShortcut(QKeySequence("F5"), self, activated=self.start_collect)
        QShortcut(QKeySequence("Ctrl+E"), self, activated=self.export_json)
        QShortcut(QKeySequence("Ctrl+K"), self, activated=self.focus_search)
        QShortcut(QKeySequence("Ctrl+,"), self, activated=self.open_settings)
        QShortcut(QKeySequence("Esc"), self, activated=self.clear_search)
        QShortcut(QKeySequence("Ctrl+="), self, activated=lambda: self._zoom_by(ZOOM_STEP))
        QShortcut(QKeySequence("Ctrl++"), self, activated=lambda: self._zoom_by(ZOOM_STEP))
        QShortcut(QKeySequence("Ctrl+-"), self, activated=lambda: self._zoom_by(-ZOOM_STEP))
        QShortcut(QKeySequence("Ctrl+0"), self, activated=lambda: self._set_zoom(1.0))

    def _zoom_by(self, delta: float) -> None:
        self._set_zoom(get_zoom() + delta)

    def _set_zoom(self, value: float) -> None:
        """缩放顶栏与控件；画板字号始终按窗口尺寸自适应，不受缩放影响"""
        value = round(max(ZOOM_MIN, min(ZOOM_MAX, value)), 2)
        if abs(value - get_zoom()) < 0.001:
            return
        set_zoom(value)
        prefs.set_gui_pref("zoom", value)
        self._apply_zoom()

    def _apply_zoom(self) -> None:
        app = QApplication.instance()
        if app is not None:
            app.setStyleSheet(theme.build_qss())
        self._bar.setFixedHeight(theme.sp(44))
        self._bar_lay.setContentsMargins(theme.sp(26), 0, theme.sp(26), 0)
        self._bar_lay.setSpacing(theme.sp(10))
        self._search.setFixedWidth(theme.sp(190))
        for btn, icon in self._tools:
            btn.setIcon(qicon(icon, theme.P["muted"], theme.sp(16)))
            btn.setIconSize(QSize(theme.sp(16), theme.sp(16)))
            btn.setFixedSize(theme.sp(24), theme.sp(24))
        self.updateGeometry()

    def _apply_default_geometry(self) -> None:
        """默认窗口尺寸按可用屏幕自适应（原型参照 1440×900）"""
        preferred_w, preferred_h = 1440, 900
        screen = QApplication.primaryScreen()
        available = screen.availableGeometry() if screen is not None else None
        if available is None:
            self.resize(preferred_w, preferred_h)
            return
        width = min(preferred_w, max(1080, available.width() - 80))
        height = min(preferred_h, max(700, available.height() - 60))
        self.resize(width, height)
        self.move(available.x() + (available.width() - width) // 2,
                  available.y() + (available.height() - height) // 2)

    def closeEvent(self, event) -> None:  # noqa: N802
        if self._worker is not None and self._worker.isRunning():
            self._worker.requestInterruption()
            self._worker.wait(1500)
        super().closeEvent(event)
