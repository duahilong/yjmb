"""便当格 · 存储详情页原型（设备 + 分区，验证列表型类别）。"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "shared"))

from PySide6.QtCore import Qt                                # noqa: E402
from PySide6.QtWidgets import (                              # noqa: E402
    QGridLayout, QHBoxLayout, QLabel, QMainWindow, QVBoxLayout, QWidget,
)

import mock_data as d                                       # noqa: E402
from ui import MeterBar, hline, label, rgba, vline             # noqa: E402
from bento_kit import (                                     # noqa: E402
    BASE_QSS, C_MEM, C_STO, action_button, build_top_bar, card, kv_row,
    mini_stat, pill,
)

QSS = BASE_QSS


def _device_card(name: str, tag: str, size: str, sub: str, frac: float,
                 rows: list[tuple[str, str]], accent: str) -> QWidget:
    frame, body = card(name, accent, "storage", tag)
    body.addWidget(label(size, "cardValueBento"))
    body.addWidget(label(sub, "cardSubBento"))
    body.addSpacing(10)
    body.addWidget(MeterBar(frac, track="#EDEBFA", gradient=(accent, "#A78BFA")))
    body.addSpacing(6)
    body.addWidget(label(f"已用 {int(frac * 100)}%", "rowSubBento"))
    body.addSpacing(12)
    for k, v in rows:
        body.addWidget(kv_row(k, v))
        body.addSpacing(8)
    return frame


def _badge(text: str, accent: str) -> QLabel:
    lb = QLabel(text)
    lb.setAlignment(Qt.AlignmentFlag.AlignCenter)
    lb.setFixedSize(34, 24)
    lb.setStyleSheet(
        f"background-color: {rgba(accent, 0.12)}; color: {accent};"
        f"border-radius: 8px; font-family: 'Cascadia Mono'; font-size: 11px; font-weight: 700;"
    )
    return lb


def _partition_row(letter: str, name: str, fs: str, used: str, total: str,
                   frac: float, accent: str) -> QWidget:
    box = QWidget()
    lay = QVBoxLayout(box)
    lay.setContentsMargins(0, 0, 0, 0)
    lay.setSpacing(8)
    line = QHBoxLayout()
    line.setSpacing(10)
    line.addWidget(_badge(letter, accent))
    line.addWidget(label(name, "rowNameBento"))
    fs_tag = QLabel(fs)
    fs_tag.setStyleSheet(
        "background-color: #EDF0F4; color: #6B7686; border-radius: 999px;"
        "padding: 2px 9px; font-size: 10px; font-family: 'Cascadia Mono';"
    )
    line.addWidget(fs_tag)
    line.addStretch()
    line.addWidget(label(f"{used} / {total}", "rowSubBento"))
    lay.addLayout(line)
    lay.addWidget(MeterBar(frac, track="#EDEBFA", gradient=(accent, "#A78BFA")))
    return box


def _metrics_card() -> QWidget:
    frame, body = card("存储概览", C_STO, "storage", "健康")
    stats = QHBoxLayout()
    stats.setSpacing(0)
    for i, (v, k) in enumerate([
        (d.DISK_TOTAL, "总容量"),
        ("831.2 GB", "已用空间"),
        ("2", "设备"),
        ("3", "分区"),
    ]):
        stats.addLayout(mini_stat(v, k), 1)
        if i < 3:
            stats.addSpacing(18)
            stats.addWidget(vline("#E6EAF0"))
            stats.addSpacing(18)
    body.addLayout(stats)
    return frame


class WindowDetailStorage(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("HWInfo — Bento · 存储详情")
        self.setStyleSheet(QSS)
        root = QWidget()
        root.setObjectName("rootBento")
        self.setCentralWidget(root)
        outer = QVBoxLayout(root)
        outer.setContentsMargins(28, 20, 28, 22)
        outer.setSpacing(0)

        outer.addWidget(build_top_bar("总览  /  存储", f"采集于 {d.COLLECTED_AT}  ·  {d.ELAPSED}"))
        outer.addSpacing(12)

        header = QHBoxLayout()
        header.setSpacing(10)
        header.addWidget(label("存储", "pageTitleBento"))
        header.addWidget(pill("2 块设备 · 3 个分区", C_STO), alignment=Qt.AlignmentFlag.AlignVCenter)
        header.addWidget(label("NVMe + SATA · 总容量 1.4 TB", "pageMetaBento"),
                         alignment=Qt.AlignmentFlag.AlignVCenter)
        header.addStretch()
        header.addWidget(action_button("复制摘要", "export", ghost=True))
        header.addWidget(action_button("重新采集", "refresh"))
        outer.addLayout(header)
        outer.addSpacing(12)

        grid = QGridLayout()
        grid.setSpacing(16)
        for c in range(4):
            grid.setColumnStretch(c, 1)
        grid.setRowMinimumHeight(0, 122)
        grid.setRowMinimumHeight(1, 292)
        grid.setRowMinimumHeight(2, 252)

        grid.addWidget(_metrics_card(), 0, 0, 1, 4)
        grid.addWidget(_device_card(
            d.DISK_1, d.DISK_1_IF, d.DISK_1_SIZE,
            f"{d.DISK_1_IF} · 固件 {d.DISK_1_FW}", 0.666,
            [("接口", "M.2 NVMe PCIe 4.0"), ("序列号", "S5GXNX0R612345"),
             ("温度", "42 °C")],
            C_STO,
        ), 1, 0, 1, 2)
        grid.addWidget(_device_card(
            d.DISK_2, d.DISK_2_IF, d.DISK_2_SIZE,
            f"{d.DISK_2_IF} · 固件 {d.DISK_2_FW}", 0.442,
            [("接口", "SATA III 6Gb/s"), ("序列号", "WD-WCC4E1234567"),
             ("温度", "38 °C")],
            "#A78BFA",
        ), 1, 2, 1, 2)
        grid.addWidget(_partition_card(), 2, 0, 1, 4)
        outer.addLayout(grid, 1)


def _partition_card() -> QWidget:
    frame, body = card("分区", C_STO, "layers", "3 个")
    body.addWidget(_partition_row("C:", "系统", "NTFS", "200.5 GB", "465.7 GB", 0.43, C_STO))
    body.addSpacing(14)
    body.addWidget(hline("#E6EAF0"))
    body.addSpacing(14)
    body.addWidget(_partition_row("D:", "数据", "NTFS", "419.9 GB", "465.7 GB", 0.90, "#A78BFA"))
    body.addSpacing(14)
    body.addWidget(hline("#E6EAF0"))
    body.addSpacing(14)
    body.addWidget(_partition_row("E:", "游戏", "NTFS", "210.8 GB", "476.9 GB", 0.44, C_MEM))
    return frame


def build_window() -> QMainWindow:
    return WindowDetailStorage()


if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication
    app = QApplication(sys.argv)
    win = build_window()
    win.resize(1440, 900)
    win.show()
    sys.exit(app.exec())
