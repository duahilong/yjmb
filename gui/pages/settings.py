"""
gui/pages/settings.py - 设置页

显示类别开关与 CLI 共用 config.yaml 的 display 段；
外观（主题 / 密度 / 置顶）与超时写入 gui / collect 段。
"""
import os
import platform

from PySide6.QtCore import Qt, QTimer, QUrl, Signal
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QApplication, QFrame, QGridLayout, QHBoxLayout, QVBoxLayout, QWidget,
)

from core.constants import ALL_CATEGORIES, CATEGORY_LABELS, VERSION
from gui import prefs, theme
from gui.components import (
    BentoPage, ElidedLabel, Segmented, Switch, action_button, card, chip,
    hline, label, pill,
)

# 每个类别在设置页里的用途说明
DESCRIPTIONS = {
    "os": "版本、安装与启动时间",
    "motherboard": "芯片组与 BIOS",
    "cpu": "型号、核心与指令集",
    "memory": "容量、频率与插槽",
    "gpu": "显卡、显存与驱动",
    "storage": "磁盘、分区与占用",
    "network": "网卡、IP 与速率",
    "audio": "输出设备与驱动",
    "monitor": "型号、分辨率与刷新率",
}

DENSITY_OPTIONS = ["compact", "comfortable", "large"]
DENSITY_TEXT = ["紧凑", "舒适", "大"]


