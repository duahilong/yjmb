"""便当格 · 处理器详情页原型。"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "shared"))

from PySide6.QtCore import Qt                                # noqa: E402
from PySide6.QtWidgets import (                              # noqa: E402
    QGridLayout, QHBoxLayout, QLabel, QMainWindow, QVBoxLayout, QWidget,
)

import mock_data as d                                       # noqa: E402
from ui import CoreGrid, MeterBar, hline, label               # noqa: E402
from bento_kit import (                                     # noqa: E402
    BASE_QSS, C_CPU, C_MEM, C_MB, build_top_bar, card, definition_grid,
    kv_row, mini_stat, pill,
)

QSS = BASE_QSS


def _tag(text: str) -> QLabel:
    lb = QLabel(text)
    lb.setStyleSheet(
        "background-color: #EDF0F4; color: #6B7686; border-radius: 999px;"
        "padding: 3px 10px; font-size: 10px; font-family: 'Cascadia Mono';"
    )
    return lb


def _cache_row(name: str, value: str, frac: float, accent: str) -> QWidget:
    box = QWidget()
    lay = QVBoxLayout(box)
    lay.setContentsMargins(0, 0, 0, 0)
    lay.setSpacing(6)
    line = QHBoxLayout()
    line.setSpacing(8)
    line.addWidget(label(name, "rowNameBento"))
    line.addStretch()
    line.addWidget(label(value, "rowSubBento"))
    lay.addLayout(line)
    lay.addWidget(MeterBar(frac, track="#EDF0FE", gradient=(accent, "#A5B4FC")))
    return box


def _model_card() -> QWidget:
    frame, body = card("处理器型号", C_CPU, "cpu", "LGA1700")
    body.addWidget(label(d.CPU, "cardValueBento"))
    body.addWidget(label("GenuineIntel · x64 · 64 位", "cardSubBento"))
    body.addSpacing(12)
    grid = QGridLayout()
    grid.setSpacing(0)
    for i, (v, k) in enumerate([
        (str(d.CPU_CORES), "核心"),
        (str(d.CPU_THREADS), "线程"),
        (d.CPU_FREQ, "基准频率"),
        ("36 MB", "L3 缓存"),
    ]):
        r, c = divmod(i, 2)
        cell = QWidget()
        cell_lay = QVBoxLayout(cell)
        cell_lay.setContentsMargins(0, 0, 0, 0)
        cell_lay.addLayout(mini_stat(v, k))
        grid.addWidget(cell, r, c)
        grid.setColumnStretch(c, 1)
    body.addLayout(grid)
    return frame


def _cores_card() -> QWidget:
    frame, body = card("核心与频率", C_CPU, "chip", "24C/24T")
    body.addSpacing(2)
    body.addWidget(CoreGrid(d.CPU_THREADS, C_CPU, "#EDF0FE", cols=12, cell=16, gap=8))
    body.addSpacing(14)
    body.addWidget(kv_row("基准频率", d.CPU_FREQ))
    body.addSpacing(9)
    body.addWidget(kv_row("插槽", d.CPU_SOCKET))
    return frame


def _cache_card() -> QWidget:
    frame, body = card("缓存", C_MB, "layers")
    body.addWidget(_cache_row("L1 数据缓存", "1.1 MB", 0.12, C_MB))
    body.addSpacing(14)
    body.addWidget(_cache_row("L2 缓存", "32 MB", 0.55, C_MB))
    body.addSpacing(14)
    body.addWidget(_cache_row("L3 缓存", "36 MB", 0.9, C_MB))
    return frame


def _feature_card() -> QWidget:
    frame, body = card("虚拟化与特性", C_MEM, "shield", "已启用")
    body.addWidget(kv_row("硬件虚拟化", "已启用", value_color=C_MEM))
    body.addSpacing(9)
    body.addWidget(kv_row("二级地址转换", "支持", value_color=C_MEM))
    body.addSpacing(9)
    body.addWidget(kv_row("硬件 DEP", "支持"))
    body.addSpacing(14)
    chips = QGridLayout()
    chips.setHorizontalSpacing(6)
    chips.setVerticalSpacing(6)
    for i, name in enumerate(["SSE", "SSE2", "SSE3", "SSSE3", "SSE4.1", "SSE4.2",
                              "AVX", "AVX2", "AES", "VT-x"]):
        chips.addWidget(_tag(name), i // 5, i % 5)
    body.addLayout(chips)
    return frame


def _spec_card() -> QWidget:
    frame, body = card("规格明细", C_CPU, "cpu")
    rows = [
        ("名称", d.CPU),
        ("制造商", "GenuineIntel"),
        ("处理器 ID", "CPU Family 6 / Model 183"),
        ("架构", "x64"),
        ("插槽", d.CPU_SOCKET),
        ("基准频率", d.CPU_FREQ),
        ("最大频率", "5.80 GHz"),
        ("外频", "100 MHz"),
        ("L2 缓存", "32 MB"),
        ("L3 缓存", "36 MB"),
        ("虚拟化", "已启用"),
        ("当前负载", "12 %"),
    ]
    body.addWidget(definition_grid(rows, columns=3))
    return frame


class WindowDetailCPU(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("HWInfo — Bento · 处理器详情")
        self.setStyleSheet(QSS)
        root = QWidget()
        root.setObjectName("rootBento")
        self.setCentralWidget(root)
        outer = QVBoxLayout(root)
        outer.setContentsMargins(28, 20, 28, 22)
        outer.setSpacing(0)

        outer.addWidget(build_top_bar("总览  /  处理器", f"采集于 {d.COLLECTED_AT}  ·  {d.ELAPSED}"))
        outer.addSpacing(16)

        header = QHBoxLayout()
        header.setSpacing(10)
        header.addWidget(label("处理器", "pageTitleBento"))
        header.addWidget(pill(f"{d.CPU_CORES}C / {d.CPU_THREADS}T", C_CPU),
                         alignment=Qt.AlignmentFlag.AlignVCenter)
        header.addWidget(label("Genuine Intel · LGA1700 · 基准 1.69 GHz", "pageMetaBento"),
                         alignment=Qt.AlignmentFlag.AlignVCenter)
        header.addStretch()
        from bento_kit import action_button
        header.addWidget(action_button("复制摘要", "export", ghost=True))
        header.addWidget(action_button("重新采集", "refresh"))
        outer.addLayout(header)
        outer.addSpacing(16)

        grid = QGridLayout()
        grid.setSpacing(16)
        for c in range(4):
            grid.setColumnStretch(c, 1)
        grid.setRowMinimumHeight(0, 214)
        grid.setRowMinimumHeight(1, 224)
        grid.setRowMinimumHeight(2, 236)

        grid.addWidget(_model_card(), 0, 0, 1, 2)
        grid.addWidget(_cores_card(), 0, 2, 1, 2)
        grid.addWidget(_cache_card(), 1, 0, 1, 2)
        grid.addWidget(_feature_card(), 1, 2, 1, 2)
        grid.addWidget(_spec_card(), 2, 0, 1, 4)
        outer.addLayout(grid, 1)


def build_window() -> QMainWindow:
    return WindowDetailCPU()


if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication
    app = QApplication(sys.argv)
    win = build_window()
    win.resize(1440, 900)
    win.show()
    sys.exit(app.exec())
