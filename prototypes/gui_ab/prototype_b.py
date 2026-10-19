"""方案 B：Night Bench / 深色诊断台（拓扑 + 实时监控）。"""
from PySide6.QtCore import QPointF, QRectF, Qt, QSize
from PySide6.QtGui import QColor, QFont, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import (
    QAbstractItemView, QFrame, QHBoxLayout, QHeaderView, QLabel, QMainWindow,
    QPushButton, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget,
)

import mock_data as d
from ui_helpers import DISPLAY, MONO, SANS, hline, qfont, qicon, vline

BG = "#0C1210"
PANEL = "#101A16"
LINE = "#22332B"
TEXT = "#E6EDE9"
MUTED = "#7F958B"
AMBER = "#E3A857"
MINT = "#5FB98A"
BLUE = "#7FB2D6"

QSS_B = """
QWidget {
    font-family: "Microsoft YaHei UI";
    font-size: 13px;
    color: #E6EDE9;
}
#rootB { background-color: #0C1210; }
#topBarB { background-color: #0C1210; border-bottom: 1px solid #1E2D26; }
#brandB {
    font-family: "Bahnschrift";
    font-size: 21px;
    font-weight: 700;
    color: #F2F7F4;
}
#hostB {
    font-family: "Cascadia Mono";
    font-size: 10px;
    color: #7F958B;
}
#liveB {
    font-family: "Cascadia Mono";
    font-size: 10px;
    color: #5FB98A;
}
#timeB {
    font-family: "Cascadia Mono";
    font-size: 10px;
    color: #7F958B;
}
QPushButton#outlineDarkB {
    background-color: transparent;
    border: 1px solid #2A3E34;
    border-radius: 2px;
    padding: 5px 12px;
    color: #DCE7E1;
    font-size: 12px;
}
QPushButton#outlineDarkB:hover { background-color: #17241E; border-color: #3A5347; }

#tabsB { background-color: #0C1210; border-bottom: 1px solid #1E2D26; }
QPushButton#tabItemB, QPushButton#tabActiveB {
    background-color: transparent;
    border: none;
    border-bottom: 2px solid transparent;
    padding: 0 14px;
    font-size: 12px;
    color: #7F958B;
}
QPushButton#tabItemB:hover { color: #E6EDE9; }
QPushButton#tabActiveB {
    border-bottom: 2px solid #E3A857;
    color: #F2F7F4;
    font-weight: 600;
}
#tabMetaB {
    font-family: "Cascadia Mono";
    font-size: 10px;
    color: #6F857A;
}

#sectionTitleB { font-size: 14px; font-weight: 700; color: #E6EDE9; }
#sectionMetaB {
    font-family: "Cascadia Mono";
    font-size: 10px;
    color: #6F857A;
}
#panelB {
    background-color: #101A16;
    border: 1px solid #22332B;
    border-radius: 3px;
}
#panelKickerB {
    font-family: "Cascadia Mono";
    font-size: 9px;
    color: #6F857A;
}
#metricLabelB { font-size: 10px; color: #7F958B; }
#metricValueB {
    font-family: "Bahnschrift";
    font-size: 27px;
    font-weight: 700;
    color: #F2F7F4;
}
#metricDeltaB {
    font-family: "Cascadia Mono";
    font-size: 9px;
    color: #5FB98A;
}
#metricUnitB {
    font-family: "Cascadia Mono";
    font-size: 10px;
    color: #7F958B;
}
#metricSubB {
    font-family: "Cascadia Mono";
    font-size: 9px;
    color: #6F857A;
}
#panelTitleB { font-size: 13px; font-weight: 700; color: #E6EDE9; }
#liveDotB {
    font-family: "Cascadia Mono";
    font-size: 9px;
    color: #5FB98A;
}
#sideLabelB { font-size: 10px; color: #7F958B; }
#sideValueB {
    font-family: "Cascadia Mono";
    font-size: 10px;
    color: #DCE7E1;
}
QTableWidget#deviceTableB {
    background-color: #101A16;
    alternate-background-color: #101A16;
    border: none;
    gridline-color: transparent;
    outline: none;
    selection-background-color: #16241E;
    selection-color: #F2F7F4;
}
QTableWidget#deviceTableB::item {
    border-bottom: 1px solid #1B2A23;
    padding: 4px 8px;
}
QTableWidget#deviceTableB QHeaderView {
    background-color: #101A16;
}
QTableWidget#deviceTableB QHeaderView::section {
    background-color: #101A16;
    border: none;
    border-bottom: 1px solid #22332B;
    color: #6F857A;
    font-size: 9px;
    font-weight: 600;
    padding: 7px 8px;
}
QTableWidget#deviceTableB QTableCornerButton::section {
    background-color: transparent;
    border: none;
}
"""