class SettingsPage(BentoPage):
    """设置页"""

    settings_saved = Signal()
    appearance_changed = Signal()
    on_top_changed = Signal(bool)

    def __init__(self, parent=None):
        super().__init__("设置", "", columns=4, row_min=theme.sp(250), parent=parent)
        self._switches: dict[str, Switch] = {}
        self._tags: dict[str, object] = {}

        current = prefs.gui_prefs()
        self._build_display()
        self._build_appearance(current)
        self._build_collect()
        self._build_about()
        self.finish()
        self._build_footer()
        self.set_meta("采集、显示与外观偏好 · 保存在 config.yaml")

    # ------------------------------------------------------------ 显示类别

    def _build_display(self) -> None:
        accent = theme.accent("os")
        frame, body = card("显示类别", accent, "layers",
                           tag=self._enabled_tag(), stretch=False)
        self._tags["display"] = frame.tag_label
        shown = prefs.display_map()

        grid = QGridLayout()
        grid.setHorizontalSpacing(theme.sp(18))
        grid.setVerticalSpacing(theme.sp(10))
        for index, cat in enumerate(ALL_CATEGORIES):
            cell, switch = self._toggle_cell(cat, shown.get(cat, True))
            self._switches[cat] = switch
            grid.addWidget(cell, index // 2, index % 2)
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)
        body.addLayout(grid)
        body.addSpacing(theme.sp(10))
        body.addWidget(label("关闭的类别不会参与采集，总览与详情页也不会显示。",
                             "hintText", wrap=True))
        self.add(frame, span=2)

    def _toggle_cell(self, cat: str, on: bool) -> tuple[QWidget, Switch]:
        accent = theme.accent(cat)
        cell = QWidget()
        lay = QHBoxLayout(cell)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(theme.sp(10))
        lay.addWidget(chip(accent, theme.CATEGORY_ICONS[cat],
                           size=theme.sp(32), radius=theme.sp(10),
                           icon_px=theme.sp(16)))
        text = QVBoxLayout()
        text.setSpacing(0)
        text.addWidget(label(CATEGORY_LABELS.get(cat, cat), "rowName"))
        text.addWidget(ElidedLabel(DESCRIPTIONS.get(cat, ""), "rowSub"))
        lay.addLayout(text, 1)
        switch = Switch(on, accent, on_change=lambda value, c=cat: self._on_category_toggle(c, value))
        lay.addWidget(switch)
        return cell, switch

    def _on_category_toggle(self, cat: str, on: bool) -> None:
        tag = self._tags.get("display")
        if tag is not None:
            tag.setText(self._enabled_tag())

    def _enabled_tag(self) -> str:
        enabled = sum(1 for s in self._switches.values() if s.is_on()) if self._switches else len(ALL_CATEGORIES)
        return f"{enabled} / {len(ALL_CATEGORIES)} 启用"

    # ------------------------------------------------------------ 外观

    def _build_appearance(self, current: dict) -> None:
        accent = theme.accent("monitor")
        frame, body = card("外观", accent, "monitor")
        body.addWidget(label("卡片密度", "miniLabel"))
        body.addSpacing(theme.sp(6))
        density = current.get("density", "comfortable")
        self._density = Segmented(
            DENSITY_TEXT,
            active=DENSITY_OPTIONS.index(density) if density in DENSITY_OPTIONS else 1,
            on_change=self._on_density,
        )
        body.addWidget(self._density)

        body.addSpacing(theme.sp(16))
        body.addWidget(label("主题", "miniLabel"))
        body.addSpacing(theme.sp(6))
        self._theme = Segmented(
            ["浅色", "深色"],
            active=0 if current.get("theme", "light") == "light" else 1,
            on_change=self._on_theme,
        )
        body.addWidget(self._theme)

        body.addSpacing(theme.sp(16))
        row = QHBoxLayout()
        row.setSpacing(theme.sp(10))
        row.addWidget(label("窗口置顶", "rowName"))
        row.addStretch()
        self._on_top = Switch(bool(current.get("on_top", False)), accent,
                              on_change=self._on_on_top)
        row.addWidget(self._on_top)
        body.addLayout(row)
        self.add(frame, span=2)

    def _on_density(self, index: int) -> None:
        name = DENSITY_OPTIONS[index]
        theme.set_density(name)
        prefs.set_gui_pref("density", name)
        QTimer.singleShot(0, self.appearance_changed.emit)

    def _on_theme(self, index: int) -> None:
        name = "light" if index == 0 else "dark"
        theme.set_theme(name)
        prefs.set_gui_pref("theme", name)
        QTimer.singleShot(0, self.appearance_changed.emit)

    def _on_on_top(self, value: bool) -> None:
        prefs.set_gui_pref("on_top", value)
        self.on_top_changed.emit(value)

    # ------------------------------------------------------------ 采集

    def _build_collect(self) -> None:
        accent = theme.accent("memory")
        frame, body = card("采集", accent, "activity")
        body.addWidget(label("采集方式", "miniLabel"))
        body.addSpacing(theme.sp(6))
        body.addWidget(label("顺序采集  ·  逐类读取，完成一类即时刷新", "rowName"))
        body.addSpacing(theme.sp(4))
        body.addWidget(label("避开多线程 WMI 并发竞态；单个类别失败不影响其它类别。",
                             "hintText", wrap=True))
        body.addSpacing(theme.sp(12))
        body.addWidget(hline())
        body.addSpacing(theme.sp(12))
        body.addWidget(label("配置文件", "miniLabel"))
        body.addSpacing(theme.sp(4))
        body.addWidget(ElidedLabel(prefs.get_user_config_path(), "rowSub"))
        self.add(frame, span=2)

    # ------------------------------------------------------------ 关于

    def _build_about(self) -> None:
        accent = theme.accent("motherboard")
        frame, body = card("关于", accent, "info", tag=VERSION)
        for key, value in [
            ("版本", VERSION),
            ("运行时", f"Python {platform.python_version()}"),
            ("界面", "PySide6 · Qt Widgets"),
            ("平台", platform.platform(terse=True)),
        ]:
            row = QHBoxLayout()
            row.setSpacing(theme.sp(8))
            row.addWidget(label(key, "miniLabel"))
            row.addStretch()
            row.addWidget(ElidedLabel(value, "rowSub"), 1)
            body.addLayout(row)
            body.addSpacing(theme.sp(8))
        body.addSpacing(theme.sp(4))
        buttons = QHBoxLayout()
        buttons.setSpacing(theme.sp(8))
        buttons.addWidget(action_button("打开配置目录", "export", kind="ghost",
                                        on_click=self._open_config_dir))
        buttons.addWidget(action_button("复制诊断信息", "info", kind="ghost",
                                        on_click=self._copy_diagnostics))
        buttons.addStretch()
        body.addLayout(buttons)
        self.add(frame, span=2)

    def _open_config_dir(self) -> None:
        directory = os.path.dirname(prefs.get_user_config_path())
        QDesktopServices.openUrl(QUrl.fromLocalFile(directory))

    def _copy_diagnostics(self) -> None:
        text = "\n".join([
            f"HWInfo {VERSION}",
            f"Python {platform.python_version()}",
            platform.platform(),
            f"配置: {prefs.get_user_config_path()}",
        ])
        QApplication.clipboard().setText(text)

    # ------------------------------------------------------------ 底部操作条

    def _build_footer(self) -> None:
        bar = QFrame()
        bar.setObjectName("actionBar")
        bar.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        lay = QHBoxLayout(bar)
        lay.setContentsMargins(theme.sp(20), theme.sp(12), theme.sp(16), theme.sp(12))
        lay.setSpacing(theme.sp(12))
        lay.addWidget(label("修改显示类别后需要重新采集才会刷新数据", "hintText"))
        lay.addStretch()
        lay.addWidget(action_button("恢复默认", kind="ghost", on_click=self._restore_defaults))
        lay.addWidget(action_button("保存设置", "check", kind="primary", on_click=self._save))
        self.add_footer(bar)

    def _save(self) -> None:
        prefs.set_display({cat: sw.is_on() for cat, sw in self._switches.items()})
        self.settings_saved.emit()

    def _restore_defaults(self) -> None:
        for switch in self._switches.values():
            switch.set_on(True)
        theme.set_density("comfortable")
        theme.set_theme("light")
        self._density.set_active(1)
        self._theme.set_active(0)
        self._on_top.set_on(False)
        tag = self._tags.get("display")
        if tag is not None:
            tag.setText(self._enabled_tag())
        prefs.set_display({cat: True for cat in ALL_CATEGORIES})
        prefs.set_gui_pref("theme", "light")
        prefs.set_gui_pref("density", "comfortable")
        prefs.set_gui_pref("on_top", False)
        self.on_top_changed.emit(False)
        self.settings_saved.emit()
        QTimer.singleShot(0, self.appearance_changed.emit)
