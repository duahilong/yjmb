"""
gui/icons.py - 线性图标与绘制工具

界面图标用内嵌 SVG 渲染成 QPixmap，不打包字体；颜色随主题变化。
应用图标从 assets/hwinfo.ico 加载，同时供窗口、任务栏和 EXE 文件使用。
"""
import os
import sys

from PySide6.QtCore import QByteArray, QSize, Qt
from PySide6.QtGui import QColor, QFont, QIcon, QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import QGraphicsDropShadowEffect, QWidget

# 系统字体：不打包字体文件，只用 Windows 自带字体
SANS = "Microsoft YaHei UI"
DISPLAY = "Bahnschrift"
MONO = "Cascadia Mono"

W_NORMAL = QFont.Weight.Normal
W_MEDIUM = QFont.Weight.Medium
W_DEMI = QFont.Weight.DemiBold
W_BOLD = QFont.Weight.Bold

# 24×24 视框的线性图标路径
_ICONS = {
    "overview": '<rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/>'
                '<rect x="3" y="14" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/>',
    "os": '<rect x="3" y="4" width="18" height="16" rx="1"/><path d="M3 8h18"/>',
    "motherboard": '<rect x="4" y="4" width="16" height="16"/><path d="M8 8h8v8H8z"/>'
                   '<path d="M4 8H2M4 16H2M20 8h2M20 16h2M8 4V2M16 4V2M8 20v2M16 20v2"/>',
    "cpu": '<rect x="6" y="6" width="12" height="12"/><rect x="9" y="9" width="6" height="6"/>'
           '<path d="M9 2v4M15 2v4M9 18v4M15 18v4M2 9h4M2 15h4M18 9h4M18 15h4"/>',
    "memory": '<rect x="3" y="7" width="18" height="10" rx="1"/><path d="M7 17v3M12 17v3M17 17v3"/>'
              '<path d="M7 10v4M12 10v4M17 10v4"/>',
    "gpu": '<rect x="2" y="6" width="20" height="12" rx="1"/><circle cx="8" cy="12" r="3"/>'
           '<path d="M14 10h5M14 14h5M6 18v2M18 18v2"/>',
    "storage": '<ellipse cx="12" cy="6" rx="8" ry="3"/><path d="M4 6v12c0 1.7 3.6 3 8 3s8-1.3 8-3V6"/>'
               '<path d="M4 12c0 1.7 3.6 3 8 3s8-1.3 8-3"/>',
    "network": '<rect x="3" y="14" width="7" height="6"/><rect x="14" y="14" width="7" height="6"/>'
               '<rect x="8.5" y="3" width="7" height="6"/><path d="M12 9v5M6.5 14v-3h11v3"/>',
    "wifi": '<path d="M2 8.5a15 15 0 0 1 20 0M5.5 12a10 10 0 0 1 13 0M9 15.5a5 5 0 0 1 6 0"/>'
            '<circle cx="12" cy="19" r="1"/>',
    "ethernet": '<rect x="3" y="10" width="18" height="10" rx="1"/><path d="M7 10V6h3v4M14 10V6h3v4"/>',
    "audio": '<path d="M4 9v6h4l5 4V5L8 9H4z"/><path d="M16 8c1.3 1.3 1.3 6.7 0 8M19 5c2.5 2.5 2.5 11.5 0 14"/>',
    "monitor": '<rect x="2" y="4" width="20" height="13" rx="1"/><path d="M8 21h8M12 17v4"/>',
    "settings": '<path d="M4 7h10M18 7h2M4 17h2M10 17h10"/><circle cx="16" cy="7" r="2"/>'
                '<circle cx="8" cy="17" r="2"/>',
    "refresh": '<path d="M21 12a9 9 0 1 1-2.6-6.4M21 3v6h-6"/>',
    "export": '<path d="M12 3v12M7 8l5-5 5 5M4 15v4h16v-4"/>',
    "search": '<circle cx="11" cy="11" r="7"/><path d="M16.5 16.5L21 21"/>',
    "check": '<path d="M4 12.5l5 5L20 6.5"/>',
    "warning": '<path d="M12 3l9 16H3l9-16z"/><path d="M12 9v5M12 17h.01"/>',
    "bolt": '<path d="M13 2L4 14h6l-1 8 9-12h-6l1-8z"/>',
    "shield": '<path d="M12 3l8 3v6c0 5-3.4 8.2-8 9-4.6-.8-8-4-8-9V6l8-3z"/>',
    "clock": '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
    "layers": '<path d="M12 3l9 5-9 5-9-5 9-5z"/><path d="M3 13l9 5 9-5"/>',
    "chip": '<rect x="5" y="5" width="14" height="14" rx="1"/><rect x="9" y="9" width="6" height="6"/>'
            '<path d="M9 2v3M15 2v3M9 19v3M15 19v3M2 9h3M2 15h3M19 9h3M19 15h3"/>',
    "activity": '<path d="M3 12h4l3 8 4-16 3 8h4"/>',
    "gauge": '<path d="M4 18a8 8 0 1 1 16 0"/><path d="M12 18l4-6"/>',
    "box": '<path d="M3 7l9-4 9 4v10l-9 4-9-4V7z"/><path d="M3 7l9 4 9-4M12 11v10"/>',
    "arrow": '<path d="M5 12h14M13 6l6 6-6 6"/>',
    "plus": '<path d="M12 5v14M5 12h14"/>',
    "minus": '<path d="M5 12h14"/>',
    "close": '<path d="M6 6l12 12M18 6L6 18"/>',
    "fan": '<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="2"/>'
           '<path d="M12 10c0-4 2-7 4-7s1 6-2 8M14 12c4 0 7 2 7 4s-6 1-8-2M10 12c0 4-2 7-4 7s-1-6 2-8M10 12c-4 0-7-2-7-4s6-1 8 2"/>',
    "usb": '<path d="M12 3v13"/><path d="M12 16a2 2 0 1 0 0 4 2 2 0 0 0 0-4z"/>'
           '<path d="M12 8l3-2M12 11l-3-2"/>',
    "thermometer": '<path d="M10 14V5a2 2 0 1 1 4 0v9a4 4 0 1 1-4 0z"/>',
    "power": '<path d="M12 3v9"/><path d="M6.5 6.5a8 8 0 1 0 11 0"/>',
    "info": '<circle cx="12" cy="12" r="9"/><path d="M12 11v5M12 8h.01"/>',
}


