"""5 套风格原型共用的字体、图标、颜色与自绘组件。"""
from PySide6.QtCore import QByteArray, QPointF, QRectF, QSize, Qt
from PySide6.QtGui import (
    QBrush, QColor, QFont, QFontMetricsF, QIcon, QLinearGradient, QPainter,
    QPainterPath, QPen, QPixmap,
)
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import QFrame, QGraphicsDropShadowEffect, QLabel, QWidget

SANS = "Microsoft YaHei UI"
DISPLAY = "Bahnschrift"
SERIF = "Georgia"
MONO = "Cascadia Mono"

W_NORMAL = QFont.Weight.Normal
W_MEDIUM = QFont.Weight.Medium
W_DEMI = QFont.Weight.DemiBold
W_BOLD = QFont.Weight.Bold


# ---------------------------------------------------------------- 基础工具

def qfont(family: str = SANS, size: int = 13, weight=W_NORMAL) -> QFont:
    f = QFont(family)
    f.setPixelSize(size)
    f.setWeight(weight)
    return f


def label(text: str = "", name: str = "", family: str | None = None,
          size: int | None = None, weight=None, color: str | None = None) -> QLabel:
    w = QLabel(text)
    if name:
        w.setObjectName(name)
    if family or size or weight:
        w.setFont(qfont(family or SANS, size or 13, weight or W_NORMAL))
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


def rgba(hex_color: str, alpha: float) -> str:
    c = QColor(hex_color)
    return f"rgba({c.red()}, {c.green()}, {c.blue()}, {alpha:.3f})"


def qc(color, alpha: float = 1.0) -> QColor:
    """返回 QColor，可带 alpha；用于自绘组件的半透明颜色。"""
    c = QColor(color) if isinstance(color, str) else QColor(color)
    if alpha < 1.0:
        c.setAlphaF(alpha)
    return c


def shadow(widget: QWidget, color: str = "#000000", blur: int = 28,
           dx: int = 0, dy: int = 8, alpha: int = 70) -> None:
    effect = QGraphicsDropShadowEffect(widget)
    effect.setBlurRadius(blur)
    effect.setOffset(dx, dy)
    c = QColor(color)
    c.setAlpha(alpha)
    effect.setColor(c)
    widget.setGraphicsEffect(effect)


# ---------------------------------------------------------------- 线性图标

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
    "display": '<rect x="2" y="5" width="15" height="11" rx="1"/><rect x="18" y="9" width="4" height="10" rx="1"/>'
               '<path d="M6 20h7"/>',
    "settings": '<path d="M4 7h10M18 7h2M4 17h2M10 17h10"/><circle cx="16" cy="7" r="2"/>'
                '<circle cx="8" cy="17" r="2"/>',
    "refresh": '<path d="M21 12a9 9 0 1 1-2.6-6.4M21 3v6h-6"/>',
    "export": '<path d="M12 3v12M7 8l5-5 5 5M4 15v4h16v-4"/>',
    "search": '<circle cx="11" cy="11" r="7"/><path d="M16.5 16.5L21 21"/>',
    "check": '<path d="M4 12.5l5 5L20 6.5"/>',
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
    "fan": '<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="2"/>'
           '<path d="M12 10c0-4 2-7 4-7s1 6-2 8M14 12c4 0 7 2 7 4s-6 1-8-2M10 12c0 4-2 7-4 7s-1-6 2-8M10 12c-4 0-7-2-7-4s6-1 8 2"/>',
    "usb": '<path d="M12 3v13"/><path d="M12 16a2 2 0 1 0 0 4 2 2 0 0 0 0-4z"/>'
           '<path d="M12 8l3-2M12 11l-3-2"/>',
    "thermometer": '<path d="M10 14V5a2 2 0 1 1 4 0v9a4 4 0 1 1-4 0z"/>',
    "power": '<path d="M12 3v9"/><path d="M6.5 6.5a8 8 0 1 0 11 0"/>',
}


def icon_pixmap(name: str, color: str, size: int = 18, width: float = 1.6) -> QPixmap:
    svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" '
        f'stroke="{color}" stroke-width="{width}" stroke-linecap="round" stroke-linejoin="round">'
        f"{_ICONS[name]}</svg>"
    )
    renderer = QSvgRenderer(QByteArray(svg.encode("utf-8")))
    pm = QPixmap(size * 2, size * 2)
    pm.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pm)
    renderer.render(painter)
    painter.end()
    pm.setDevicePixelRatio(2)
    return pm


