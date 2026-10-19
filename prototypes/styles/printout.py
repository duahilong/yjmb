"""风格 05 · PRINTOUT —— 点阵打印报告 / 收据。

深灰桌面 + 米白纸张 + 等宽字体 + 点线引导 + 印章与条形码。
像一张刚从点阵打印机里吐出来的硬件诊断单，复古但可信。
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "shared"))

from PySide6.QtCore import Qt                                # noqa: E402
from PySide6.QtGui import QColor, QPainter, QPen             # noqa: E402
from PySide6.QtWidgets import (                              # noqa: E402
    QFrame, QHBoxLayout, QLabel, QMainWindow, QVBoxLayout, QWidget,
)

import mock_data as d                                       # noqa: E402
from ui import (                                            # noqa: E402
    MONO, SANS, W_BOLD, W_DEMI, Barcode, DotLeaderRow, Stamp, label, qfont,
    shadow,
)

DESK = "#1F2124"
PAPER = "#F5F1E6"
INK = "#202020"
MUTED = "#6B6558"
FAINT = "#9A9280"
DASH = "#BEB6A4"
RED = "#B23A2E"
GREEN = "#2E7D32"

QSS = f"""
QWidget {{ font-family: "{SANS}"; font-size: 12px; color: {INK}; }}
#rootPO {{ background-color: {DESK}; }}
#paperPO {{ background-color: {PAPER}; border-radius: 2px; }}
#brandPO {{ font-family: "{MONO}"; font-size: 20px; font-weight: 700; color: {INK}; }}
#titlePO {{ font-family: "{MONO}"; font-size: 12px; font-weight: 700; color: {INK}; }}
#subPO {{ font-size: 12px; color: {MUTED}; }}
#metaPO {{ font-family: "{MONO}"; font-size: 10px; color: {MUTED}; }}
#sectPO {{ font-family: "{MONO}"; font-size: 11px; font-weight: 700; color: {INK}; }}
#sectMetaPO {{ font-family: "{MONO}"; font-size: 9px; color: {FAINT}; }}
#footPO {{ font-family: "{MONO}"; font-size: 9px; color: {MUTED}; }}
#endPO {{ font-family: "{MONO}"; font-size: 12px; font-weight: 700; color: {INK}; }}
"""


def _dashed(color: str = DASH) -> QFrame:
    f = QFrame()
    f.setFixedHeight(1)
    f.setStyleSheet(f"border-top: 1px dashed {color}; background: transparent;")
    return f


class Paper(QFrame):
    """带两侧走纸虚线的纸张。"""

    def paintEvent(self, event):
        super().paintEvent(event)
        p = QPainter(self)
        pen = QPen(QColor(DASH), 1, Qt.PenStyle.DotLine)
        p.setPen(pen)
        p.drawLine(18, 12, 18, self.height() - 12)
        p.drawLine(self.width() - 18, 12, self.width() - 18, self.height() - 12)
        p.end()


def _section(title: str, count: int) -> QWidget:
    box = QWidget()
    lay = QHBoxLayout(box)
    lay.setContentsMargins(0, 0, 0, 0)
    lay.setSpacing(8)
    lay.addWidget(label(f"== {title} ", "sectPO"))
    line = QFrame()
    line.setFixedHeight(1)
    line.setStyleSheet(f"border-top: 1px dashed {DASH}; background: transparent;")
    lay.addWidget(line, 1)
    lay.addWidget(label(f"{count:02d}", "sectMetaPO"))
    return box


def _row(key: str, value: str) -> DotLeaderRow:
    return DotLeaderRow(key, value, key_color=MUTED, value_color=INK,
                        dot_color=DASH, size=11, height=18)


def _spec_block(title: str, rows: list[tuple[str, str]]) -> QVBoxLayout:
    lay = QVBoxLayout()
    lay.setContentsMargins(0, 0, 0, 0)
    lay.setSpacing(2)
    lay.addSpacing(2)
    lay.addWidget(_section(title, len(rows)))
    lay.addSpacing(1)
    for k, v in rows:
        lay.addWidget(_row(k, v))
    lay.addSpacing(5)
    return lay


class WindowPrintout(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("HWInfo — Printout")
        self.setStyleSheet(QSS)
        root = QWidget()
        root.setObjectName("rootPO")
        self.setCentralWidget(root)
        outer = QVBoxLayout(root)
        outer.setContentsMargins(0, 14, 0, 14)
        outer.setSpacing(0)
        outer.addStretch()

        paper = Paper()
        paper.setObjectName("paperPO")
        paper.setFixedWidth(760)
        shadow(paper, "#000000", blur=48, dy=16, alpha=130)
        outer.addWidget(paper, 0, Qt.AlignmentFlag.AlignHCenter)

        lay = QVBoxLayout(paper)
        lay.setContentsMargins(44, 26, 44, 24)
        lay.setSpacing(0)

        # —— 报头 ——
        head = QHBoxLayout()
        head.setSpacing(10)
        left = QVBoxLayout()
        left.setSpacing(2)
        left.addWidget(label("HWINFO", "brandPO"))
        left.addWidget(label("Hardware Diagnostic Report / 硬件诊断报告", "subPO"))
        head.addLayout(left, 1)
        head.addWidget(Stamp("9/9  PASS", GREEN, angle=-8, size=14, width=150, height=42),
                      alignment=Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight)
        lay.addLayout(head)
        lay.addSpacing(6)
        lay.addWidget(label("H A R D W A R E   D I A G N O S T I C   R E P O R T", "titlePO"))
        lay.addSpacing(10)
        lay.addWidget(_dashed())
        lay.addSpacing(8)

        for k, v in [
            ("HOST", d.HOST),
            ("OS", f"{d.OS_NAME}  {d.OS_VERSION}"),
            ("BOARD", f"{d.VENDOR} {d.MODEL} ({d.BOARD})  BIOS {d.BIOS}"),
            ("TIME", f"{d.COLLECTED_DATE} {d.COLLECTED_AT}  ·  {d.ELAPSED}"),
        ]:
            lay.addWidget(_row(k, v))
        lay.addSpacing(6)
        lay.addWidget(_dashed())
        lay.addSpacing(2)

        # —— 规格 ——
        blocks = [
            ("处理器", [
                ("核心 / 线程", f"{d.CPU_CORES} 核 / {d.CPU_THREADS} 线程"),
                ("基准频率", d.CPU_FREQ),
                ("插槽", d.CPU_SOCKET),
            ]),
            ("内存", [
                ("容量 / 类型", f"{d.RAM_TOTAL} {d.RAM_TYPE}"),
                ("频率 / 时序", f"{d.RAM_SPEED} / {d.RAM_LATENCY}"),
            ]),
            ("显卡", [
                ("独立显卡", d.GPU_FULL),
                ("显存", d.GPU_VRAM),
                ("驱动版本", d.GPU_DRIVER),
            ]),
            ("存储", [
                ("系统盘", f"{d.DISK_1}  {d.DISK_1_SIZE}"),
                ("接口", d.DISK_1_IF),
                ("数据盘", f"{d.DISK_2}  {d.DISK_2_SIZE}"),
            ]),
            ("网络", [
                ("无线", d.WIFI),
                ("有线", d.LAN),
            ]),
            ("显示器", [
                ("主屏", f"{d.MONITOR_1}  {d.MONITOR_1_SPEC}"),
                ("副屏", f"{d.MONITOR_2}  {d.MONITOR_2_SPEC}"),
            ]),
            ("主板 / 固件", [
                ("型号", f"{d.VENDOR} {d.MODEL}"),
                ("BIOS / 固件", f"{d.BIOS} / {d.FIRMWARE}"),
            ]),
            ("音频", [
                ("设备", d.AUDIO),
                ("驱动版本", d.AUDIO_DRIVER),
            ]),
        ]
        for title, rows in blocks:
            lay.addLayout(_spec_block(title, rows))

        # —— 页脚 ——
        lay.addWidget(_dashed())
        lay.addSpacing(8)
        foot = QHBoxLayout()
        foot.setSpacing(8)
        foot.addWidget(label("END OF REPORT", "endPO"))
        foot.addStretch()
        foot.addWidget(label(f"PAGE 1 / 1  ·  {d.CATEGORIES_OK}/{d.CATEGORIES_TOTAL} CATEGORIES  ·  {d.ERRORS} ERRORS", "footPO"))
        lay.addLayout(foot)
        lay.addSpacing(10)
        lay.addWidget(Barcode(f"{d.HOST}-{d.COLLECTED_DATE}-HWINFO", color=INK, height=38))
        lay.addSpacing(6)
        lay.addWidget(label(f"生成于 {d.COLLECTED_DATE} {d.COLLECTED_AT} · HWINFO v0.1.0", "footPO"),
                      alignment=Qt.AlignmentFlag.AlignHCenter)

        outer.addStretch()


def build_window() -> QMainWindow:
    return WindowPrintout()


if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication
    app = QApplication(sys.argv)
    win = build_window()
    win.resize(1440, 900)
    win.show()
    sys.exit(app.exec())
