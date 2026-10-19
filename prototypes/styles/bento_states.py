"""便当格 · 状态页原型：加载 / 空 / 失败 / 渐进采集。"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "shared"))

from PySide6.QtCore import Qt                                # noqa: E402
from PySide6.QtWidgets import (                              # noqa: E402
    QGridLayout, QHBoxLayout, QMainWindow, QVBoxLayout, QWidget,
)

import mock_data as d                                       # noqa: E402
from ui import MeterBar, hline, label                        # noqa: E402
from bento_kit import (                                     # noqa: E402
    BASE_QSS, C_AUD, C_CPU, C_DSP, C_ERR, C_GPU, C_MB, C_MEM, C_NET, C_OS,
    C_STO, Skeleton, StateBadge, action_button, build_top_bar, card, chip, pill,
)

QSS = BASE_QSS

STATUS = {
    "done": (C_MEM, "完成"),
    "running": (C_CPU, "进行中"),
    "waiting": ("#98A2AD", "等待"),
}


def _loading_card() -> QWidget:
    frame, body = card("加载中", C_CPU, "refresh", "采集中", stretch=False)
    body.addStretch()
    body.addWidget(Skeleton([(1.0, 14), (0.82, 10)]))
    body.addSpacing(16)
    body.addWidget(Skeleton([(0.55, 30)]))
    body.addSpacing(16)
    body.addWidget(Skeleton([(0.92, 10), (0.7, 10)]))
    body.addSpacing(14)
    body.addWidget(label("正在通过 WMI 读取硬件信息…", "stateBodyBento"))
    body.addStretch()
    return frame


def _empty_card() -> QWidget:
    frame, body = card("空状态", C_OS, "box", "未采集", stretch=False)
    body.addStretch()
    body.addWidget(StateBadge("box", C_OS), alignment=Qt.AlignmentFlag.AlignHCenter)
    body.addSpacing(14)
    body.addWidget(label("该类别未采集", "stateTitleBento"),
                   alignment=Qt.AlignmentFlag.AlignHCenter)
    body.addSpacing(4)
    hint = label("此类别已在设置中隐藏，或采集器未返回数据。", "stateBodyBento")
    hint.setWordWrap(True)
    hint.setAlignment(Qt.AlignmentFlag.AlignHCenter)
    body.addWidget(hint)
    body.addSpacing(16)
    row = QHBoxLayout()
    row.addStretch()
    row.addWidget(action_button("重新采集", "refresh", ghost=True))
    row.addStretch()
    body.addLayout(row)
    body.addStretch()
    return frame


def _failed_card() -> QWidget:
    frame, body = card("采集失败", C_ERR, "shield", "错误", stretch=False)
    body.addStretch()
    body.addWidget(StateBadge("shield", C_ERR), alignment=Qt.AlignmentFlag.AlignHCenter)
    body.addSpacing(14)
    body.addWidget(label("采集失败", "stateTitleBento"),
                   alignment=Qt.AlignmentFlag.AlignHCenter)
    body.addSpacing(4)
    hint = label("COM 接口调用超时（0x80041010），请以管理员身份重试。", "stateBodyBento")
    hint.setWordWrap(True)
    hint.setAlignment(Qt.AlignmentFlag.AlignHCenter)
    body.addWidget(hint)
    body.addSpacing(16)
    row = QHBoxLayout()
    row.addStretch()
    row.addWidget(action_button("查看详情", ghost=True))
    row.addWidget(action_button("重试", "refresh", primary=True))
    row.addStretch()
    body.addLayout(row)
    body.addStretch()
    return frame


def _status_item(accent: str, icon: str, name: str, state: str) -> QWidget:
    color, text = STATUS[state]
    row = QWidget()
    lay = QHBoxLayout(row)
    lay.setContentsMargins(0, 0, 0, 0)
    lay.setSpacing(10)
    lay.addWidget(chip(accent, icon, size=30, radius=9, icon_px=15))
    lay.addWidget(label(name, "rowNameBento"))
    lay.addStretch()
    lay.addWidget(pill(text, color))
    return row


def _collecting_card() -> QWidget:
    frame, body = card("采集进行中", C_CPU, "activity", "4 / 9")
    body.addWidget(label("正在采集 4 / 9 类别 · 已用 0.8s", "stateBodyBento"))
    body.addSpacing(10)
    body.addWidget(MeterBar(4 / 9, track="#EDF0FE", gradient=(C_CPU, "#A5B4FC"), height=8))
    body.addSpacing(18)
    grid = QGridLayout()
    grid.setHorizontalSpacing(28)
    grid.setVerticalSpacing(14)
    items = [
        (C_OS, "os", "操作系统", "done"),
        (C_MB, "motherboard", "主板", "done"),
        (C_CPU, "cpu", "处理器", "done"),
        (C_MEM, "memory", "内存", "done"),
        (C_GPU, "gpu", "显卡", "running"),
        (C_STO, "storage", "存储", "running"),
        (C_NET, "network", "网络", "waiting"),
        (C_AUD, "audio", "音频", "waiting"),
        (C_DSP, "monitor", "显示器", "waiting"),
    ]
    for i, (accent, icon, name, state) in enumerate(items):
        grid.addWidget(_status_item(accent, icon, name, state), i // 3, i % 3)
    body.addLayout(grid)
    body.addSpacing(18)
    foot = QHBoxLayout()
    foot.setSpacing(10)
    foot.addWidget(label("剩余 5 类 · 预计 1.2s", "hintBento"))
    foot.addStretch()
    foot.addWidget(action_button("取消采集", ghost=True))
    body.addLayout(foot)
    return frame


class WindowStates(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("HWInfo — Bento · 状态")
        self.setStyleSheet(QSS)
        root = QWidget()
        root.setObjectName("rootBento")
        self.setCentralWidget(root)
        outer = QVBoxLayout(root)
        outer.setContentsMargins(28, 20, 28, 22)
        outer.setSpacing(0)

        outer.addWidget(build_top_bar("状态组件  ·  加载 / 空 / 失败", "", actions=False))
        outer.addSpacing(16)

        header = QHBoxLayout()
        header.setSpacing(10)
        header.addWidget(label("状态与反馈", "pageTitleBento"))
        header.addWidget(pill("卡片级三态 + 渐进采集", C_CPU),
                         alignment=Qt.AlignmentFlag.AlignVCenter)
        header.addStretch()
        outer.addLayout(header)
        outer.addSpacing(16)

        grid = QGridLayout()
        grid.setSpacing(16)
        for c in range(3):
            grid.setColumnStretch(c, 1)
        grid.setRowMinimumHeight(0, 252)
        grid.setRowMinimumHeight(1, 292)
        grid.addWidget(_loading_card(), 0, 0)
        grid.addWidget(_empty_card(), 0, 1)
        grid.addWidget(_failed_card(), 0, 2)
        grid.addWidget(_collecting_card(), 1, 0, 1, 3)
        outer.addLayout(grid, 1)


def build_window() -> QMainWindow:
    return WindowStates()


if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication
    app = QApplication(sys.argv)
    win = build_window()
    win.resize(1440, 900)
    win.show()
    sys.exit(app.exec())