def qfont(family: str = SANS, size: int = 13, weight=W_NORMAL) -> QFont:
    """构造按像素指定字号的字体"""
    f = QFont(family)
    f.setPixelSize(max(1, int(size)))
    f.setWeight(weight)
    return f


def icon_pixmap(name: str, color: str, size: int = 18, width: float = 1.6) -> QPixmap:
    """把内嵌 SVG 渲染成带 2 倍图的高分辨率 QPixmap"""
    body = _ICONS.get(name, _ICONS["info"])
    svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" '
        f'stroke="{color}" stroke-width="{width}" stroke-linecap="round" stroke-linejoin="round">'
        f"{body}</svg>"
    )
    renderer = QSvgRenderer(QByteArray(svg.encode("utf-8")))
    pm = QPixmap(size * 2, size * 2)
    pm.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pm)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    renderer.render(painter)
    painter.end()
    pm.setDevicePixelRatio(2)
    return pm


def qicon(name: str, color: str, size: int = 18, width: float = 1.6) -> QIcon:
    return QIcon(icon_pixmap(name, color, size, width))


def app_icon_path() -> str:
    """应用图标路径，兼容源码运行与 PyInstaller 单文件模式。"""
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, "assets", "hwinfo.ico")
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(root, "assets", "hwinfo.ico")


def app_icon() -> QIcon:
    """窗口 / 任务栏使用的多尺寸应用图标；缺失时回退到 CPU 线稿。"""
    path = app_icon_path()
    if os.path.isfile(path):
        return QIcon(path)
    return qicon("cpu", "#4C6EF5", 64)


def icon_size(size: int = 18) -> QSize:
    return QSize(size, size)


def rgba(hex_color: str, alpha: float) -> str:
    """十六进制色 → QSS 可用的 rgba() 字符串"""
    c = QColor(hex_color)
    return f"rgba({c.red()}, {c.green()}, {c.blue()}, {alpha:.3f})"


def qc(color, alpha: float = 1.0) -> QColor:
    """返回 QColor（可带 alpha）。

    注意：QColor 不解析 CSS 的 rgba() 字符串，自绘组件必须走这里，
    否则半透明色会变成黑色。
    """
    c = QColor(color) if isinstance(color, str) else QColor(color)
    if alpha < 1.0:
        c.setAlphaF(alpha)
    return c


def shadow(widget: QWidget, color: str, blur: int, dy: int = 8, alpha: int = 60) -> None:
    """给控件加柔和投影"""
    effect = QGraphicsDropShadowEffect(widget)
    effect.setBlurRadius(blur)
    effect.setOffset(0, dy)
    c = QColor(color)
    c.setAlpha(alpha)
    effect.setColor(c)
    widget.setGraphicsEffect(effect)
