"""风格 04 · GLASS —— 深色玻璃 / 现代高级感。

深夜蓝黑渐变背景 + 自绘柔光 + 半透明磨砂面板 + 青紫渐变点缀。
强调「层次、光泽、圆角」，偏现代感、偏好看。
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "shared"))

from PySide6.QtCore import Qt                                # noqa: E402
from PySide6.QtGui import QLinearGradient, QPainter, QRadialGradient  # noqa: E402
from PySide6.QtWidgets import (                              # noqa: E402
    QFrame, QGridLayout, QHBoxLayout, QLabel, QMainWindow, QPushButton,
    QVBoxLayout, QWidget,
)

import mock_data as d                                       # noqa: E402
from ui import (                                            # noqa: E402
    DISPLAY, MONO, SANS, W_BOLD, W_DEMI, CoreGrid, Donut, GradientText,
    MeterBar, hline, icon_pixmap, icon_size, label, qc, qicon, rgba, shadow,
    vline,
)

INK = "#F2F6FF"
MUTED = "rgba(226, 233, 255, 0.62)"
FAINT = "rgba(226, 233, 255, 0.42)"
LINE = "rgba(255, 255, 255, 0.10)"
CYAN = "#5EEAD4"
VIOLET = "#A78BFA"
GREEN = "#34D399"

QSS = f"""
QWidget {{ font-family: "{SANS}"; font-size: 13px; color: {INK}; }}
#brandG {{ font-family: "{DISPLAY}"; font-size: 20px; font-weight: 700; color: {INK}; }}
#hostG {{ font-family: "{MONO}"; font-size: 10px; color: {FAINT}; }}
#glassPanel {{
    background-color: rgba(255, 255, 255, 0.055);
    border: 1px solid rgba(255, 255, 255, 0.10);
    border-radius: 20px;
}}
#glassHero {{
    background-color: rgba(255, 255, 255, 0.07);
    border: 1px solid rgba(255, 255, 255, 0.12);
    border-radius: 24px;
}}
#segG {{
    background-color: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 999px;
}}
QPushButton#segItemG, QPushButton#segActiveG {{
    background-color: transparent;
    border: none;
    border-radius: 999px;
    padding: 7px 15px;
    color: {MUTED};
    font-size: 12px;
}}
QPushButton#segItemG:hover {{ color: {INK}; }}
QPushButton#segActiveG {{ background-color: rgba(255, 255, 255, 0.16); color: #FFFFFF; font-weight: 600; }}
QPushButton#circleG {{
    background-color: rgba(255, 255, 255, 0.06);
    border: 1px solid rgba(255, 255, 255, 0.10);
    border-radius: 17px;
    min-width: 34px; max-width: 34px; min-height: 34px; max-height: 34px;
}}
QPushButton#circleG:hover {{ background-color: rgba(255, 255, 255, 0.13); }}
#searchG {{
    background-color: rgba(255, 255, 255, 0.06);
    border: 1px solid rgba(255, 255, 255, 0.10);
    border-radius: 999px;
    padding: 8px 16px;
    color: {FAINT};
    font-size: 12px;
}}
#kickerG {{ font-family: "{MONO}"; font-size: 10px; color: {FAINT}; }}
#panelTitleG {{ font-size: 13px; font-weight: 600; color: {INK}; }}
#valueG {{ font-family: "{DISPLAY}"; font-size: 27px; font-weight: 700; color: {INK}; }}
#subG {{ font-size: 11px; color: {MUTED}; }}
#metricLabelG {{ font-family: "{MONO}"; font-size: 9px; color: {FAINT}; }}
#metricValueG {{ font-family: "{DISPLAY}"; font-size: 30px; font-weight: 700; color: {INK}; }}
#metricSubG {{ font-size: 10px; color: {MUTED}; }}
#rowNameG {{ font-size: 12px; color: {INK}; }}
#rowSubG {{ font-family: "{MONO}"; font-size: 10px; color: {MUTED}; }}
#okG {{ font-family: "{MONO}"; font-size: 10px; color: {GREEN}; }}
"""


class GlassRoot(QWidget):
    """自绘渐变与柔光背景。"""

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()

        base = QLinearGradient(0, 0, w, h)
        base.setColorAt(0.0, qc("#0B0F1A"))
        base.setColorAt(0.5, qc("#121829"))
        base.setColorAt(1.0, qc("#0A0D14"))
        p.fillRect(self.rect(), base)

        g1 = QRadialGradient(w * 0.16, h * 0.08, w * 0.55)
        g1.setColorAt(0.0, qc(CYAN, 0.20))
        g1.setColorAt(1.0, qc(CYAN, 0.0))
        p.fillRect(self.rect(), g1)

        g2 = QRadialGradient(w * 0.90, h * 0.95, w * 0.60)
        g2.setColorAt(0.0, qc(VIOLET, 0.22))
        g2.setColorAt(1.0, qc(VIOLET, 0.0))
        p.fillRect(self.rect(), g2)
        p.end()


def _panel(title: str, kicker: str = "") -> tuple[QFrame, QVBoxLayout]:
    panel = QFrame()
    panel.setObjectName("glassPanel")
    panel.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
    lay = QVBoxLayout(panel)
    lay.setContentsMargins(20, 16, 20, 16)
    lay.setSpacing(0)
    head = QHBoxLayout()
    head.setSpacing(8)
    head.addWidget(label(title, "panelTitleG"))
    head.addStretch()
    if kicker:
        head.addWidget(label(kicker, "kickerG"))
    lay.addLayout(head)
    lay.addSpacing(12)
    body = QVBoxLayout()
    body.setSpacing(6)
    lay.addLayout(body)
    lay.addStretch()
    return panel, body


def _segmented() -> QFrame:
    bar = QFrame()
    bar.setObjectName("segG")
    lay = QHBoxLayout(bar)
    lay.setContentsMargins(4, 4, 4, 4)
    lay.setSpacing(2)
    for i, name in enumerate(["总览", "处理器", "显卡", "内存", "存储", "网络", "显示器"]):
        btn = QPushButton(name)
        btn.setObjectName("segActiveG" if i == 0 else "segItemG")
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        lay.addWidget(btn)
    return bar


def _metric(value: str, unit: str, lb: str, sub: str) -> QWidget:
    box = QWidget()
    lay = QVBoxLayout(box)
    lay.setContentsMargins(0, 0, 0, 0)
    lay.setSpacing(1)
    lay.addWidget(label(lb, "metricLabelG"))
    row = QHBoxLayout()
    row.setSpacing(5)
    row.addWidget(label(value, "metricValueG"))
    row.addWidget(label(unit, "kickerG"), alignment=Qt.AlignmentFlag.AlignBottom)
    row.addStretch()
    lay.addLayout(row)
    lay.addWidget(label(sub, "metricSubG"))
    return box


def _hero() -> QFrame:
    hero = QFrame()
    hero.setObjectName("glassHero")
    hero.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
    shadow(hero, CYAN, blur=70, dy=0, alpha=44)

    lay = QVBoxLayout(hero)
    lay.setContentsMargins(26, 22, 26, 22)
    lay.setSpacing(0)

    top = QHBoxLayout()
    top.setSpacing(14)
    left = QVBoxLayout()
    left.setSpacing(4)
    left.addWidget(label("SYSTEM OVERVIEW  /  系统总览", "kickerG"))
    left.addWidget(GradientText(d.MODEL, CYAN, VIOLET, size=42))
    left.addWidget(label(f"{d.VENDOR} · {d.OS_NAME} · {d.HOST}", "subG"))
    top.addLayout(left, 1)
    top.addWidget(label(f"{d.CATEGORIES_OK}/{d.CATEGORIES_TOTAL}  OK", "okG"),
                  alignment=Qt.AlignmentFlag.AlignTop)
    lay.addLayout(top)
    lay.addSpacing(20)

    metrics = QHBoxLayout()
    metrics.setSpacing(0)
    stats = [
        (f"{d.CPU_CORES}/{d.CPU_THREADS}", "", "核心 / 线程", f"{d.CPU_FREQ} · {d.CPU_SOCKET}"),
        (d.RAM_TOTAL.replace(" GB", ""), "GB", "内存", f"DDR5-7200 · {d.RAM_SLOTS_USED}/{d.RAM_SLOTS_TOTAL} 插槽"),
        (d.GPU_VRAM.replace(" GB", ""), "GB", "显存", d.GPU_FULL),
        (d.DISK_TOTAL.replace(" TB", ""), "TB", "存储", "NVMe + SATA · 2 块"),
    ]
    for i, (v, u, lb, sub) in enumerate(stats):
        metrics.addWidget(_metric(v, u, lb, sub), 1)
        if i < len(stats) - 1:
            metrics.addSpacing(20)
            metrics.addWidget(vline(LINE))
            metrics.addSpacing(20)
    lay.addLayout(metrics)
    lay.addSpacing(18)
    lay.addWidget(MeterBar(1.0, track=qc("#FFFFFF", 0.08), gradient=(CYAN, VIOLET), height=6))
    return hero


def _cpu_panel() -> QFrame:
    panel, body = _panel("处理器", "24C/24T")
    body.addWidget(label(f"{d.CPU_CORES}C / {d.CPU_THREADS}T", "valueG"))
    body.addWidget(label(f"Genuine Intel · {d.CPU_FREQ}", "subG"))
    body.addSpacing(12)
    body.addWidget(CoreGrid(d.CPU_THREADS, qc(CYAN), qc("#FFFFFF", 0.09), cols=12, cell=9, gap=4))
    return panel


def _memory_panel() -> QFrame:
    panel, body = _panel("内存", "DDR5")
    row = QHBoxLayout()
    row.setSpacing(16)
    ring = Donut(0.5, CYAN, qc("#FFFFFF", 0.10), size=118, thickness=9,
                 center="2/4", sub="插槽", center_family=DISPLAY)
    row.addWidget(ring)
    right = QVBoxLayout()
    right.setSpacing(4)
    right.addWidget(label(d.RAM_TOTAL, "valueG"))
    right.addWidget(label(f"{d.RAM_SPEED} · {d.RAM_LATENCY}", "subG"))
    right.addWidget(label("双通道", "rowSubG"))
    right.addStretch()
    row.addLayout(right, 1)
    body.addLayout(row)
    return panel


def _gpu_panel() -> QFrame:
    panel, body = _panel("显卡", "独显")
    body.addWidget(label(d.GPU, "valueG"))
    body.addWidget(label("NVIDIA GeForce · 驱动 " + d.GPU_DRIVER, "subG"))
    body.addSpacing(12)
    body.addWidget(MeterBar(0.86, track=qc("#FFFFFF", 0.08), gradient=(VIOLET, CYAN)))
    body.addSpacing(6)
    body.addWidget(label(f"{d.GPU_VRAM} VRAM · PCIe 5.0 x16", "rowSubG"))
    return panel


def _disk_row(name: str, sub: str, used: str, total: str, value: float) -> QWidget:
    box = QWidget()
    lay = QVBoxLayout(box)
    lay.setContentsMargins(0, 0, 0, 0)
    lay.setSpacing(7)
    head = QHBoxLayout()
    head.setSpacing(8)
    mark = QLabel()
    mark.setPixmap(icon_pixmap("storage", CYAN, 16))
    head.addWidget(mark)
    head.addWidget(label(name, "rowNameG"), 1)
    head.addWidget(label(f"{used} / {total}", "rowSubG"))
    lay.addLayout(head)
    lay.addWidget(MeterBar(value, track=qc("#FFFFFF", 0.08), gradient=(CYAN, VIOLET)))
    lay.addWidget(label(sub, "rowSubG"))
    return box


def _storage_panel() -> QFrame:
    panel, body = _panel("存储", "2 块")
    body.addWidget(_disk_row(d.DISK_1, f"{d.DISK_1_SIZE} · {d.DISK_1_IF}", d.DISK_1_USED, d.DISK_1_SIZE, 0.666))
    body.addSpacing(14)
    body.addWidget(hline(LINE))
    body.addSpacing(14)
    body.addWidget(_disk_row(d.DISK_2, f"{d.DISK_2_SIZE} · {d.DISK_2_IF}", d.DISK_2_USED, d.DISK_2_SIZE, 0.442))
    return panel


def _net_row(icon: str, name: str, sub: str) -> QWidget:
    box = QWidget()
    lay = QHBoxLayout(box)
    lay.setContentsMargins(0, 0, 0, 0)
    lay.setSpacing(10)
    mark = QLabel()
    mark.setPixmap(icon_pixmap(icon, CYAN, 17))
    mark.setFixedSize(28, 28)
    lay.addWidget(mark)
    txt = QVBoxLayout()
    txt.setSpacing(0)
    txt.addWidget(label(name, "rowNameG"))
    txt.addWidget(label(sub, "rowSubG"))
    lay.addLayout(txt, 1)
    return box


def _network_panel() -> QFrame:
    panel, body = _panel("网络", "2 个适配器")
    body.addWidget(_net_row("wifi", d.WIFI, "Wi-Fi 6E · 无线 · 驱动 " + d.WIFI_DRIVER))
    body.addSpacing(12)
    body.addWidget(hline(LINE))
    body.addSpacing(12)
    body.addWidget(_net_row("ethernet", d.LAN, "2.5 Gbps · 以太网 · 驱动 " + d.LAN_DRIVER))
    return panel


def _display_panel() -> QFrame:
    panel, body = _panel("显示器", "2 台")
    row = QHBoxLayout()
    row.setSpacing(12)
    for name, spec in [(d.MONITOR_1, "3840×2160 · 120 Hz"), (d.MONITOR_2, "1920×1080 · 60 Hz")]:
        box = QVBoxLayout()
        box.setSpacing(6)
        glyph = QLabel()
        glyph.setFixedHeight(60)
        glyph.setPixmap(icon_pixmap("monitor", VIOLET, 32))
        glyph.setAlignment(Qt.AlignmentFlag.AlignCenter)
        glyph.setStyleSheet(f"background-color: {rgba(VIOLET, 0.10)}; border-radius: 14px;")
        box.addWidget(glyph)
        box.addWidget(label(name, "rowNameG"))
        box.addWidget(label(spec, "rowSubG"))
        row.addLayout(box, 1)
    body.addLayout(row)
    return panel


class WindowGlass(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("HWInfo — Glass")
        self.setStyleSheet(QSS)
        root = GlassRoot()
        self.setCentralWidget(root)
        outer = QVBoxLayout(root)
        outer.setContentsMargins(28, 20, 28, 24)
        outer.setSpacing(0)

        top = QHBoxLayout()
        top.setSpacing(14)
        top.addWidget(label("HWINFO", "brandG"))
        top.addWidget(label(f"{d.HOST}  ·  {d.COLLECTED_DATE} {d.COLLECTED_AT}", "hostG"))
        top.addStretch()
        top.addWidget(_segmented())
        top.addStretch()
        search = QFrame()
        search.setObjectName("searchG")
        search_lay = QHBoxLayout(search)
        search_lay.setContentsMargins(14, 7, 16, 7)
        search_lay.setSpacing(8)
        s_icon = QLabel()
        s_icon.setPixmap(icon_pixmap("search", rgba("#FFFFFF", 0.45), 14))
        search_lay.addWidget(s_icon)
        search_lay.addWidget(label("搜索  Ctrl K", color="rgba(226, 233, 255, 0.42)"))
        top.addWidget(search)
        for icon in ("refresh", "export"):
            btn = QPushButton()
            btn.setObjectName("circleG")
            btn.setIcon(qicon(icon, INK, 15))
            btn.setIconSize(icon_size(15))
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            top.addWidget(btn)
        outer.addLayout(top)
        outer.addSpacing(18)

        outer.addWidget(_hero())
        outer.addSpacing(16)

        grid = QGridLayout()
        grid.setSpacing(16)
        for c in range(3):
            grid.setColumnStretch(c, 1)
        grid.addWidget(_cpu_panel(), 0, 0)
        grid.addWidget(_memory_panel(), 0, 1)
        grid.addWidget(_gpu_panel(), 0, 2)
        grid.addWidget(_storage_panel(), 1, 0)
        grid.addWidget(_network_panel(), 1, 1)
        grid.addWidget(_display_panel(), 1, 2)
        outer.addLayout(grid, 1)


def build_window() -> QMainWindow:
    return WindowGlass()


if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication
    app = QApplication(sys.argv)
    win = build_window()
    win.resize(1440, 900)
    win.show()
    sys.exit(app.exec())