def qicon(name: str, color: str, size: int = 18, width: float = 1.6) -> QIcon:
    return QIcon(icon_pixmap(name, color, size, width))


def icon_size(size: int = 18) -> QSize:
    return QSize(size, size)


# ---------------------------------------------------------------- 自绘组件

class MeterBar(QWidget):
    """圆角进度条，可单色或线性渐变。"""

    def __init__(self, value: float = 0.5, fill="#4C6EF5", track="#E6E9EF",
                 height: int = 8, radius: float = 4, gradient: tuple | None = None,
                 parent=None):
        super().__init__(parent)
        self._value = max(0.0, min(1.0, value))
        self._fill = QColor(fill)
        self._track = QColor(track)
        self._radius = radius
        self._gradient = gradient
        self.setFixedHeight(height)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        r = self._radius
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(self._track)
        p.drawRoundedRect(QRectF(0, 0, w, h), r, r)
        fill_w = w * self._value
        if fill_w <= 0:
            return
        if self._gradient:
            grad = QLinearGradient(0, 0, w, 0)
            grad.setColorAt(0, QColor(self._gradient[0]))
            grad.setColorAt(1, QColor(self._gradient[1]))
            p.setBrush(QBrush(grad))
        else:
            p.setBrush(self._fill)
        p.drawRoundedRect(QRectF(0, 0, max(fill_w, h), h), r, r)


class Donut(QWidget):
    """圆环进度，中心可带大号数字与副标题。"""

    def __init__(self, value: float, color: str, track: str, size: int = 132,
                 thickness: int = 10, center: str = "", sub: str = "",
                 center_family: str = DISPLAY, parent=None):
        super().__init__(parent)
        self._value = max(0.0, min(1.0, value))
        self._color = QColor(color)
        self._track = QColor(track)
        self._thickness = thickness
        self._center = center
        self._sub = sub
        self._center_family = center_family
        self.setFixedSize(size, size)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        m = self._thickness / 2 + 1
        rect = QRectF(m, m, self.width() - 2 * m, self.height() - 2 * m)

        pen = QPen(self._track, self._thickness)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        p.setPen(pen)
        p.drawArc(rect, 0, 360 * 16)

        pen = QPen(self._color, self._thickness)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        p.setPen(pen)
        p.drawArc(rect, 90 * 16, -int(360 * 16 * self._value))

        if self._center:
            p.setPen(QColor(self._color))
            p.setFont(qfont(self._center_family, int(self.height() * 0.24), W_BOLD))
            p.drawText(rect, Qt.AlignmentFlag.AlignCenter, self._center)
        if self._sub:
            p.setPen(QColor("#8A8F98"))
            p.setFont(qfont(SANS, 10))
            sub_rect = QRectF(rect.left(), rect.center().y() + self.height() * 0.10,
                              rect.width(), self.height() * 0.24)
            p.drawText(sub_rect, Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop, self._sub)


class SlotRow(QWidget):
    """内存插槽可视化。"""

    def __init__(self, total: int, used: int, color: str = "#12B886",
                 empty: str = "#E3E7EC", width: int = 22, height: int = 8, parent=None):
        super().__init__(parent)
        self._total = total
        self._used = used
        self._color = QColor(color)
        self._empty = QColor(empty)
        self.setFixedHeight(height)
        self.setMinimumWidth(total * (width + 6))

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        h = self.height()
        gap = 6
        w = (self.width() - gap * (self._total - 1)) / self._total
        p.setPen(Qt.PenStyle.NoPen)
        for i in range(self._total):
            p.setBrush(self._color if i < self._used else self._empty)
            p.drawRoundedRect(QRectF(i * (w + gap), 0, w, h), h / 2, h / 2)


class CoreGrid(QWidget):
    """24 个小格表示核心数。"""

    def __init__(self, count: int, color: str, empty: str, cols: int = 12,
                 cell: int = 10, gap: int = 4, parent=None):
        super().__init__(parent)
        self._count = count
        self._color = QColor(color)
        self._empty = QColor(empty)
        self._cols = cols
        self._cell = cell
        self._gap = gap
        rows = (count + cols - 1) // cols
        self.setFixedSize(cols * cell + (cols - 1) * gap, rows * cell + (rows - 1) * gap)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setPen(Qt.PenStyle.NoPen)
        for i in range(self._count):
            r, c = divmod(i, self._cols)
            x = c * (self._cell + self._gap)
            y = r * (self._cell + self._gap)
            p.setBrush(self._color)
            p.drawRoundedRect(QRectF(x, y, self._cell, self._cell), 2, 2)


