"""风格 03 · BENTO —— 便当格总览。

浅灰底 + 白色大圆角卡片 + 柔和阴影 + 每类一色的图标块。
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "shared"))

from PySide6.QtCore import Qt                                # noqa: E402
from PySide6.QtWidgets import (                              # noqa: E402
    QFrame, QGridLayout, QHBoxLayout, QLabel, QMainWindow, QVBoxLayout, QWidget,
)

import mock_data as d                                       # noqa: E402
from ui import CoreGrid, MeterBar, SlotRow, hline, icon_pixmap, label, rgba, vline  # noqa: E402
from bento_kit import (                                     # noqa: E402
    BASE_QSS, C_AUD, C_CPU, C_DSP, C_GPU, C_MB, C_MEM, C_NET, C_STO,
    build_top_bar, card, mini_stat, pill,
)

QSS = BASE_QSS


def _mini_stat(value: str, key: str) -> QVBoxLayout:
    return mini_stat(value, key)


def _identity_card() -> QFrame:
    frame = QFrame()
    frame.setObjectName("identityBento")
    frame.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
    from ui import shadow
    shadow(frame, "#A9B4C4", blur=30, dy=10, alpha=70)

    lay = QVBoxLayout(frame)
    lay.setContentsMargins(24, 20, 24, 20)
    lay.setSpacing(0)

    top = QHBoxLayout()
    top.setSpacing(10)
    top.addWidget(label("本机 / THIS MACHINE", "idKickerBento"))
    top.addStretch()
    top.addWidget(pill(f"{d.CATEGORIES_OK} / {d.CATEGORIES_TOTAL} 类别完整", C_MEM))
    lay.addLayout(top)
    lay.addSpacing(8)

    lay.addWidget(label(d.MODEL, "idModelBento"))
    lay.addWidget(label(f"{d.VENDOR} · {d.OS_NAME} · {d.OS_VERSION}", "idSubBento"))
    lay.addSpacing(2)
    lay.addWidget(label(
        f"{d.HOST}  ·  BIOS {d.BIOS}  ·  {d.FIRMWARE}  ·  {d.COLLECTED_DATE} {d.COLLECTED_AT}",
        "rowSubBento"))
    lay.addStretch()
    lay.addWidget(hline("#E6EAF0"))
    lay.addSpacing(12)

    stats = QHBoxLayout()
    stats.setSpacing(0)
    for i, (v, k) in enumerate([
        (f"{d.CPU_CORES}C/{d.CPU_THREADS}T", "处理器"),
        (d.RAM_TOTAL, "内存"),
        (d.GPU, "显卡"),
        (d.DISK_TOTAL, "存储"),
    ]):
        stats.addLayout(_mini_stat(v, k), 1)
        if i < 3:
            stats.addSpacing(12)
            stats.addWidget(vline("#E6EAF0"))
            stats.addSpacing(12)
    lay.addLayout(stats)
    return frame


def _cpu_card() -> QFrame:
    frame, body = card("处理器", C_CPU, "cpu", "24C/24T")
    body.addWidget(label(f"{d.CPU_CORES}C / {d.CPU_THREADS}T", "cardValueBento"))
    body.addWidget(label(f"Genuine Intel · {d.CPU_FREQ} · {d.CPU_SOCKET}", "cardSubBento"))
    body.addSpacing(8)
    body.addWidget(CoreGrid(d.CPU_THREADS, C_CPU, "#EDF0FE", cols=12, cell=9, gap=4))
    return frame


def _memory_card() -> QFrame:
    frame, body = card("内存", C_MEM, "memory", "DDR5")
    body.addWidget(label(d.RAM_TOTAL, "cardValueBento"))
    body.addWidget(label(f"{d.RAM_SPEED} · {d.RAM_LATENCY} · 双通道", "cardSubBento"))
    body.addSpacing(10)
    body.addWidget(SlotRow(d.RAM_SLOTS_TOTAL, d.RAM_SLOTS_USED, C_MEM, "#E7EBF0"))
    body.addSpacing(6)
    body.addWidget(label(f"{d.RAM_SLOTS_USED} / {d.RAM_SLOTS_TOTAL} 插槽已用", "cardSubBento"))
    return frame


def _gpu_card() -> QFrame:
    frame, body = card("显卡", C_GPU, "gpu", "独显")
    body.addWidget(label(d.GPU, "cardValueBento"))
    body.addWidget(label("NVIDIA GeForce · 驱动 " + d.GPU_DRIVER, "cardSubBento"))
    body.addSpacing(10)
    body.addWidget(MeterBar(0.86, track="#FDEEE3", gradient=(C_GPU, "#FBBF24")))
    body.addSpacing(6)
    body.addWidget(label(f"{d.GPU_VRAM} VRAM · PCIe 5.0 x16", "cardSubBento"))
    return frame


def _network_row(icon: str, name: str, sub: str, accent: str) -> QWidget:
    row = QWidget()
    lay = QHBoxLayout(row)
    lay.setContentsMargins(0, 0, 0, 0)
    lay.setSpacing(10)
    mark = QLabel()
    mark.setFixedSize(30, 30)
    mark.setAlignment(Qt.AlignmentFlag.AlignCenter)
    mark.setPixmap(icon_pixmap(icon, accent, 16))
    mark.setStyleSheet(f"background-color: {rgba(accent, 0.10)}; border-radius: 9px;")
    lay.addWidget(mark)
    txt = QVBoxLayout()
    txt.setSpacing(0)
    txt.addWidget(label(name, "rowNameBento"))
    txt.addWidget(label(sub, "rowSubBento"))
    lay.addLayout(txt, 1)
    return row


def _network_card() -> QFrame:
    frame, body = card("网络", C_NET, "network", "已连接")
    body.addWidget(_network_row("wifi", d.WIFI, "Wi-Fi 6E · 无线", C_NET))
    body.addSpacing(8)
    body.addWidget(hline("#E6EAF0"))
    body.addSpacing(8)
    body.addWidget(_network_row("ethernet", d.LAN, "2.5 Gbps · 以太网", C_NET))
    return frame


def _disk_row(name: str, used: str, total: str, value: float, accent: str) -> QWidget:
    row = QWidget()
    lay = QVBoxLayout(row)
    lay.setContentsMargins(0, 0, 0, 0)
    lay.setSpacing(6)
    head = QHBoxLayout()
    head.setSpacing(10)
    mark = QLabel()
    mark.setFixedSize(30, 30)
    mark.setAlignment(Qt.AlignmentFlag.AlignCenter)
    mark.setPixmap(icon_pixmap("storage", accent, 16))
    mark.setStyleSheet(f"background-color: {rgba(accent, 0.10)}; border-radius: 9px;")
    head.addWidget(mark)
    head.addWidget(label(name, "rowNameBento"), 1)
    head.addWidget(label(f"{used} / {total}", "rowSubBento"))
    lay.addLayout(head)
    lay.addWidget(MeterBar(value, track="#EDEBFA", gradient=(accent, "#A78BFA")))
    return row


def _storage_card() -> QFrame:
    frame, body = card("存储", C_STO, "storage", "2 块")
    body.addWidget(_disk_row(f"{d.DISK_1} · {d.DISK_1_IF}",
                             d.DISK_1_USED, d.DISK_1_SIZE, 0.666, C_STO))
    body.addSpacing(12)
    body.addWidget(hline("#E6EAF0"))
    body.addSpacing(12)
    body.addWidget(_disk_row(f"{d.DISK_2} · {d.DISK_2_IF}",
                             d.DISK_2_USED, d.DISK_2_SIZE, 0.442, "#A78BFA"))
    return frame


def _display_card() -> QFrame:
    frame, body = card("显示器", C_DSP, "monitor")
    screens = QHBoxLayout()
    screens.setSpacing(10)
    body.addLayout(screens)
    for name, spec in [(d.MONITOR_1, "4K · 120 Hz"), (d.MONITOR_2, "1080p · 60 Hz")]:
        box = QVBoxLayout()
        box.setSpacing(6)
        glyph = QLabel()
        glyph.setFixedHeight(52)
        glyph.setPixmap(icon_pixmap("monitor", rgba(C_DSP, 0.75), 32))
        glyph.setAlignment(Qt.AlignmentFlag.AlignCenter)
        glyph.setStyleSheet(f"background-color: {rgba(C_DSP, 0.08)}; border-radius: 12px;")
        box.addWidget(glyph)
        box.addWidget(label(name, "rowNameBento"))
        box.addWidget(label(spec, "rowSubBento"))
        screens.addLayout(box, 1)
    return frame


def _audio_card() -> QFrame:
    frame, body = card("音频", C_AUD, "audio")
    body.addWidget(label("Realtek HD", "cardValueBento"))
    body.addWidget(label("High Definition Audio · 板载", "cardSubBento"))
    body.addSpacing(10)
    body.addWidget(MeterBar(0.7, track="#FEF3E2", gradient=(C_AUD, "#FBBF24")))
    body.addSpacing(6)
    body.addWidget(label("驱动 " + d.AUDIO_DRIVER, "cardSubBento"))
    return frame


def _system_card() -> QFrame:
    frame, body = card("主板 / 系统", C_MB, "motherboard", d.FIRMWARE)
    body.addWidget(label(f"{d.VENDOR} {d.MODEL}", "cardValueBento"))
    body.addWidget(label(f"{d.BOARD} · BIOS {d.BIOS}", "cardSubBento"))
    body.addSpacing(8)
    for k, v in [("操作系统", f"Windows 11 · {d.OS_VERSION}"), ("固件", f"{d.FIRMWARE} · 安全启动")]:
        line = QHBoxLayout()
        line.setSpacing(8)
        line.addWidget(label(k, "miniLabelBento"))
        line.addStretch()
        line.addWidget(label(v, "rowSubBento"))
        body.addLayout(line)
    return frame


def _collector_card() -> QFrame:
    frame, body = card("采集", C_MEM, "check", "完成")
    body.addWidget(label(f"{d.CATEGORIES_OK} / {d.CATEGORIES_TOTAL}", "cardValueBento"))
    body.addWidget(label("类别完成 · 无错误", "cardSubBento"))
    body.addSpacing(8)
    for k, v in [("耗时", d.ELAPSED), ("错误 / 警告", f"{d.ERRORS} / {d.WARNINGS}")]:
        line = QHBoxLayout()
        line.setSpacing(8)
        line.addWidget(label(k, "miniLabelBento"))
        line.addStretch()
        line.addWidget(label(v, "rowSubBento"))
        body.addLayout(line)
    return frame


class WindowBento(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("HWInfo — Bento")
        self.setStyleSheet(QSS)
        root = QWidget()
        root.setObjectName("rootBento")
        self.setCentralWidget(root)
        outer = QVBoxLayout(root)
        outer.setContentsMargins(28, 20, 28, 22)
        outer.setSpacing(0)

        outer.addWidget(build_top_bar(
            f"{d.HOST}  ·  {d.COLLECTED_DATE}",
            f"采集于 {d.COLLECTED_AT}  ·  {d.ELAPSED}",
        ))
        outer.addSpacing(18)

        grid = QGridLayout()
        grid.setSpacing(16)
        for c in range(4):
            grid.setColumnStretch(c, 1)
        grid.setRowMinimumHeight(0, 210)
        grid.setRowMinimumHeight(1, 238)
        grid.setRowMinimumHeight(2, 196)

        grid.addWidget(_identity_card(), 0, 0, 1, 2)
        grid.addWidget(_cpu_card(), 0, 2)
        grid.addWidget(_memory_card(), 0, 3)
        grid.addWidget(_storage_card(), 1, 0, 1, 2)
        grid.addWidget(_gpu_card(), 1, 2)
        grid.addWidget(_network_card(), 1, 3)
        grid.addWidget(_display_card(), 2, 0)
        grid.addWidget(_audio_card(), 2, 1)
        grid.addWidget(_system_card(), 2, 2)
        grid.addWidget(_collector_card(), 2, 3)
        outer.addLayout(grid, 1)


def build_window() -> QMainWindow:
    return WindowBento()


if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication
    app = QApplication(sys.argv)
    win = build_window()
    win.resize(1440, 900)
    win.show()
    sys.exit(app.exec())
