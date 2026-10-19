"""原型共用的小工具：字体、线性图标、分隔线。"""
from PySide6.QtCore import QByteArray, QSize, Qt
from PySide6.QtGui import QFont, QIcon, QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import QFrame, QLabel

SANS = "Microsoft YaHei UI"
DISPLAY = "Bahnschrift"
MONO = "Cascadia Mono"


def qfont(family: str = SANS, size: int = 13, weight: int = QFont.Weight.Normal) -> QFont:
    f = QFont(family)
    f.setPixelSize(size)
    f.setWeight(weight)
    return f


def label(text: str = "", name: str = "", family: str | None = None,
          size: int | None = None, weight: int | None = None,
          color: str | None = None) -> QLabel:
    w = QLabel(text)
    if name:
        w.setObjectName(name)
    if family or size or weight:
        f = qfont(family or SANS, size or 13, weight or QFont.Weight.Normal)
        w.setFont(f)
    if color:
        w.setStyleSheet(f"color: {color};")
    return w


def hline(color: str, height: int = 1) -> QFrame:
    line = QFrame()
    line.setFixedHeight(height)
    line.setStyleSheet(f"background-color: {color}; border: none;")
    return line


def vline(color: str, width: int = 1) -> QFrame:
    line = QFrame()
    line.setFixedWidth(width)
    line.setStyleSheet(f"background-color: {color}; border: none;")
    return line


# 24x24 线性图标。只保留描边，颜色由调用方注入。
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
    "audio": '<path d="M4 9v6h4l5 4V5L8 9H4z"/><path d="M16 8c1.3 1.3 1.3 6.7 0 8M19 5c2.5 2.5 2.5 11.5 0 14"/>',
    "monitor": '<rect x="2" y="4" width="20" height="13" rx="1"/><path d="M8 21h8M12 17v4"/>',
    "settings": '<path d="M4 7h10M18 7h2M4 17h2M10 17h10"/><circle cx="16" cy="7" r="2"/>'
                '<circle cx="8" cy="17" r="2"/>',
    "refresh": '<path d="M21 12a9 9 0 1 1-2.6-6.4M21 3v6h-6"/>',
    "export": '<path d="M12 3v12M7 8l5-5 5 5M4 15v4h16v-4"/>',
    "search": '<circle cx="11" cy="11" r="7"/><path d="M16.5 16.5L21 21"/>',
}


def icon_pixmap(name: str, color: str, size: int = 18) -> QPixmap:
    body = _ICONS[name]
    svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" '
        f'stroke="{color}" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">'
        f"{body}</svg>"
    )
    renderer = QSvgRenderer(QByteArray(svg.encode("utf-8")))
    pm = QPixmap(size * 2, size * 2)
    pm.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pm)
    renderer.render(painter)
    painter.end()
    pm.setDevicePixelRatio(2)
    return pm


def qicon(name: str, color: str, size: int = 18) -> QIcon:
    return QIcon(icon_pixmap(name, color, size))


def nav_icon_size(size: int = 18) -> QSize:
    return QSize(size, size)