class Barcode(QWidget):
    """伪条形码，用于打印风格。"""

    def __init__(self, seed: str, color: str = "#202020", height: int = 44, parent=None):
        super().__init__(parent)
        self._seed = seed
        self._color = QColor(color)
        self.setFixedHeight(height)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(self._color)
        x = 0
        i = 0
        h = self.height()
        while x < self.width() - 2:
            code = ord(self._seed[i % len(self._seed)]) + i * 7
            bar = 1 + (code % 3)
            gap = 1 + (code % 4)
            p.drawRect(QRectF(x, 0, bar, h))
            x += bar + gap
            i += 1


class DotLeaderRow(QWidget):
    """标签 …… 值，点线引导。"""

    def __init__(self, key: str, value: str, key_color: str = "#6B6558",
                 value_color: str = "#202020", dot_color: str = "#BEB6A4",
                 size: int = 12, bold_value: bool = True, height: int = 24, parent=None):
        super().__init__(parent)
        self._key = key
        self._value = value
        self._key_color = QColor(key_color)
        self._value_color = QColor(value_color)
        self._dot_color = QColor(dot_color)
        self._font = qfont(MONO, size)
        self._value_font = qfont(MONO, size, W_DEMI if bold_value else W_NORMAL)
        self.setFixedHeight(height)

    def paintEvent(self, event):
        p = QPainter(self)
        fm = QFontMetricsF(self._font)
        fmv = QFontMetricsF(self._value_font)
        y = (self.height() - fm.height()) / 2 + fm.ascent()
        p.setFont(self._font)
        p.setPen(self._key_color)
        p.drawText(QPointF(0, y), self._key)
        kw = fm.horizontalAdvance(self._key)

        p.setFont(self._value_font)
        vw = fmv.horizontalAdvance(self._value)
        p.setPen(self._value_color)
        p.drawText(QPointF(self.width() - vw, y), self._value)

        start = kw + 6
        end = self.width() - vw - 6
        if end > start:
            p.setPen(QPen(self._dot_color, 1, Qt.PenStyle.DotLine))
            p.drawLine(QPointF(start, self.height() / 2), QPointF(end, self.height() / 2))


class Stamp(QWidget):
    """旋转的印章 / 状态戳。"""

    def __init__(self, text: str, color: str, angle: float = -8, size: int = 15,
                 width: int = 170, height: int = 44, parent=None):
        super().__init__(parent)
        self._text = text
        self._color = QColor(color)
        self._angle = angle
        self._size = size
        self.setFixedSize(width, height)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.translate(self.width() / 2, self.height() / 2)
        p.rotate(self._angle)
        rect = QRectF(-self.width() / 2 + 3, -self.height() / 2 + 3,
                      self.width() - 6, self.height() - 6)
        pen = QPen(self._color, 2)
        p.setPen(pen)
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawRoundedRect(rect, 4, 4)
        p.setPen(self._color)
        p.setFont(qfont(MONO, self._size, W_BOLD))
        p.drawText(rect, Qt.AlignmentFlag.AlignCenter, self._text)


class GradientText(QWidget):
    """渐变填充的文本，用于深色高端风格的主标题。"""

    def __init__(self, text: str, c1: str, c2: str, size: int = 40,
                 family: str = DISPLAY, weight=W_BOLD, parent=None):
        super().__init__(parent)
        self._text = text
        self._c1 = QColor(c1)
        self._c2 = QColor(c2)
        self._font = qfont(family, size, weight)
        self.setMinimumHeight(int(size * 1.5))

    def sizeHint(self):
        fm = QFontMetricsF(self._font)
        return QSize(int(fm.horizontalAdvance(self._text)) + 4, int(fm.height() * 1.3))

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setFont(self._font)
        grad = QLinearGradient(0, 0, self.width(), 0)
        grad.setColorAt(0, self._c1)
        grad.setColorAt(1, self._c2)
        pen = QPen(QBrush(grad), 1)
        p.setPen(pen)
        fm = QFontMetricsF(self._font)
        p.drawText(QPointF(0, fm.ascent()), self._text)
