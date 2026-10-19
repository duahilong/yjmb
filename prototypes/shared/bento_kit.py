"""BENTO 风格共享套件：tokens、QSS、卡片与自绘组件。

总览页、详情页、设置页、状态页都从这里取样式，保证一致的圆角、阴影与配色。
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from PySide6.QtCore import Qt, QRectF                      # noqa: E402
from PySide6.QtGui import QColor, QPainter                 # noqa: E402
from PySide6.QtWidgets import (                            # noqa: E402
    QFrame, QGridLayout, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget,
)

import mock_data as d                                      # noqa: E402
from ui import (                                           # noqa: E402
    DISPLAY, MONO, SANS, hline, icon_pixmap, icon_size, label, qicon, rgba,
    shadow, vline,
)

# ---------------------------------------------------------------- tokens

BG = "#EEF1F4"
CARD = "#FFFFFF"
INK = "#1B2430"
MUTED = "#8A93A0"
FAINT = "#A0A8B4"
LINE = "#E6EAF0"
SOFT = "#EDF0F4"

C_OS = "#0EA5E9"
C_MB = "#5C7CFA"
C_CPU = "#4C6EF5"
C_MEM = "#12B886"
C_GPU = "#F76707"
C_STO = "#7048E8"
C_NET = "#1098AD"
C_DSP = "#E64980"
C_AUD = "#F59F00"
C_ERR = "#E03131"
C_OK = "#12B886"

ACCENTS = {
    "操作系统": C_OS, "主板": C_MB, "处理器": C_CPU, "内存": C_MEM,
    "显卡": C_GPU, "存储": C_STO, "网络": C_NET, "音频": C_AUD, "显示器": C_DSP,
}

BASE_QSS = f"""
QWidget {{ font-family: "{SANS}"; font-size: 13px; color: {INK}; }}
#rootBento {{ background-color: {BG}; }}
#brandBento {{ font-family: "{DISPLAY}"; font-size: 20px; font-weight: 700; color: {INK}; }}
#hostBento {{ font-family: "{MONO}"; font-size: 10px; color: {MUTED}; }}
#timeBento {{ font-family: "{MONO}"; font-size: 10px; color: {FAINT}; }}
QPushButton#bentoBtn {{
    background-color: {CARD}; border: none; border-radius: 999px;
    padding: 8px 16px; color: {INK}; font-size: 12px;
}}
QPushButton#bentoBtn:hover {{ background-color: #F7F9FC; }}
QPushButton#bentoGhost {{
    background-color: transparent; border: 1px solid #DDE3EA; border-radius: 999px;
    padding: 7px 16px; color: {INK}; font-size: 12px;
}}
QPushButton#bentoGhost:hover {{ background-color: {CARD}; }}
QPushButton#bentoPrimary {{
    background-color: {C_CPU}; border: none; border-radius: 999px;
    padding: 8px 18px; color: #FFFFFF; font-size: 12px; font-weight: 600;
}}
QPushButton#bentoPrimary:hover {{ background-color: #3B5BDB; }}
QPushButton#bentoLink {{
    background: transparent; border: none; color: {C_CPU}; font-size: 12px; padding: 0;
}}
#cardBento {{ background-color: {CARD}; border-radius: 20px; }}
#identityBento {{
    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 {CARD}, stop:1 #F1F5FF);
    border-radius: 20px;
}}
#cardTitleBento {{ font-size: 12px; color: {MUTED}; }}
#cardValueBento {{ font-family: "{DISPLAY}"; font-size: 27px; font-weight: 700; color: {INK}; }}
#cardSubBento {{ font-size: 11px; color: {MUTED}; }}
#miniLabelBento {{ font-size: 10px; color: {FAINT}; }}
#miniValueBento {{ font-family: "{DISPLAY}"; font-size: 19px; font-weight: 600; color: {INK}; }}
#idKickerBento {{ font-family: "{MONO}"; font-size: 10px; color: {FAINT}; }}
#idModelBento {{ font-family: "{DISPLAY}"; font-size: 38px; font-weight: 700; color: {INK}; }}
#idSubBento {{ font-size: 12px; color: {MUTED}; }}
#rowNameBento {{ font-size: 12px; color: {INK}; font-weight: 600; }}
#rowSubBento {{ font-family: "{MONO}"; font-size: 10px; color: {MUTED}; }}
#pageTitleBento {{ font-family: "{DISPLAY}"; font-size: 30px; font-weight: 700; color: {INK}; }}
#pageMetaBento {{ font-size: 12px; color: {MUTED}; }}
#sectionBento {{ font-size: 14px; font-weight: 700; color: {INK}; }}
#sectionMetaBento {{ font-family: "{MONO}"; font-size: 10px; color: {FAINT}; }}
#specKeyBento {{ font-size: 11px; color: {MUTED}; }}
#specValueBento {{ font-family: "{MONO}"; font-size: 11px; color: {INK}; }}
#segLight {{ background-color: {SOFT}; border-radius: 999px; }}
QPushButton#segLightItem {{
    background-color: transparent; border: none; border-radius: 999px;
    padding: 7px 15px; color: {MUTED}; font-size: 12px;
}}
QPushButton#segLightItem:hover {{ color: {INK}; }}
QPushButton#segLightActive {{
    background-color: {CARD}; border: none; border-radius: 999px;
    padding: 7px 15px; color: {INK}; font-size: 12px; font-weight: 600;
}}
#stateTitleBento {{ font-size: 14px; font-weight: 700; color: {INK}; }}
#stateBodyBento {{ font-size: 12px; color: {MUTED}; }}
#actionBarBento {{ background-color: {CARD}; border-radius: 18px; }}
#hintBento {{ font-family: "{MONO}"; font-size: 10px; color: {FAINT}; }}
#dotBento {{ font-family: "{MONO}"; font-size: 10px; color: {MUTED}; }}
"""


# ---------------------------------------------------------------- builders

def pill(text: str, accent: str) -> QLabel:
    lb = QLabel(text)
    lb.setStyleSheet(
        f"background-color: {rgba(accent, 0.12)}; color: {accent};"
        f"border-radius: 999px; padding: 3px 10px; font-size: 10px;"
        f"font-family: '{MONO}';"
    )
    return lb


def chip(accent: str, icon: str, size: int = 40, radius: int = 13, icon_px: int = 20) -> QLabel:
    lb = QLabel()
    lb.setFixedSize(size, size)
    lb.setAlignment(Qt.AlignmentFlag.AlignCenter)
    lb.setPixmap(icon_pixmap(icon, accent, icon_px))
    lb.setStyleSheet(f"background-color: {rgba(accent, 0.14)}; border-radius: {radius}px;")
    return lb


def card(title: str, accent: str, icon: str, tag: str | None = None,
         body_spacing: int = 6, stretch: bool = True) -> tuple[QFrame, QVBoxLayout]:
    frame = QFrame()
    frame.setObjectName("cardBento")
    frame.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
    shadow(frame, "#A9B4C4", blur=26, dy=8, alpha=60)

    lay = QVBoxLayout(frame)
    lay.setContentsMargins(20, 18, 20, 18)
    lay.setSpacing(0)

    head = QHBoxLayout()
    head.setSpacing(10)
    head.addWidget(chip(accent, icon))
    head.addWidget(label(title, "cardTitleBento"))
    head.addStretch()
    if tag:
        head.addWidget(pill(tag, accent))
    lay.addLayout(head)
    lay.addSpacing(14)

    body = QVBoxLayout()
    body.setSpacing(body_spacing)
    lay.addLayout(body)
    if stretch:
        lay.addStretch()
    return frame, body


def mini_stat(value: str, key: str) -> QVBoxLayout:
    box = QVBoxLayout()
    box.setSpacing(1)
    box.addWidget(label(key, "miniLabelBento"))
    box.addWidget(label(value, "miniValueBento"))
    return box


def kv_row(key: str, value: str, value_color: str | None = None) -> QWidget:
    row = QWidget()
    lay = QVBoxLayout(row)
    lay.setContentsMargins(0, 0, 0, 0)
    lay.setSpacing(5)
    line = QHBoxLayout()
    line.setSpacing(8)
    line.addWidget(label(key, "miniLabelBento"))
    line.addStretch()
    val = label(value, "rowSubBento")
    if value_color:
        val.setStyleSheet(f"color: {value_color};")
    line.addWidget(val)
    lay.addLayout(line)
    lay.addWidget(hline(LINE))
    return row


def definition_grid(rows: list[tuple[str, str]], columns: int = 2) -> QWidget:
    box = QWidget()
    grid = QGridLayout(box)
    grid.setContentsMargins(0, 0, 0, 0)
    grid.setHorizontalSpacing(36)
    grid.setVerticalSpacing(12)
    per_col = (len(rows) + columns - 1) // columns
    for i, (k, v) in enumerate(rows):
        col, row = divmod(i, per_col)
        cell = QWidget()
        lay = QHBoxLayout(cell)
        lay.setContentsMargins(0, 0, 0, 6)
        lay.setSpacing(8)
        lay.addWidget(label(k, "specKeyBento"))
        lay.addStretch()
        lay.addWidget(label(v, "specValueBento"))
        grid.addWidget(cell, row, col)
    return box


def action_button(text: str, icon: str | None = None, primary: bool = False,
                  ghost: bool = False) -> QPushButton:
    btn = QPushButton(f" {text}" if icon else text)
    btn.setObjectName("bentoPrimary" if primary else ("bentoGhost" if ghost else "bentoBtn"))
    if icon:
        color = "#FFFFFF" if primary else INK
        btn.setIcon(qicon(icon, color, 14))
        btn.setIconSize(icon_size(14))
    btn.setCursor(Qt.CursorShape.PointingHandCursor)
    return btn


def build_top_bar(host_text: str, right_text: str, actions: bool = True) -> QWidget:
    bar = QWidget()
    lay = QHBoxLayout(bar)
    lay.setContentsMargins(0, 0, 0, 0)
    lay.setSpacing(12)
    lay.addWidget(label("HWINFO", "brandBento"))
    lay.addWidget(label(host_text, "hostBento"))
    lay.addStretch()
    lay.addWidget(label(right_text, "timeBento"))
    if actions:
        lay.addWidget(action_button("刷新", "refresh"))
        lay.addWidget(action_button("导出", "export"))
    return bar


def segmented(options: list[str], active: int = 0) -> QFrame:
    bar = QFrame()
    bar.setObjectName("segLight")
    lay = QHBoxLayout(bar)
    lay.setContentsMargins(4, 4, 4, 4)
    lay.setSpacing(2)
    for i, name in enumerate(options):
        btn = QPushButton(name)
        btn.setObjectName("segLightActive" if i == active else "segLightItem")
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        lay.addWidget(btn)
    return bar


# ---------------------------------------------------------------- 自绘组件

class Switch(QWidget):
    """设置页开关。"""

    def __init__(self, on: bool = True, accent: str = C_CPU, parent=None):
        super().__init__(parent)
        self._on = on
        self._accent = QColor(accent)
        self._track_off = QColor("#D7DCE3")
        self.setFixedSize(40, 22)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def mousePressEvent(self, event):
        self._on = not self._on
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(self._accent if self._on else self._track_off)
        p.drawRoundedRect(QRectF(0, 0, self.width(), self.height()), 11, 11)
        p.setBrush(QColor("#FFFFFF"))
        knob = 16
        x = self.width() - knob - 3 if self._on else 3
        p.drawEllipse(QRectF(x, 3, knob, knob))
        p.end()


class Skeleton(QWidget):
    """加载占位条。"""

    def __init__(self, bars: list[tuple[float, int]], color: str = "#E9EDF2",
                 radius: int = 6, gap: int = 10, parent=None):
        super().__init__(parent)
        self._bars = bars
        self._color = QColor(color)
        self._radius = radius
        self.setFixedHeight(sum(h for _, h in bars) + gap * (len(bars) - 1))

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(self._color)
        y = 0
        for frac, height in self._bars:
            p.drawRoundedRect(QRectF(0, y, self.width() * frac, height), self._radius, self._radius)
            y += height + 10
        p.end()


class StateBadge(QWidget):
    """圆形图标底：用于空 / 失败状态。"""

    def __init__(self, icon: str, accent: str, size: int = 64, parent=None):
        super().__init__(parent)
        self._icon = icon
        self._accent = accent
        self.setFixedSize(size, size)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setPen(Qt.PenStyle.NoPen)
        bg = QColor(self._accent)
        bg.setAlphaF(0.12)
        p.setBrush(bg)
        p.drawEllipse(QRectF(0, 0, self.width(), self.height()))
        pm = icon_pixmap(self._icon, self._accent, int(self.width() * 0.42))
        p.drawPixmap(int(self.width() * 0.29), int(self.height() * 0.29), pm)
        p.end()
