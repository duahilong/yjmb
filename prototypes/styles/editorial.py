"""风格 02 · EDITORIAL —— 规格手册 / 杂志排版。

冷白纸面 + Georgia 衬线大字号 + 朱红点缀 + 细发丝线。
把一屏硬件信息排成一份有呼吸感的规格特稿。
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "shared"))

from PySide6.QtCore import Qt                                # noqa: E402
from PySide6.QtWidgets import (                              # noqa: E402
    QFrame, QHBoxLayout, QLabel, QMainWindow, QVBoxLayout, QWidget,
)

import mock_data as d                                       # noqa: E402
from ui import (                                            # noqa: E402
    MONO, SANS, SERIF, W_BOLD, W_DEMI, W_NORMAL, hline, label, qfont, rgba,
    vline,
)

PAPER = "#F7F7F5"
INK = "#141414"
MUTED = "#6E6E6E"
SOFT = "#9A9A94"
HAIR = "#E3E3DE"
RED = "#D0342C"

QSS = f"""
QWidget {{ font-family: "{SANS}"; font-size: 13px; color: {INK}; }}
#rootED {{ background-color: {PAPER}; }}
#eyebrowED {{ font-family: "{MONO}"; font-size: 10px; color: {RED}; }}
#modelED {{ font-family: "{SERIF}"; font-size: 58px; font-weight: 700; color: {INK}; }}
#taglineED {{ font-size: 13px; color: {MUTED}; }}
#sectionNoED {{ font-family: "{MONO}"; font-size: 11px; color: {RED}; font-weight: 700; }}
#sectionTitleED {{ font-size: 15px; font-weight: 700; color: {INK}; }}
#specKeyED {{ font-size: 11px; color: {MUTED}; }}
#specValueED {{ font-family: "{MONO}"; font-size: 10px; color: {INK}; }}
#heroNumED {{ font-family: "{SERIF}"; font-size: 46px; font-weight: 700; color: {INK}; }}
#heroLabelED {{ font-family: "{MONO}"; font-size: 10px; color: {RED}; }}
#heroSubED {{ font-size: 11px; color: {MUTED}; }}
#indexLabelED {{ font-family: "{MONO}"; font-size: 10px; color: {SOFT}; }}
#indexKeyED {{ font-size: 12px; color: {INK}; }}
#indexNumED {{ font-family: "{MONO}"; font-size: 10px; color: {MUTED}; }}
#footNoteED {{ font-family: "{SERIF}"; font-size: 14px; font-style: italic; color: {MUTED}; }}
#footMetaED {{ font-family: "{MONO}"; font-size: 10px; color: {SOFT}; }}
"""


def _dot_leader() -> QFrame:
    f = QFrame()
    f.setFixedHeight(6)
    f.setStyleSheet(f"border-bottom: 1px dotted {SOFT}; background: transparent;")
    f.setSizePolicy(f.sizePolicy().horizontalPolicy(), f.sizePolicy().verticalPolicy())
    return f


def _index_row(key: str, num: str) -> QWidget:
    row = QWidget()
    lay = QHBoxLayout(row)
    lay.setContentsMargins(0, 0, 0, 0)
    lay.setSpacing(6)
    lay.addWidget(label(key, "indexKeyED"))
    lay.addWidget(_dot_leader(), 1)
    lay.addWidget(label(num, "indexNumED"))
    return row


def _spec_row(key: str, value: str) -> QWidget:
    row = QWidget()
    lay = QVBoxLayout(row)
    lay.setContentsMargins(0, 0, 0, 0)
    lay.setSpacing(3)
    line = QHBoxLayout()
    line.setSpacing(8)
    line.addWidget(label(key, "specKeyED"))
    line.addStretch()
    val = label(value, "specValueED")
    line.addWidget(val)
    lay.addLayout(line)
    lay.addWidget(hline(HAIR))
    return row


def _section(no: str, title: str, rows: list[tuple[str, str]]) -> QWidget:
    box = QWidget()
    lay = QVBoxLayout(box)
    lay.setContentsMargins(0, 0, 0, 0)
    lay.setSpacing(6)
    head = QHBoxLayout()
    head.setSpacing(8)
    head.addWidget(label(no, "sectionNoED"))
    head.addWidget(label(title, "sectionTitleED"))
    head.addStretch()
    lay.addLayout(head)
    for k, v in rows:
        lay.addWidget(_spec_row(k, v))
    return box


def _hero(num: str, unit: str, label_text: str, sub: str) -> QWidget:
    box = QWidget()
    lay = QVBoxLayout(box)
    lay.setContentsMargins(0, 0, 0, 0)
    lay.setSpacing(2)
    row = QHBoxLayout()
    row.setSpacing(6)
    row.addWidget(label(num, "heroNumED"))
    row.addWidget(label(unit, "heroLabelED"), alignment=Qt.AlignmentFlag.AlignBottom)
    row.addStretch()
    lay.addLayout(row)
    lay.addWidget(label(label_text, "heroSubED"))
    lay.addWidget(label(sub, "specValueED"))
    return box


class WindowEditorial(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("HWInfo — Editorial")
        self.setStyleSheet(QSS)
        root = QWidget()
        root.setObjectName("rootED")
        self.setCentralWidget(root)
        lay = QVBoxLayout(root)
        lay.setContentsMargins(56, 40, 56, 28)
        lay.setSpacing(0)

        # —— 刊头 ——
        lay.addWidget(label("H A R D W A R E   S P E C I F I C A T I O N   /   硬件检测报告", "eyebrowED"))
        lay.addSpacing(10)
        masthead = QHBoxLayout()
        masthead.setSpacing(32)
        left = QVBoxLayout()
        left.setSpacing(6)
        left.addWidget(label(d.MODEL, "modelED"))
        left.addWidget(label(
            f"{d.VENDOR} · 台式工作站 · {d.HOST} · {d.COLLECTED_DATE} {d.COLLECTED_AT}",
            "taglineED", size=13))
        masthead.addLayout(left, 1)

        index = QVBoxLayout()
        index.setSpacing(4)
        index.addWidget(label("INDEX / 目录", "indexLabelED"))
        index.addSpacing(2)
        for num, key in enumerate(
            ["操作系统", "主板", "处理器", "内存", "显卡", "存储", "网络", "音频", "显示器"], start=1
        ):
            index.addWidget(_index_row(key, f"{num:02d}"))
        masthead.addLayout(index)
        lay.addLayout(masthead)
        lay.addSpacing(16)
        lay.addWidget(hline(RED, 3))
        lay.addSpacing(22)

        # —— 核心指标 ——
        hero = QHBoxLayout()
        hero.setSpacing(0)
        stats = [
            ("24/24", "核心 / 线程", "", "24C / 24T · 1.69 GHz"),
            ("48", "GB", "内存容量", "DDR5-7200 CL36 · 2/4 插槽"),
            ("11", "GB", "显存", "RTX 2080 Ti · 独显"),
            ("1.4", "TB", "存储容量", "NVMe + SATA · 2 块"),
        ]
        for i, (num, unit, lb, sub) in enumerate(stats):
            hero.addWidget(_hero(num, unit, lb, sub), 1)
            if i < len(stats) - 1:
                hero.addSpacing(22)
                hero.addWidget(vline(HAIR))
                hero.addSpacing(22)
        lay.addLayout(hero)
        lay.addSpacing(22)
        lay.addWidget(hline(HAIR))
        lay.addSpacing(22)

        # —— 三栏规格 ——
        cols = QHBoxLayout()
        cols.setSpacing(0)
        columns = [
            [
                ("01", "操作系统", [
                    ("版本", "10.0.26300"),
                    ("架构", "64 位"),
                    ("系统状态", "正常")]),
                ("04", "内存", [
                    ("品牌", "Golden Empire"),
                    ("容量", "48 GB DDR5"),
                    ("频率 / 时序", "7200 MHz / CL36")]),
                ("07", "音频", [
                    ("设备", "Realtek HD Audio"),
                    ("驱动", "6.0.8988.1")]),
            ],
            [
                ("02", "主板", [
                    ("型号", "MSI Z790MPOWER"),
                    ("板号", d.BOARD),
                    ("BIOS / 固件", "P.60 / UEFI")]),
                ("05", "显卡", [
                    ("独显", "RTX 2080 Ti"),
                    ("显存 / 驱动", "11 GB / 32.0.16.1088"),
                    ("核显", "Intel UHD Graphics")]),
                ("08", "显示器", [
                    ("主屏", f"{d.MONITOR_1} · 4K120"),
                    ("副屏", f"{d.MONITOR_2} · 1080p")]),
            ],
            [
                ("03", "处理器", [
                    ("型号", "Genuine Intel(R) 0000"),
                    ("核心 / 线程", "24 / 24"),
                    ("插槽", "LGA1700")]),
                ("06", "存储", [
                    ("系统盘", "Samsung 980 PRO"),
                    ("容量 / 接口", "931.5 GB / NVMe"),
                    ("数据盘", "GXF-512 PRO · 476.9 GB")]),
                ("09", "网络", [
                    ("无线", "Wi-Fi 6E AX211"),
                    ("有线", "Realtek 2.5GbE"),
                    ("驱动", "23.140.0.3")]),
            ],
        ]
        for i, sections in enumerate(columns):
            col = QVBoxLayout()
            col.setSpacing(16)
            for no, title, rows in sections:
                col.addWidget(_section(no, title, rows))
            col.addStretch()
            cols.addLayout(col, 1)
            if i < len(columns) - 1:
                cols.addSpacing(28)
                cols.addWidget(vline(HAIR))
                cols.addSpacing(28)
        lay.addLayout(cols, 1)

        # —— 页脚 ——
        lay.addWidget(hline(HAIR))
        lay.addSpacing(12)
        foot = QHBoxLayout()
        foot.setSpacing(10)
        foot.addWidget(label("“", "heroLabelED"))
        foot.addWidget(label(
            "9 个类别全部完成，无错误、无警告；本报告由 HWINFO 于采集时生成。",
            "footNoteED"))
        foot.addStretch()
        foot.addWidget(label(
            f"{d.CATEGORIES_OK}/{d.CATEGORIES_TOTAL} 类别 · {d.ERRORS} 错误 · {d.ELAPSED}",
            "footMetaED"))
        lay.addLayout(foot)


def build_window() -> QMainWindow:
    return WindowEditorial()


if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication
    app = QApplication(sys.argv)
    win = build_window()
    win.resize(1440, 900)
    win.show()
    sys.exit(app.exec())