def _label(text: str, name: str = "", size: int | None = None,
           family: str | None = None, weight: int | None = None,
           color: str | None = None) -> QLabel:
    w = QLabel(text)
    if name:
        w.setObjectName(name)
    if size:
        w.setFont(qfont(family or SANS, size, weight or QFont.Weight.Normal))
    elif family:
        w.setFont(qfont(family, 13, weight or QFont.Weight.Normal))
    if color:
        w.setStyleSheet(f"color: {color};")
    return w


def _tab(text: str, active: bool = False) -> QPushButton:
    btn = QPushButton(text)
    btn.setObjectName("tabActiveB" if active else "tabItemB")
    btn.setFixedHeight(46)
    btn.setCursor(Qt.CursorShape.PointingHandCursor)
    return btn


class TopologyMap(QWidget):
    """自绘系统拓扑，节点位置随控件尺寸缩放。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(340)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()

        # 低对比网格
        p.setPen(QPen(QColor("#14231D"), 1))
        for x in range(0, w, 32):
            p.drawLine(x, 0, x, h)
        for y in range(0, h, 32):
            p.drawLine(0, y, w, y)

        cx = w / 2
        cpu = QRectF(cx - 95, 22, 190, 64)
        mem = QRectF(36, 150, 190, 64)
        gpu = QRectF(w - 226, 150, 190, 64)
        sto = QRectF(36, 262, 190, 64)
        net = QRectF(cx - 95, 262, 190, 64)
        disp = QRectF(w - 226, 262, 190, 64)

        bus_y = 112
        left_x = mem.center().x()
        right_x = gpu.center().x()

        # 总线
        p.setPen(QPen(QColor("#2C4A3D"), 1))
        p.drawLine(QPointF(cpu.center().x(), cpu.bottom()), QPointF(cpu.center().x(), bus_y))
        p.drawLine(QPointF(left_x, bus_y), QPointF(right_x, bus_y))
        p.drawLine(QPointF(left_x, bus_y), QPointF(left_x, mem.top()))
        p.drawLine(QPointF(right_x, bus_y), QPointF(right_x, gpu.top()))
        p.drawLine(QPointF(cx, bus_y), QPointF(cx, net.top()))
        p.drawLine(QPointF(left_x, mem.bottom()), QPointF(left_x, sto.top()))
        p.drawLine(QPointF(right_x, gpu.bottom()), QPointF(right_x, disp.top()))

        # 连接点
        p.setBrush(QColor(AMBER))
        p.setPen(Qt.PenStyle.NoPen)
        for pt in [
            QPointF(cx, bus_y), QPointF(left_x, bus_y), QPointF(right_x, bus_y),
            QPointF(left_x, mem.top()), QPointF(right_x, gpu.top()),
        ]:
            p.drawRect(QRectF(pt.x() - 2, pt.y() - 2, 4, 4))

        # 连线标注
        p.setFont(qfont(MONO, 8))
        p.setPen(QColor("#6F857A"))
        p.drawText(QPointF(left_x + 8, bus_y - 7), "DDR5-7200")
        p.drawText(QPointF(right_x - 62, bus_y - 7), "PCIe 5.0 x16")
        p.drawText(QPointF(left_x + 8, 240), "NVMe")
        p.drawText(QPointF(cx + 8, 240), "2.5GbE")
        p.drawText(QPointF(right_x - 40, 240), "DP 1.4")

        self._node(p, cpu, "PROCESSOR", f"{d.CPU_CORES}C / {d.CPU_THREADS}T", accent=True)
        self._node(p, mem, "MEMORY", "48 GB DDR5")
        self._node(p, gpu, "GRAPHICS", "RTX 2080 Ti")
        self._node(p, sto, "STORAGE", "1.4 TB")
        self._node(p, net, "NETWORK", "Wi-Fi 6E")
        self._node(p, disp, "DISPLAY", "3 台显示器")
        p.end()

    def _node(self, p: QPainter, rect: QRectF, kicker: str, value: str,
              accent: bool = False) -> None:
        p.setBrush(QColor("#14231D"))
        p.setPen(QPen(QColor(AMBER if accent else "#2B4036"), 1))
        p.drawRoundedRect(rect, 4, 4)

        # 状态点
        p.setBrush(QColor(MINT))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(QPointF(rect.right() - 12, rect.top() + 12), 3, 3)

        p.setFont(qfont(MONO, 8))
        p.setPen(QColor(AMBER if accent else "#6F857A"))
        p.drawText(QPointF(rect.left() + 12, rect.top() + 20), kicker)

        p.setFont(qfont(MONO, 13, QFont.Weight.DemiBold))
        p.setPen(QColor(TEXT))
        p.drawText(QPointF(rect.left() + 12, rect.top() + 45), value)


class Sparkline(QWidget):
    def __init__(self, data: list[int], color: str, parent=None):
        super().__init__(parent)
        self._data = data
        self._color = QColor(color)
        self.setFixedHeight(34)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()

        p.setPen(QPen(QColor("#22332B"), 1))
        for frac in (0.25, 0.5, 0.75):
            y = h * frac
            p.drawLine(0, int(y), w, int(y))

        if not self._data:
            return
        top, bottom = 4, h - 4
        step = w / max(1, len(self._data) - 1)
        points = []
        for i, value in enumerate(self._data):
            x = i * step
            y = bottom - (max(0, min(100, value)) / 100) * (bottom - top)
            points.append(QPointF(x, y))

        area = QPainterPath()
        area.moveTo(points[0].x(), bottom)
        for pt in points:
            area.lineTo(pt)
        area.lineTo(points[-1].x(), bottom)
        area.closeSubpath()
        fill = QColor(self._color)
        fill.setAlpha(28)
        p.fillPath(area, fill)

        line = QPainterPath()
        line.moveTo(points[0])
        for pt in points[1:]:
            line.lineTo(pt)
        p.setPen(QPen(self._color, 1.6))
        p.drawPath(line)

        p.setBrush(self._color)
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(points[-1], 2.5, 2.5)


class MetricBlock(QWidget):
    def __init__(self, label: str, value: str, sub: str, data: list[int],
                 color: str, delta: str = "", parent=None):
        super().__init__(parent)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 5, 0, 5)
        lay.setSpacing(0)

        top = QHBoxLayout()
        top.setSpacing(6)
        top.addWidget(_label(label, "metricLabelB"))
        top.addStretch()
        if delta:
            top.addWidget(_label(delta, "metricDeltaB"))
        lay.addLayout(top)
        lay.addSpacing(1)

        mid = QHBoxLayout()
        mid.setSpacing(5)
        mid.addWidget(_label(value, "metricValueB"))
        mid.addWidget(_label("%", "metricUnitB"), alignment=Qt.AlignmentFlag.AlignBottom)
        mid.addStretch()
        mid.addWidget(_label(sub, "metricSubB"), alignment=Qt.AlignmentFlag.AlignBottom)
        lay.addLayout(mid)
        lay.addSpacing(2)
        lay.addWidget(Sparkline(data, color))


def _top_bar() -> QWidget:
    bar = QWidget()
    bar.setObjectName("topBarB")
    bar.setFixedHeight(64)
    lay = QHBoxLayout(bar)
    lay.setContentsMargins(24, 0, 24, 0)
    lay.setSpacing(14)

    lay.addWidget(_label("HWINFO", "brandB"))
    lay.addWidget(vline("#22332B", 1))
    lay.addWidget(_label(f"{d.HOST}  /  {d.MODEL}", "hostB"))
    lay.addStretch()
    lay.addWidget(_label("●  LIVE  2s", "liveB"))
    lay.addWidget(_label(d.COLLECTED_AT, "timeB"))

    refresh = QPushButton(" 刷新")
    refresh.setObjectName("outlineDarkB")
    refresh.setIcon(qicon("refresh", "#DCE7E1", 14))
    refresh.setIconSize(QSize(14, 14))
    refresh.setCursor(Qt.CursorShape.PointingHandCursor)
    lay.addWidget(refresh)

    export = QPushButton(" 导出")
    export.setObjectName("outlineDarkB")
    export.setIcon(qicon("export", "#DCE7E1", 14))
    export.setIconSize(QSize(14, 14))
    export.setCursor(Qt.CursorShape.PointingHandCursor)
    lay.addWidget(export)
    return bar


def _tabs() -> QWidget:
    tabs = QWidget()
    tabs.setObjectName("tabsB")
    tabs.setFixedHeight(46)
    lay = QHBoxLayout(tabs)
    lay.setContentsMargins(24, 0, 24, 0)
    lay.setSpacing(2)
    names = ["总览", "处理器", "显卡", "内存", "存储", "网络", "音频", "显示器", "主板", "系统"]
    for i, name in enumerate(names):
        lay.addWidget(_tab(name, i == 0))
    lay.addStretch()
    lay.addWidget(_label(f"采集于 {d.COLLECTED_AT}", "tabMetaB"))
    return tabs


def _sections_header(title: str, meta: str) -> QHBoxLayout:
    row = QHBoxLayout()
    row.setSpacing(8)
    row.addWidget(_label(title, "sectionTitleB"))
    row.addStretch()
    row.addWidget(_label(meta, "sectionMetaB"))
    return row


def _topology() -> QWidget:
    panel = QWidget()
    panel.setObjectName("panelB")
    panel.setFixedHeight(380)
    lay = QVBoxLayout(panel)
    lay.setContentsMargins(0, 0, 0, 0)
    lay.addWidget(TopologyMap())
    return panel


def _metrics_panel() -> QWidget:
    panel = QWidget()
    panel.setObjectName("panelB")
    panel.setFixedWidth(340)
    panel.setFixedHeight(412)
    lay = QVBoxLayout(panel)
    lay.setContentsMargins(18, 12, 18, 12)
    lay.setSpacing(0)

    head = QHBoxLayout()
    head.setSpacing(6)
    head.addWidget(_label("实时监控", "panelTitleB"))
    head.addStretch()
    head.addWidget(_label("●  LIVE  2s", "liveDotB"))
    lay.addLayout(head)
    lay.addSpacing(5)
    lay.addWidget(hline("#22332B"))
    lay.addSpacing(1)

    lay.addWidget(MetricBlock(
        "CPU 负载", "34", "24C/24T · 1.69 GHz",
        [12, 18, 14, 22, 30, 25, 34, 28, 31, 34], AMBER, "▲ 2.1%",
    ))
    lay.addWidget(hline("#1B2A23"))
    lay.addWidget(MetricBlock(
        "GPU 负载", "62", "RTX 2080 Ti · 11 GB",
        [20, 28, 35, 30, 48, 55, 51, 66, 58, 62], MINT, "▲ 7.4%",
    ))
    lay.addWidget(hline("#1B2A23"))
    lay.addWidget(MetricBlock(
        "内存占用", "44", "21.0 / 48 GB · DDR5",
        [38, 39, 41, 40, 42, 43, 42, 45, 44, 44], BLUE, "▲ 0.3%",
    ))

    lay.addSpacing(4)
    lay.addWidget(hline("#22332B"))
    lay.addSpacing(8)
    summary = QHBoxLayout()
    summary.setSpacing(6)
    summary.addWidget(_label("9 / 9 类别", "sideLabelB"))
    summary.addStretch()
    summary.addWidget(_label(f"{d.ELAPSED}  ·  0 错误", "sideValueB"))
    lay.addLayout(summary)
    return panel


def _device_table() -> QTableWidget:
    table = QTableWidget(len(d.DEVICE_ROWS), 4)
    table.setObjectName("deviceTableB")
    table.setHorizontalHeaderLabels(["类别", "设备", "状态", "驱动 / 版本"])
    table.verticalHeader().setVisible(False)
    table.verticalHeader().setDefaultSectionSize(34)
    table.setShowGrid(False)
    table.setFrameShape(QFrame.Shape.NoFrame)
    table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
    table.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
    table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
    table.setWordWrap(False)
    table.setFixedHeight(32 + 7 * 34)

    header = table.horizontalHeader()
    header.setFixedHeight(32)
    header.setHighlightSections(False)
    header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
    header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
    header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
    header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
    table.setColumnWidth(0, 84)
    table.setColumnWidth(2, 104)
    table.setColumnWidth(3, 180)
    for c in (0, 1, 2, 3):
        table.horizontalHeaderItem(c).setTextAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        )

    for row, (cat, device, status, extra) in enumerate(d.DEVICE_ROWS):
        values = [
            (cat, qfont(SANS, 10, QFont.Weight.DemiBold), "#7F958B"),
            (device, qfont(SANS, 11), "#E6EDE9"),
            (f"●  {status}", qfont(MONO, 9), "#5FB98A"),
            (extra, qfont(MONO, 9), "#8FA39B"),
        ]
        for col, (text, font, color) in enumerate(values):
            item = QTableWidgetItem(text)
            item.setFont(font)
            item.setForeground(QColor(color))
            item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            table.setItem(row, col, item)
    return table


class WindowB(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("HWInfo — Night Bench")
        self.setStyleSheet(QSS_B)

        root = QWidget()
        root.setObjectName("rootB")
        self.setCentralWidget(root)
        root_lay = QVBoxLayout(root)
        root_lay.setContentsMargins(0, 0, 0, 0)
        root_lay.setSpacing(0)

        root_lay.addWidget(_top_bar())
        root_lay.addWidget(_tabs())

        content = QWidget()
        lay = QVBoxLayout(content)
        lay.setContentsMargins(24, 18, 24, 18)
        lay.setSpacing(0)

        top = QHBoxLayout()
        top.setSpacing(16)

        left = QVBoxLayout()
        left.setSpacing(8)
        left.addLayout(_sections_header("系统拓扑", "6 个节点  ·  全部在线"))
        left.addWidget(_topology())
        top.addLayout(left, 1)
        top.addWidget(_metrics_panel())
        lay.addLayout(top)

        lay.addSpacing(16)
        lay.addLayout(_sections_header("设备清单", "7 项  ·  采集于 14:32:08"))
        lay.addSpacing(8)
        lay.addWidget(_device_table())
        root_lay.addWidget(content, 1)


def build_window() -> QMainWindow:
    return WindowB()


if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    w = build_window()
    w.resize(1440, 900)
    w.show()
    sys.exit(app.exec())
