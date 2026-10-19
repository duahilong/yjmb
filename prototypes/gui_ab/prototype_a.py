"""方案 A：Bench Sheet / 工程铭牌（浅色规格表）。"""
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QHeaderView, QLabel, QMainWindow, QPushButton,
    QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget, QAbstractItemView,
)

import mock_data as d
from ui_helpers import (
    DISPLAY, MONO, SANS, hline, qfont, qicon, vline,
)

QSS_A = """
QWidget {
    font-family: "Microsoft YaHei UI";
    font-size: 13px;
    color: #16211D;
}
#rootA { background-color: #F1F4F1; }
#railA { background-color: #14201C; }
#wordmarkA {
    font-family: "Bahnschrift";
    font-size: 22px;
    font-weight: 700;
    color: #F1F4F1;
}
#hostA {
    font-family: "Cascadia Mono";
    font-size: 10px;
    color: #8FA39B;
}
QPushButton#navItemA, QPushButton#navActiveA {
    background-color: transparent;
    border: none;
    border-left: 3px solid transparent;
    border-radius: 0;
    text-align: left;
    padding: 0 12px;
    color: #AFC0B8;
    font-size: 13px;
}
QPushButton#navItemA:hover { background-color: #1A2A24; color: #F1F4F1; }
QPushButton#navActiveA {
    background-color: #1D2C26;
    border-left: 3px solid #D9480F;
    color: #F1F4F1;
    font-weight: 600;
}
#railFootA { font-family: "Cascadia Mono"; font-size: 10px; color: #71877D; }

#topBarA { border-bottom: 1px solid #CBD6D0; }
#modelA {
    font-family: "Bahnschrift";
    font-size: 30px;
    font-weight: 700;
    color: #16211D;
}
#subtitleA { font-size: 12px; color: #5E6E68; }
#statusOkA { font-size: 12px; color: #2F7D5B; font-weight: 600; }
#stampA {
    font-family: "Cascadia Mono";
    font-size: 10px;
    color: #7A8A83;
}
QPushButton#outlineA {
    background-color: transparent;
    border: 1px solid #C4D0CA;
    border-radius: 2px;
    padding: 5px 12px;
    color: #16211D;
    font-size: 12px;
}
QPushButton#outlineA:hover { background-color: #E7EDE9; border-color: #AEBDB6; }
QPushButton#outlineA:pressed { background-color: #DDE6E1; }

#systemBandA {
    background-color: #FBFCFA;
    border-top: 1px solid #CBD6D0;
    border-bottom: 1px solid #CBD6D0;
}
#bandLabelA { font-size: 10px; color: #6C7B75; font-weight: 600; }
#bandValueA {
    font-family: "Bahnschrift";
    font-size: 17px;
    font-weight: 600;
    color: #16211D;
}
#bandSubA { font-size: 10px; color: #6C7B75; }

#sectionTitleA { font-size: 15px; font-weight: 700; color: #16211D; }
#sectionMetaA {
    font-family: "Cascadia Mono";
    font-size: 10px;
    color: #7A8A83;
}
QTableWidget#specTableA {
    background-color: #F1F4F1;
    alternate-background-color: #F1F4F1;
    border: none;
    gridline-color: transparent;
    outline: none;
    selection-background-color: transparent;
}
QTableWidget#specTableA::item {
    border-bottom: 1px solid #DDE5E0;
    padding: 4px 8px;
}
QTableWidget#specTableA QHeaderView {
    background-color: #F1F4F1;
}
QTableWidget#specTableA QHeaderView::section {
    background-color: #F1F4F1;
    border: none;
    border-bottom: 1px solid #CBD6D0;
    color: #6C7B75;
    font-size: 10px;
    font-weight: 600;
    padding: 8px;
}
QTableWidget#specTableA QTableCornerButton::section {
    background-color: transparent;
    border: none;
}

#sidePanelA {
    border-left: 1px solid #CBD6D0;
}
#sideKickerA {
    font-family: "Cascadia Mono";
    font-size: 10px;
    color: #7A8A83;
}
#sideBigA {
    font-family: "Bahnschrift";
    font-size: 28px;
    font-weight: 700;
    color: #16211D;
}
#sideLabelA { font-size: 11px; color: #6C7B75; }
#sideLabel2A { font-size: 11px; color: #5E6E68; }
#sideValueA {
    font-family: "Cascadia Mono";
    font-size: 11px;
    color: #16211D;
}
#noteA { font-size: 10px; color: #6C7B75; }
QPushButton#sideButtonA {
    background-color: #D9480F;
    border: none;
    border-radius: 2px;
    padding: 7px 12px;
    color: #FFFFFF;
    font-size: 12px;
    font-weight: 600;
}
QPushButton#sideButtonA:hover { background-color: #BF3E0C; }

#footerA { border-top: 1px solid #CBD6D0; }
#footerTextA {
    font-family: "Cascadia Mono";
    font-size: 10px;
    color: #7A8A83;
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


def _nav_button(icon: str, text: str, active: bool = False) -> QPushButton:
    btn = QPushButton(f"  {text}")
    btn.setObjectName("navActiveA" if active else "navItemA")
    btn.setIcon(qicon(icon, "#F1F4F1" if active else "#AFC0B8", 18))
    btn.setIconSize(QSize(18, 18))
    btn.setFixedHeight(40)
    btn.setCursor(Qt.CursorShape.PointingHandCursor)
    return btn


def _rail() -> QWidget:
    rail = QWidget()
    rail.setObjectName("railA")
    rail.setFixedWidth(224)
    lay = QVBoxLayout(rail)
    lay.setContentsMargins(20, 22, 16, 18)
    lay.setSpacing(0)

    lay.addWidget(_label("HWINFO", "wordmarkA"))
    lay.addSpacing(4)
    lay.addWidget(_label(d.HOST, "hostA"))
    lay.addSpacing(16)
    lay.addWidget(hline("#26352F"))
    lay.addSpacing(12)

    items = [
        ("overview", "总览", True),
        ("os", "操作系统", False),
        ("motherboard", "主板", False),
        ("cpu", "处理器", False),
        ("memory", "内存", False),
        ("gpu", "显卡", False),
        ("storage", "存储", False),
        ("network", "网络", False),
        ("audio", "音频", False),
        ("monitor", "显示器", False),
    ]
    for icon, text, active in items:
        lay.addWidget(_nav_button(icon, text, active))
        lay.addSpacing(2)

    lay.addStretch()
    lay.addWidget(hline("#26352F"))
    lay.addSpacing(10)
    lay.addWidget(_nav_button("settings", "设置", False))
    lay.addSpacing(14)
    lay.addWidget(_label("WINDOWS HARDWARE", "railFootA"))
    lay.addSpacing(2)
    lay.addWidget(_label("v0.1.0", "railFootA"))
    return rail


def _top_bar() -> QWidget:
    bar = QWidget()
    bar.setObjectName("topBarA")
    lay = QHBoxLayout(bar)
    lay.setContentsMargins(24, 18, 24, 16)
    lay.setSpacing(16)

    left = QVBoxLayout()
    left.setSpacing(4)
    left.addWidget(_label(d.MODEL, "modelA"))
    sub = f"{d.VENDOR}  ·  {d.OS_NAME}  ·  Intel {d.CPU_CORES}C/{d.CPU_THREADS}T  ·  {d.RAM_TOTAL}  ·  RTX 2080 Ti"
    left.addWidget(_label(sub, "subtitleA"))
    lay.addLayout(left, 1)

    right = QVBoxLayout()
    right.setSpacing(6)
    status_row = QHBoxLayout()
    status_row.setSpacing(10)
    status = _label("●  采集完成", "statusOkA")
    status.setStyleSheet("color: #2F7D5B; font-weight: 600;")
    status_row.addWidget(status)
    stamp = _label(f"{d.COLLECTED_AT}", "stampA")
    status_row.addWidget(stamp)
    status_row.addStretch()

    refresh = QPushButton(" 刷新")
    refresh.setObjectName("outlineA")
    refresh.setIcon(qicon("refresh", "#16211D", 14))
    refresh.setIconSize(QSize(14, 14))
    refresh.setCursor(Qt.CursorShape.PointingHandCursor)
    status_row.addWidget(refresh)

    export = QPushButton(" 导出")
    export.setObjectName("outlineA")
    export.setIcon(qicon("export", "#16211D", 14))
    export.setIconSize(QSize(14, 14))
    export.setCursor(Qt.CursorShape.PointingHandCursor)
    status_row.addWidget(export)

    right.addLayout(status_row)
    right.addWidget(
        _label(f"上次采集 {d.COLLECTED_AT}  ·  耗时 {d.ELAPSED}  ·  0 错误  0 警告",
               "stampA"),
        alignment=Qt.AlignmentFlag.AlignRight,
    )
    lay.addLayout(right)
    return bar


def _band() -> QWidget:
    band = QWidget()
    band.setObjectName("systemBandA")
    band.setFixedHeight(92)
    lay = QHBoxLayout(band)
    lay.setContentsMargins(24, 12, 24, 12)
    lay.setSpacing(0)

    cells = [
        ("计算", f"{d.CPU_CORES}C / {d.CPU_THREADS}T", f"Genuine Intel · {d.CPU_FREQ}"),
        ("内存", d.RAM_TOTAL, "DDR5-7200 · 2/4 插槽"),
        ("图形", "RTX 2080 Ti", "11 GB · 驱动 32.0.16.1088"),
        ("存储", d.DISK_TOTAL, "2 块 · NVMe + SATA"),
        ("外围", "3 台显示器", "Wi-Fi 6E · 2.5GbE"),
    ]
    for i, (label, value, sub) in enumerate(cells):
        cell = QVBoxLayout()
        cell.setSpacing(2)
        cell.addWidget(_label(label, "bandLabelA"))
        cell.addWidget(_label(value, "bandValueA"))
        cell.addWidget(_label(sub, "bandSubA"))
        lay.addLayout(cell, 1)
        if i < len(cells) - 1:
            lay.addSpacing(18)
            lay.addWidget(vline("#DDE5E0"))
            lay.addSpacing(18)
    return band


def _spec_table() -> QTableWidget:
    table = QTableWidget(len(d.SPEC_ROWS), 4)
    table.setObjectName("specTableA")
    table.setHorizontalHeaderLabels(["类别", "设备 / 型号", "关键规格", "驱动 / 备注"])
    table.verticalHeader().setVisible(False)
    table.verticalHeader().setDefaultSectionSize(42)
    table.setShowGrid(False)
    table.setFrameShape(QFrame.Shape.NoFrame)
    table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
    table.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
    table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
    table.setWordWrap(False)
    table.setFixedHeight(36 + 13 * 42)

    header = table.horizontalHeader()
    header.setFixedHeight(36)
    header.setHighlightSections(False)
    header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
    header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
    header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
    header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
    table.setColumnWidth(0, 84)
    table.setColumnWidth(2, 236)
    table.setColumnWidth(3, 188)
    for c in (0, 1, 2, 3):
        table.horizontalHeaderItem(c).setTextAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
            if c < 3 else Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        )

    for row, (cat, device, spec, extra) in enumerate(d.SPEC_ROWS):
        items = [
            (cat, qfont(SANS, 10, QFont.Weight.DemiBold), "#6C7B75",
             Qt.AlignmentFlag.AlignLeft),
            (device, qfont(SANS, 12, QFont.Weight.Medium), "#16211D",
             Qt.AlignmentFlag.AlignLeft),
            (spec, qfont(MONO, 10), "#3D4A45", Qt.AlignmentFlag.AlignLeft),
            (extra, qfont(MONO, 10), "#6C7B75", Qt.AlignmentFlag.AlignRight),
        ]
        for col, (text, font, color, align) in enumerate(items):
            item = QTableWidgetItem(text)
            item.setFont(font)
            item.setForeground(QColor(color))
            item.setTextAlignment(align | Qt.AlignmentFlag.AlignVCenter)
            table.setItem(row, col, item)
    return table


def _side_panel() -> QWidget:
    panel = QWidget()
    panel.setObjectName("sidePanelA")
    panel.setFixedWidth(276)
    panel.setFixedHeight(36 + 13 * 42)
    lay = QVBoxLayout(panel)
    lay.setContentsMargins(20, 2, 0, 2)
    lay.setSpacing(0)

    lay.addWidget(_label("采集摘要", "sideKickerA"))
    lay.addSpacing(8)
    lay.addWidget(_label("9 / 9", "sideBigA"))
    lay.addSpacing(1)
    lay.addWidget(_label("类别完成", "sideLabelA"))
    lay.addSpacing(14)
    lay.addWidget(hline("#DDE5E0"))
    lay.addSpacing(12)

    rows = [
        ("采集耗时", d.ELAPSED),
        ("错误", "0"),
        ("警告", "0"),
        ("设备条目", "13"),
    ]
    for k, v in rows:
        row = QHBoxLayout()
        row.setSpacing(8)
        row.addWidget(_label(k, "sideLabel2A"))
        row.addStretch()
        row.addWidget(_label(v, "sideValueA"))
        lay.addLayout(row)
        lay.addSpacing(7)

    lay.addSpacing(8)
    lay.addWidget(hline("#DDE5E0"))
    lay.addSpacing(12)
    lay.addWidget(_label("驱动版本", "sideKickerA"))
    lay.addSpacing(8)
    for k, v in [
        ("显卡", d.GPU_DRIVER),
        ("网络", d.WIFI_DRIVER),
        ("音频", d.AUDIO_DRIVER),
    ]:
        row = QHBoxLayout()
        row.setSpacing(8)
        row.addWidget(_label(k, "sideLabel2A"))
        row.addStretch()
        row.addWidget(_label(v, "sideValueA"))
        lay.addLayout(row)
        lay.addSpacing(6)

    lay.addStretch()
    note = _label("以管理员运行可获取更完整的磁盘健康信息", "noteA")
    note.setWordWrap(True)
    lay.addWidget(note)
    lay.addSpacing(10)

    button = QPushButton("导出 JSON")
    button.setObjectName("sideButtonA")
    button.setFixedHeight(32)
    button.setCursor(Qt.CursorShape.PointingHandCursor)
    lay.addWidget(button)
    return panel


def _footer() -> QWidget:
    footer = QWidget()
    footer.setObjectName("footerA")
    footer.setFixedHeight(32)
    lay = QHBoxLayout(footer)
    lay.setContentsMargins(24, 0, 24, 0)
    lay.addWidget(_label("HWINFO  v0.1.0", "footerTextA"))
    lay.addStretch()
    lay.addWidget(_label(
        f"采集完成  ·  {d.COLLECTED_AT}  ·  {d.ELAPSED}  ·  0 错误  0 警告",
        "footerTextA",
    ))
    return footer


class WindowA(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("HWInfo — Bench Sheet")
        self.setStyleSheet(QSS_A)

        root = QWidget()
        root.setObjectName("rootA")
        self.setCentralWidget(root)
        root_lay = QHBoxLayout(root)
        root_lay.setContentsMargins(0, 0, 0, 0)
        root_lay.setSpacing(0)

        root_lay.addWidget(_rail())

        content = QWidget()
        content_lay = QVBoxLayout(content)
        content_lay.setContentsMargins(0, 0, 0, 0)
        content_lay.setSpacing(0)
        content_lay.addWidget(_top_bar())
        content_lay.addWidget(_band())

        main = QWidget()
        main_lay = QVBoxLayout(main)
        main_lay.setContentsMargins(24, 16, 24, 10)
        main_lay.setSpacing(0)

        head = QHBoxLayout()
        head.setSpacing(8)
        head.addWidget(_label("配置概览", "sectionTitleA"))
        head.addStretch()
        head.addWidget(_label("9 类硬件  ·  13 个设备条目", "sectionMetaA"))
        main_lay.addLayout(head)
        main_lay.addSpacing(6)

        body = QHBoxLayout()
        body.setSpacing(0)
        body.addWidget(_spec_table(), 1)
        body.addWidget(_side_panel())
        main_lay.addLayout(body)
        content_lay.addWidget(main, 1)
        content_lay.addWidget(_footer())

        root_lay.addWidget(content, 1)


def build_window() -> QMainWindow:
    return WindowA()


if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    w = build_window()
    w.resize(1440, 900)
    w.show()
    sys.exit(app.exec())
