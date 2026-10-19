"""便当格 · 设置页原型。"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "shared"))

from PySide6.QtCore import Qt                                # noqa: E402
from PySide6.QtWidgets import (                              # noqa: E402
    QFrame, QGridLayout, QHBoxLayout, QMainWindow, QVBoxLayout, QWidget,
)

import mock_data as d                                       # noqa: E402
from ui import label                                         # noqa: E402
from bento_kit import (                                     # noqa: E402
    BASE_QSS, C_AUD, C_CPU, C_DSP, C_GPU, C_MB, C_MEM, C_NET, C_OS, C_STO,
    Switch, action_button, build_top_bar, card, chip, pill, segmented,
)

QSS = BASE_QSS


def _field(name: str, control: QWidget) -> QWidget:
    row = QWidget()
    lay = QHBoxLayout(row)
    lay.setContentsMargins(0, 0, 0, 0)
    lay.setSpacing(10)
    lay.addWidget(label(name, "rowNameBento"))
    lay.addStretch()
    lay.addWidget(control)
    return row


def _toggle_row(accent: str, icon: str, name: str, meta: str, on: bool) -> QWidget:
    row = QWidget()
    lay = QHBoxLayout(row)
    lay.setContentsMargins(0, 0, 0, 0)
    lay.setSpacing(12)
    lay.addWidget(chip(accent, icon, size=34, radius=10, icon_px=17))
    txt = QVBoxLayout()
    txt.setSpacing(0)
    txt.addWidget(label(name, "rowNameBento"))
    txt.addWidget(label(meta, "rowSubBento"))
    lay.addLayout(txt, 1)
    lay.addWidget(Switch(on, accent))
    return row


def _categories_card() -> QWidget:
    frame, body = card("显示类别", C_CPU, "layers", "9 / 9 启用", stretch=False)
    rows = [
        (C_OS, "os", "操作系统", "12 项", True),
        (C_MB, "motherboard", "主板", "8 项", True),
        (C_CPU, "cpu", "处理器", "14 项", True),
        (C_MEM, "memory", "内存", "24 项", True),
        (C_GPU, "gpu", "显卡", "12 项", True),
        (C_STO, "storage", "存储", "9 项", True),
        (C_NET, "network", "网络", "7 项", True),
        (C_AUD, "audio", "音频", "6 项", False),
        (C_DSP, "monitor", "显示器", "4 项", True),
    ]
    for i, (accent, icon, name, meta, on) in enumerate(rows):
        body.addWidget(_toggle_row(accent, icon, name, meta, on))
        if i < len(rows) - 1:
            body.addSpacing(12)
            body.addStretch()
    return frame


def _appearance_card() -> QWidget:
    frame, body = card("外观", C_DSP, "display")
    body.addWidget(_field("卡片密度", segmented(["紧凑", "舒适", "大"], active=1)))
    body.addSpacing(14)
    body.addWidget(_field("主题", segmented(["浅色", "深色", "跟随系统"], active=0)))
    body.addSpacing(14)
    body.addWidget(_field("窗口置顶", Switch(False, C_DSP)))
    return frame


def _collect_card() -> QWidget:
    frame, body = card("采集", C_MEM, "activity")
    body.addWidget(_field("采集全部类别", Switch(True, C_MEM)))
    body.addSpacing(14)
    body.addWidget(_field("包含隐藏类别", Switch(False, C_MEM)))
    body.addSpacing(14)
    body.addWidget(_field("超时", segmented(["5 秒", "10 秒", "30 秒"], active=1)))
    return frame


def _about_card() -> QWidget:
    frame, body = card("关于", C_MB, "box")
    for k, v in [
        ("版本", "0.1.0"),
        ("运行时", "Python 3.13 · PySide6 6.9.0"),
        ("平台", "Windows 10.0.26300"),
    ]:
        line = QHBoxLayout()
        line.setSpacing(8)
        line.addWidget(label(k, "miniLabelBento"))
        line.addStretch()
        line.addWidget(label(v, "rowSubBento"))
        body.addLayout(line)
        body.addSpacing(10)
    body.addSpacing(2)
    links = QHBoxLayout()
    links.setSpacing(16)
    links.addWidget(action_button("打开日志", "export", ghost=True))
    links.addWidget(action_button("检查更新", "refresh", ghost=True))
    links.addStretch()
    body.addLayout(links)
    return frame


class WindowSettings(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("HWInfo — Bento · 设置")
        self.setStyleSheet(QSS)
        root = QWidget()
        root.setObjectName("rootBento")
        self.setCentralWidget(root)
        outer = QVBoxLayout(root)
        outer.setContentsMargins(28, 20, 28, 22)
        outer.setSpacing(0)

        outer.addWidget(build_top_bar("设置  ·  偏好", "", actions=False))
        outer.addSpacing(16)

        header = QHBoxLayout()
        header.setSpacing(10)
        header.addWidget(label("设置", "pageTitleBento"))
        header.addWidget(pill("本地配置 · 自动保存", C_MEM), alignment=Qt.AlignmentFlag.AlignVCenter)
        header.addWidget(label("采集、显示与外观偏好", "pageMetaBento"),
                         alignment=Qt.AlignmentFlag.AlignVCenter)
        header.addStretch()
        outer.addLayout(header)
        outer.addSpacing(16)

        grid = QGridLayout()
        grid.setSpacing(16)
        for c in range(4):
            grid.setColumnStretch(c, 1)
        grid.setRowMinimumHeight(0, 208)
        grid.setRowMinimumHeight(1, 208)
        grid.setRowMinimumHeight(2, 208)

        grid.addWidget(_categories_card(), 0, 0, 3, 2)
        grid.addWidget(_appearance_card(), 0, 2, 1, 2)
        grid.addWidget(_collect_card(), 1, 2, 1, 2)
        grid.addWidget(_about_card(), 2, 2, 1, 2)
        outer.addLayout(grid, 1)
        outer.addSpacing(16)

        bar = QFrame()
        bar.setObjectName("actionBarBento")
        bar.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        bar_lay = QHBoxLayout(bar)
        bar_lay.setContentsMargins(20, 12, 16, 12)
        bar_lay.setSpacing(12)
        bar_lay.addWidget(label("修改后需重新采集才能刷新数据", "hintBento"))
        bar_lay.addStretch()
        bar_lay.addWidget(action_button("恢复默认", ghost=True))
        bar_lay.addWidget(action_button("保存设置", primary=True))
        outer.addWidget(bar)


def build_window() -> QMainWindow:
    return WindowSettings()


if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication
    app = QApplication(sys.argv)
    win = build_window()
    win.resize(1440, 900)
    win.show()
    sys.exit(app.exec())
