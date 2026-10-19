"""风格 01 · BLUEPRINT —— 蓝图工程图 / 技术制图。

深普鲁士蓝底、白色技术线稿、引出标注、尺寸线、右下角图签。
把「硬件检测」做成一张工程图纸，而不是一个设置面板。
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "shared"))

from PySide6.QtCore import QPointF, QRectF, Qt, QSize          # noqa: E402
from PySide6.QtGui import QColor, QPainter, QPen               # noqa: E402
from PySide6.QtWidgets import (                                # noqa: E402
    QHBoxLayout, QLabel, QMainWindow, QPushButton, QVBoxLayout, QWidget,
)

import mock_data as d                                         # noqa: E402
from ui import (                                              # noqa: E402
    DISPLAY, MONO, SANS, W_BOLD, W_DEMI, W_NORMAL, hline, icon_size, label,
    qfont, qicon, rgba, vline,
)

BG = "#06203A"
PANEL = "#072744"
GRID = "#123A5C"
LINE = "#3F8DC0"
SOFT = "#2A5F86"
BRIGHT = "#9ED8F7"
INK = "#EAF4FC"
MUTED = "#6FA6CC"
ACCENT = "#FFB454"
OK = "#7DE0A6"

QSS = f"""
QWidget {{ font-family: "{SANS}"; font-size: 13px; color: {INK}; }}
#rootBP {{ background-color: {BG}; }}
#topBarBP {{ background-color: {BG}; border-bottom: 1px solid {SOFT}; }}
#brandBP {{ font-family: "{MONO}"; font-size: 18px; font-weight: 700; color: {INK}; }}
#kickerBP {{ font-family: "{MONO}"; font-size: 10px; color: {MUTED}; }}
#hostBP {{ font-family: "{MONO}"; font-size: 11px; color: {BRIGHT}; }}
#okBP {{ font-family: "{MONO}"; font-size: 11px; color: {OK}; }}
QPushButton#bpBtn {{
    background-color: transparent;
    border: 1px solid {LINE};
    border-radius: 0;
    padding: 5px 12px;
    color: {BRIGHT};
    font-family: "{MONO}";
    font-size: 11px;
}}
QPushButton#bpBtn:hover {{ background-color: {rgba(LINE, 0.16)}; border-color: {BRIGHT}; }}
#scheduleBP {{ background-color: {PANEL}; border-left: 1px solid {SOFT}; }}
#schedHeadBP {{ font-family: "{MONO}"; font-size: 11px; font-weight: 700; color: {BRIGHT}; }}
#schedCodeBP {{ font-family: "{MONO}"; font-size: 9px; color: {ACCENT}; }}
#schedNameBP {{ font-family: "{MONO}"; font-size: 10px; color: {INK}; }}
#schedValueBP {{ font-family: "{MONO}"; font-size: 10px; color: {MUTED}; }}
#titleCellLabelBP {{ font-family: "{MONO}"; font-size: 8px; color: {MUTED}; }}
#titleCellValueBP {{ font-family: "{MONO}"; font-size: 10px; color: {INK}; }}
#titleBarBP {{ background-color: {PANEL}; border-top: 1px solid {SOFT}; }}
"""


def _text(p: QPainter, x: float, y: float, text: str, color: str,
          size: int, family: str = MONO, weight=W_DEMI) -> None:
    p.setPen(QColor(color))
    p.setFont(qfont(family, size, weight))
    p.drawText(QPointF(x, y), text)


class BlueprintCanvas(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(560, 520)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()

        # 网格
        p.setPen(QPen(QColor(GRID), 1))
        for x in range(0, w, 28):
            p.drawLine(x, 0, x, h)
        for y in range(0, h, 28):
            p.drawLine(0, y, w, y)

        # 双线图框
        m = 22
        frame = QRectF(m, m, w - 2 * m, h - 2 * m)
        p.setPen(QPen(QColor(LINE), 1.2))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawRect(frame)
        p.setPen(QPen(QColor(SOFT), 1))
        p.drawRect(frame.adjusted(6, 6, -6, -6))

        cx = w / 2
        cpu = QRectF(cx - 118, 108, 236, 94)
        mem = QRectF(86, 322, 214, 86)
        audio = QRectF(cx - 100, 322, 200, 86)
        gpu = QRectF(w - 300, 322, 214, 86)
        sto = QRectF(86, 540, 214, 86)
        net = QRectF(cx - 107, 540, 214, 86)
        dsp = QRectF(w - 300, 540, 214, 86)

        bus_y = 278
        left_x = mem.center().x()
        right_x = gpu.center().x()

        p.setPen(QPen(QColor(LINE), 1))
        p.drawLine(QPointF(cx, cpu.bottom()), QPointF(cx, bus_y))
        p.drawLine(QPointF(left_x, bus_y), QPointF(right_x, bus_y))
        p.drawLine(QPointF(left_x, bus_y), QPointF(left_x, mem.top()))
        p.drawLine(QPointF(right_x, bus_y), QPointF(right_x, gpu.top()))
        p.drawLine(QPointF(cx, bus_y), QPointF(cx, audio.top()))
        p.drawLine(QPointF(left_x, mem.bottom()), QPointF(left_x, sto.top()))
        p.drawLine(QPointF(right_x, gpu.bottom()), QPointF(right_x, dsp.top()))
        p.drawLine(QPointF(cx, audio.bottom()), QPointF(cx, net.top()))

        p.setBrush(QColor(BRIGHT))
        for pt in (QPointF(cx, bus_y), QPointF(left_x, bus_y), QPointF(right_x, bus_y)):
            p.drawEllipse(pt, 2.6, 2.6)

        # 引出标注
        p.setPen(QPen(QColor(MUTED), 1))
        p.drawLine(QPointF(left_x + 40, mem.top()), QPointF(left_x + 40, 250))
        p.drawLine(QPointF(right_x - 40, gpu.top()), QPointF(right_x - 40, 250))
        _text(p, left_x + 46, 246, "DDR5-7200 CL36", MUTED, 9)
        _text(p, right_x - 96, 246, "PCIe 5.0 x16", MUTED, 9)

        self._block(p, cpu, "U1", "PROCESSOR", f"{d.CPU_CORES}C / {d.CPU_THREADS}T", True)
        self._block(p, mem, "J1", "MEMORY", f"{d.RAM_TOTAL} {d.RAM_TYPE}")
        self._block(p, audio, "U7", "AUDIO", "Realtek HD Audio")
        self._block(p, gpu, "J2", "GRAPHICS", d.GPU)
        self._block(p, sto, "M.2", "STORAGE", d.DISK_1_SIZE)
        self._block(p, net, "J3", "NETWORK", "WIFI 6E / 2.5G")
        self._block(p, dsp, "DP", "DISPLAY", "3 × MONITOR")

        # 尺寸线
        dim_y = h - 54
        p.setPen(QPen(QColor(SOFT), 1))
        p.drawLine(QPointF(86, dim_y), QPointF(w - 86, dim_y))
        for x in (86, w - 86):
            p.drawLine(QPointF(x, dim_y - 6), QPointF(x, dim_y + 6))
        _text(p, cx - 92, dim_y - 8, "Z790 / LGA1700 / PCIe 5.0 / DDR5", MUTED, 9, MONO, W_NORMAL)

        # 图纸标题
        _text(p, m + 20, m + 30, "FIG. 1  SYSTEM BLOCK DIAGRAM", BRIGHT, 11, MONO, W_BOLD)
        _text(p, m + 20, m + 46, "系统框图 / 硬件采集", MUTED, 10, SANS, W_NORMAL)
        p.end()

    def _block(self, p: QPainter, rect: QRectF, code: str, title: str,
               value: str, accent: bool = False) -> None:
        p.setBrush(QColor(rgba(BRIGHT, 0.05)))
        p.setPen(QPen(QColor(ACCENT if accent else BRIGHT), 1.2))
        p.drawRect(rect)
        # 引脚刻度
        p.setPen(QPen(QColor(SOFT), 1))
        for i in range(1, 8):
            x = rect.left() + rect.width() * i / 8
            p.drawLine(QPointF(x, rect.bottom()), QPointF(x, rect.bottom() + 4))
        _text(p, rect.left() + 10, rect.top() + 20, code, ACCENT if accent else MUTED, 8, MONO, W_BOLD)
        _text(p, rect.left() + 10, rect.top() + 40, title, MUTED, 8, MONO, W_NORMAL)
        _text(p, rect.left() + 10, rect.top() + 68, value, INK, 14, MONO, W_DEMI)


def _top_bar() -> QWidget:
    bar = QWidget()
    bar.setObjectName("topBarBP")
    bar.setFixedHeight(58)
    lay = QHBoxLayout(bar)
    lay.setContentsMargins(24, 0, 24, 0)
    lay.setSpacing(14)
    lay.addWidget(label("HWINFO", "brandBP"))
    lay.addWidget(vline(rgba(LINE, 0.4)))
    lay.addWidget(label("HARDWARE SURVEY / 硬件采集", "kickerBP"))
    lay.addStretch()
    lay.addWidget(label(f"{d.HOST}  ·  {d.COLLECTED_DATE} {d.COLLECTED_AT}", "hostBP"))
    lay.addWidget(vline(rgba(LINE, 0.4)))
    lay.addWidget(label(f"{d.CATEGORIES_OK}/{d.CATEGORIES_TOTAL} OK  ·  {d.ELAPSED}", "okBP"))
    for text, icon in (("刷新", "refresh"), ("导出", "export")):
        btn = QPushButton(f" {text}")
        btn.setObjectName("bpBtn")
        btn.setIcon(qicon(icon, BRIGHT, 14))
        btn.setIconSize(icon_size(14))
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        lay.addWidget(btn)
    return bar


def _schedule() -> QWidget:
    panel = QWidget()
    panel.setObjectName("scheduleBP")
    panel.setFixedWidth(400)
    lay = QVBoxLayout(panel)
    lay.setContentsMargins(22, 20, 22, 18)
    lay.setSpacing(0)
    lay.addWidget(label("SPECIFICATION SCHEDULE", "schedHeadBP"))
    lay.addSpacing(6)
    lay.addWidget(hline(LINE))
    lay.addWidget(hline(BRIGHT))
    lay.addSpacing(6)

    for code, name, value in d.SCHEDULE_ROWS:
        row = QHBoxLayout()
        row.setSpacing(10)
        code_lb = label(code, "schedCodeBP")
        code_lb.setFixedWidth(30)
        row.addWidget(code_lb)
        row.addWidget(label(name, "schedNameBP"), 1)
        row.addWidget(label(value, "schedValueBP"))
        lay.addLayout(row)
        lay.addSpacing(6)
        lay.addWidget(hline(rgba(SOFT, 0.55)))
        lay.addSpacing(6)

    lay.addStretch()
    lay.addWidget(hline(LINE))
    lay.addSpacing(8)
    for k, v in (("ISSUE", "001"), ("STATUS", "COMPLETE"),
                 ("ERRORS", str(d.ERRORS)), ("WARNINGS", str(d.WARNINGS))):
        row = QHBoxLayout()
        row.setSpacing(10)
        row.addWidget(label(k, "schedCodeBP"))
        row.addStretch()
        row.addWidget(label(v, "schedNameBP"))
        lay.addLayout(row)
        lay.addSpacing(4)
    return panel


def _title_block() -> QWidget:
    bar = QWidget()
    bar.setObjectName("titleBarBP")
    bar.setFixedHeight(66)
    lay = QHBoxLayout(bar)
    lay.setContentsMargins(24, 10, 24, 10)
    lay.setSpacing(0)
    cells = [
        ("PROJECT", "HWINFO / HARDWARE SURVEY"),
        ("SHEET", "01 OF 01"),
        ("SCALE", "NTS"),
        ("DATE", d.COLLECTED_DATE),
        ("REV", "A"),
        ("DRAWN", "JKM B"),
    ]
    for i, (k, v) in enumerate(cells):
        cell = QVBoxLayout()
        cell.setSpacing(1)
        cell.addWidget(label(k, "titleCellLabelBP"))
        cell.addWidget(label(v, "titleCellValueBP"))
        lay.addLayout(cell, 1 if i == 0 else 0)
        if i < len(cells) - 1:
            lay.addSpacing(18)
            lay.addWidget(vline(rgba(SOFT, 0.7)))
            lay.addSpacing(18)
    return bar


class WindowBlueprint(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("HWInfo — Blueprint")
        self.setStyleSheet(QSS)
        root = QWidget()
        root.setObjectName("rootBP")
        self.setCentralWidget(root)
        outer = QVBoxLayout(root)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)
        outer.addWidget(_top_bar())
        body = QHBoxLayout()
        body.setContentsMargins(0, 0, 0, 0)
        body.setSpacing(0)
        body.addWidget(BlueprintCanvas(), 1)
        body.addWidget(_schedule())
        outer.addLayout(body, 1)
        outer.addWidget(_title_block())


def build_window() -> QMainWindow:
    return WindowBlueprint()


if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication
    app = QApplication(sys.argv)
    win = build_window()
    win.resize(1440, 900)
    win.show()
    sys.exit(app.exec())
