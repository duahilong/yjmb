"""
gui/components.py - 便当格组件库

卡片、胶囊、开关、进度条等全部从这里取，页面只负责组合数据。
所有间距/尺寸走 theme.sp()，因此密度与缩放切换后整页同步变化。
"""
from PySide6.QtCore import QRectF, Qt, Signal
from PySide6.QtGui import QBrush, QColor, QLinearGradient, QPainter, QPen
from PySide6.QtWidgets import (
    QFrame, QGridLayout, QHBoxLayout, QLabel, QPushButton, QScrollArea,
    QVBoxLayout, QWidget,
)

from gui import theme
from gui.icons import icon_pixmap, icon_size, qc, qfont, qicon, rgba, shadow


# ---------------------------------------------------------------- 基础控件

def label(text: str = "", role: str = "", color: str | None = None,
          wrap: bool = False) -> QLabel:
    """文本标签。role 对应 theme 中定义的 QSS 角色（objectName）。"""
    lb = QLabel(text)
    if role:
        lb.setObjectName(role)
    if color:
        lb.setStyleSheet(f"color: {color};")
    if wrap:
        lb.setWordWrap(True)
    return lb


def hline(color: str | None = None, height: int = 1) -> QFrame:
    line = QFrame()
    line.setFixedHeight(max(1, height))
    line.setStyleSheet(f"background-color: {color or theme.P['line']}; border: none;")
    return line


def vline(color: str | None = None, width: int = 1) -> QFrame:
    line = QFrame()
    line.setFixedWidth(max(1, width))
    line.setStyleSheet(f"background-color: {color or theme.P['line']}; border: none;")
    return line


def pill(text: str, accent: str) -> QLabel:
    """小标签：半透明底色 + 强调色文字

    注意：Qt 会忽略「大于控件一半高度」的 border-radius（直接退化成直角），
    所以这里用固定内边距 + 保守圆角，宽度靠 contentsMargins 撑开，
    避免 QSS padding 不参与 sizeHint 导致文字被截断。
    """
    lb = QLabel(text)
    lb.setAlignment(Qt.AlignmentFlag.AlignCenter)
    lb.setContentsMargins(theme.sp(8), theme.sp(2), theme.sp(8), theme.sp(2))
    lb.setMinimumHeight(theme.sp(18))
    lb.setFont(qfont("Microsoft YaHei UI", theme.sp(10)))
    lb.setStyleSheet(
        f"background-color: {rgba(accent, 0.12)}; color: {accent};"
        f"border-radius: {theme.sp(8)}px;"
    )
    return lb


def chip(accent: str, icon: str, size: int | None = None,
         radius: int | None = None, icon_px: int | None = None) -> QLabel:
    """圆角图标块：卡片左上角的彩色小方块"""
    size = size or theme.sp(40)
    radius = radius or theme.sp(13)
    icon_px = icon_px or theme.sp(20)
    lb = QLabel()
    lb.setFixedSize(size, size)
    lb.setAlignment(Qt.AlignmentFlag.AlignCenter)
    lb.setPixmap(icon_pixmap(icon, accent, icon_px))
    lb.setStyleSheet(f"background-color: {rgba(accent, 0.14)}; border-radius: {radius}px;")
    return lb


def mini_stat(value: str, key: str) -> QVBoxLayout:
    """迷你指标：上标签下数值"""
    box = QVBoxLayout()
    box.setSpacing(theme.sp(2))
    box.addWidget(label(key, "miniLabel"))
    box.addWidget(label(value, "miniValue"))
    return box


def kv_row(key: str, value: str, value_color: str | None = None) -> QWidget:
    """键值行：左键右值，底部细分隔线"""
    row = QWidget()
    lay = QVBoxLayout(row)
    lay.setContentsMargins(0, 0, 0, 0)
    lay.setSpacing(theme.sp(6))
    line = QHBoxLayout()
    line.setSpacing(theme.sp(8))
    line.addWidget(label(key, "miniLabel"))
    line.addStretch()
    line.addWidget(label(value, "rowSub", color=value_color))
    lay.addLayout(line)
    lay.addWidget(hline())
    return row


def definition_grid(rows: list[tuple[str, str]], columns: int = 2) -> QWidget:
    """规格明细网格：列优先填充，右键值对齐"""
    box = QWidget()
    grid = QGridLayout(box)
    grid.setContentsMargins(0, 0, 0, 0)
    grid.setHorizontalSpacing(theme.sp(36))
    grid.setVerticalSpacing(theme.sp(12))
    columns = max(1, columns)
    per_col = (len(rows) + columns - 1) // columns
    for i, (k, v) in enumerate(rows):
        col, row = divmod(i, per_col)
        cell = QWidget()
        lay = QHBoxLayout(cell)
        lay.setContentsMargins(0, 0, 0, theme.sp(6))
        lay.setSpacing(theme.sp(8))
        lay.addWidget(label(k, "specKey"))
        lay.addStretch()
        val = ElidedLabel(v, "specValue")
        val.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        lay.addWidget(val)
        grid.addWidget(cell, row, col)
    for col in range(columns):
        grid.setColumnStretch(col, 1)
    return box


def action_button(text: str, icon: str | None = None, kind: str = "default",
                  accent: str | None = None, on_click=None) -> QPushButton:
    """胶囊按钮。kind: default / ghost / primary"""
    btn = QPushButton(f"  {text}" if icon else text)
    obj = {"ghost": "btnGhost", "primary": "btnPrimary"}.get(kind, "btnDefault")
    btn.setObjectName(obj)
    if icon:
        color = "#FFFFFF" if kind == "primary" else theme.P["ink"]
        btn.setIcon(qicon(icon, color, theme.sp(14)))
        btn.setIconSize(icon_size(theme.sp(14)))
    btn.setCursor(Qt.CursorShape.PointingHandCursor)
    if on_click:
        btn.clicked.connect(on_click)
    return btn


def icon_button(icon: str, tooltip: str = "", size: int | None = None, on_click=None) -> QPushButton:
    """圆形小图标按钮（顶栏缩放、刷新用）"""
    size = size or theme.sp(30)
    btn = QPushButton()
    btn.setObjectName("btnIcon")
    btn.setFixedSize(size, size)
    btn.setIcon(qicon(icon, theme.P["muted"], theme.sp(14)))
    btn.setIconSize(icon_size(theme.sp(14)))
    btn.setCursor(Qt.CursorShape.PointingHandCursor)
    if tooltip:
        btn.setToolTip(tooltip)
    if on_click:
        btn.clicked.connect(on_click)
    return btn


class ElidedLabel(QLabel):
    """按可用宽度省略的文本标签（鼠标悬停显示完整内容）"""

    def __init__(self, text: str = "", role: str = "", parent=None):
        super().__init__("", parent)
        self._full = text or ""
        if role:
            self.setObjectName(role)
        super().setText(self._full)

    def full_text(self) -> str:
        return self._full

    def minimumSizeHint(self):  # noqa: N802
        """允许被布局压窄（否则长文本会把列撑爆，见规格明细网格）"""
        from PySide6.QtCore import QSize
        hint = super().minimumSizeHint()
        return QSize(min(hint.width(), theme.sp(56)), hint.height())

    def sizeHint(self):  # noqa: N802
        """留一点余量：省略宽度正好等于文字宽度时会误截断"""
        from PySide6.QtCore import QSize
        hint = super().sizeHint()
        return QSize(hint.width() + theme.sp(6), hint.height())

    def setText(self, text: str) -> None:  # noqa: N802
        self._full = text or ""
        self._elide()

    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)
        self._elide()

    def changeEvent(self, event) -> None:  # noqa: N802
        super().changeEvent(event)
        self._elide()

    def _elide(self) -> None:
        fm = self.fontMetrics()
        width = max(0, self.width() - 1)
        if width <= 0:
            return
        elided = fm.elidedText(self._full, Qt.TextElideMode.ElideRight, width)
        super().setText(elided)
        self.setToolTip(self._full if elided != self._full else "")


# ---------------------------------------------------------------- 卡片

CARD_MARGIN_X = 20
CARD_MARGIN_Y = 15


def card(title: str, accent: str, icon: str, tag: str | None = None,
         stretch: bool = True, body_spacing: int = 6,
         hero: bool = False) -> tuple[QFrame, QVBoxLayout]:
    """便当格卡片。返回 (卡片控件, 内容布局)。

    hero=True 时用淡渐变底色，用于总览页的主卡。
    """
    frame = QFrame()
    frame.setObjectName("heroCard" if hero else "card")
    frame.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
    color, blur, dy = theme.shadow_params()
    shadow(frame, color, blur, dy, theme.P["shadow_alpha"])
    frame.accent = accent          # 供标签等后续使用

    lay = QVBoxLayout(frame)
    lay.setContentsMargins(theme.sp(CARD_MARGIN_X), theme.sp(CARD_MARGIN_Y),
                           theme.sp(CARD_MARGIN_X), theme.sp(CARD_MARGIN_Y))
    lay.setSpacing(0)

    head = QHBoxLayout()
    head.setSpacing(theme.sp(10))
    head.addWidget(chip(accent, icon))
    head.addWidget(label(title, "cardTitle"))
    head.addStretch()
    tag_label = pill(tag, accent) if tag else None
    if tag_label:
        head.addWidget(tag_label)
        tag_label.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
    lay.addLayout(head)
    lay.addSpacing(theme.sp(12))

    body = QVBoxLayout()
    body.setSpacing(body_spacing)
    lay.addLayout(body)
    if stretch:
        lay.addStretch()

    frame.body = body
    frame.tag_label = tag_label
    return frame, body


def set_tag(frame: QFrame, text: str, accent: str | None = None) -> None:
    """更新卡片的右上角标签"""
    lb = getattr(frame, "tag_label", None)
    if lb is None:
        return
    lb.setText(text)


def state_card(icon: str, accent: str, title: str, body_text: str,
               status: str = "", buttons: list[QPushButton] | None = None,
               button_row: bool = True) -> QFrame:
    """空态 / 失败态卡片：居中图标 + 标题 + 说明 + 可选操作"""
    frame, body = card(title, accent, icon, status or None, stretch=False)
    body.addStretch()
    body.addWidget(StateBadge(icon, accent, theme.sp(64)),
                   alignment=Qt.AlignmentFlag.AlignHCenter)
    body.addSpacing(theme.sp(14))
    body.addWidget(label(body_text, "stateBody", wrap=True),
                   alignment=Qt.AlignmentFlag.AlignHCenter)
    if buttons:
        body.addSpacing(theme.sp(16))
        row = QHBoxLayout()
        row.addStretch()
        for btn in buttons:
            row.addWidget(btn)
        row.addStretch()
        if button_row:
            body.addLayout(row)
    body.addStretch()
    return frame


# ---------------------------------------------------------------- 分段控件

class Segmented(QWidget):
    """分段控件：一组选项，选中项为白色胶囊"""

    changed = Signal(int)

    def __init__(self, options: list[str], active: int = 0, on_change=None, parent=None):
        super().__init__(parent)
        self._options = list(options)
        self._active = active
        self._buttons: list[QPushButton] = []

        track = QFrame(self)
        track.setObjectName("segTrack")
        track.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(track)
        inner = QHBoxLayout(track)
        inner.setContentsMargins(theme.sp(4), theme.sp(4), theme.sp(4), theme.sp(4))
        inner.setSpacing(theme.sp(2))
        for i, name in enumerate(self._options):
            btn = QPushButton(name)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda _=False, idx=i: self.set_active(idx, emit=True))
            self._buttons.append(btn)
            inner.addWidget(btn)
        if on_change:
            self.changed.connect(on_change)
        self._apply()

    def _apply(self) -> None:
        for i, btn in enumerate(self._buttons):
            btn.setObjectName("segActive" if i == self._active else "segItem")
            btn.style().unpolish(btn)
            btn.style().polish(btn)

    def set_active(self, index: int, emit: bool = False) -> None:
        if not 0 <= index < len(self._buttons):
            return
        self._active = index
        self._apply()
        if emit:
            self.changed.emit(index)

    def current(self) -> int:
        return self._active

    def current_text(self) -> str:
        return self._options[self._active]


# ---------------------------------------------------------------- 自绘控件

class Switch(QWidget):
    """开关。toggled(bool) 在用户点击后发出。"""

    toggled = Signal(bool)

    def __init__(self, on: bool = True, accent: str | None = None, on_change=None, parent=None):
        super().__init__(parent)
        self._on = on
        self._accent = QColor(accent or theme.accent("cpu"))
        self.setFixedSize(theme.sp(40), theme.sp(22))
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        if on_change:
            self.toggled.connect(on_change)

    def is_on(self) -> bool:
        return self._on

    def set_on(self, on: bool, emit: bool = False) -> None:
        if self._on == on:
            return
        self._on = on
        self.update()
        if emit:
            self.toggled.emit(on)

    def set_accent(self, accent: str) -> None:
        self._accent = QColor(accent)
        self.update()

    def mousePressEvent(self, event) -> None:  # noqa: N802
        if event.button() == Qt.MouseButton.LeftButton:
            self._on = not self._on
            self.update()
            self.toggled.emit(self._on)

    def paintEvent(self, event) -> None:  # noqa: N802
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setPen(Qt.PenStyle.NoPen)
        track_off = qc(theme.P["line"])
        p.setBrush(self._accent if self._on else track_off)
        radius = self.height() / 2
        p.drawRoundedRect(QRectF(0, 0, self.width(), self.height()), radius, radius)
        p.setBrush(qc(theme.P["card"]))
        knob = self.height() - theme.sp(6)
        x = self.width() - knob - theme.sp(3) if self._on else theme.sp(3)
        p.drawEllipse(QRectF(x, theme.sp(3), knob, knob))
        p.end()


class Skeleton(QWidget):
    """加载占位条：按 (宽度比例, 高度) 列表绘制"""

    def __init__(self, bars: list[tuple[float, int]], parent=None):
        super().__init__(parent)
        self._bars = bars
        self._color = qc(theme.P["soft"])
        self._radius = theme.sp(6)
        self._gap = theme.sp(10)
        self.setFixedHeight(sum(theme.sp(h) for _, h in bars) + self._gap * (len(bars) - 1))

    def paintEvent(self, event) -> None:  # noqa: N802
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(self._color)
        y = 0
        for frac, height in self._bars:
            h = theme.sp(height)
            p.drawRoundedRect(QRectF(0, y, self.width() * frac, h), self._radius, self._radius)
            y += h + self._gap
        p.end()


class StateBadge(QWidget):
    """圆形图标底：空态 / 失败态用"""

    def __init__(self, icon: str, accent: str, size: int | None = None, parent=None):
        super().__init__(parent)
        self._icon = icon
        self._accent = accent
        size = size or theme.sp(64)
        self.setFixedSize(size, size)

    def paintEvent(self, event) -> None:  # noqa: N802
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(qc(self._accent, 0.12))
        p.drawEllipse(QRectF(0, 0, self.width(), self.height()))
        inner = int(self.width() * 0.42)
        pm = icon_pixmap(self._icon, self._accent, inner)
        off = int(self.width() * 0.29)
        p.drawPixmap(off, off, pm)
        p.end()


class MeterBar(QWidget):
    """圆角进度条：单色或线性渐变"""

    def __init__(self, value: float = 0.5, fill: str | None = None, track: str | None = None,
                 height: int | None = None, gradient: tuple[str, str] | None = None, parent=None):
        super().__init__(parent)
        self._value = max(0.0, min(1.0, value))
        self._fill = QColor(fill or theme.accent("cpu"))
        self._track = QColor(track or theme.P["soft"])
        self._radius = (theme.sp(height or 8)) / 2
        self._gradient = gradient
        self.setFixedHeight(theme.sp(height or 8))

    def paintEvent(self, event) -> None:  # noqa: N802
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h, r = self.width(), self.height(), self._radius
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(self._track)
        p.drawRoundedRect(QRectF(0, 0, w, h), r, r)
        fill_w = w * self._value
        if fill_w <= 0:
            p.end()
            return
        if self._gradient:
            grad = QLinearGradient(0, 0, w, 0)
            grad.setColorAt(0, QColor(self._gradient[0]))
            grad.setColorAt(1, QColor(self._gradient[1]))
            p.setBrush(QBrush(grad))
        else:
            p.setBrush(self._fill)
        p.drawRoundedRect(QRectF(0, 0, max(fill_w, h), h), r, r)
        p.end()


class SlotRow(QWidget):
    """内存插槽可视化：已用实心、空闲浅色

    每个插槽固定宽度，避免在宽卡片里被拉成进度条。
    """

    def __init__(self, total: int, used: int, color: str | None = None,
                 slot_width: int | None = None, parent=None):
        super().__init__(parent)
        self._total = max(1, total)
        self._used = max(0, min(used, total))
        self._color = QColor(color or theme.accent("memory"))
        self._empty = qc(theme.P["line"])
        self._h = theme.sp(9)
        self._gap = theme.sp(6)
        self._slot = slot_width or theme.sp(46)
        self.setFixedSize(self._total * self._slot + (self._total - 1) * self._gap,
                          self._h)

    def paintEvent(self, event) -> None:  # noqa: N802
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        h = self._h
        gap = self._gap
        w = self._slot
        p.setPen(Qt.PenStyle.NoPen)
        for i in range(self._total):
            p.setBrush(self._color if i < self._used else self._empty)
            p.drawRoundedRect(QRectF(i * (w + gap), 0, w, h), h / 2, h / 2)
        p.end()


class CoreGrid(QWidget):
    """核心格：每格代表一个逻辑核心"""

    def __init__(self, count: int, color: str | None = None, cols: int = 12,
                 cell: int | None = None, gap: int | None = None, parent=None):
        super().__init__(parent)
        self._count = max(0, count)
        self._color = QColor(color or theme.accent("cpu"))
        self._cols = max(1, cols)
        self._cell = cell or theme.sp(16)
        self._gap = gap or theme.sp(8)
        rows = max(1, (count + self._cols - 1) // self._cols)
        self.setFixedSize(
            self._cols * self._cell + (self._cols - 1) * self._gap,
            rows * self._cell + (rows - 1) * self._gap,
        )

    def paintEvent(self, event) -> None:  # noqa: N802
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(self._color)
        for i in range(self._count):
            r, c = divmod(i, self._cols)
            x = c * (self._cell + self._gap)
            y = r * (self._cell + self._gap)
            p.drawRoundedRect(QRectF(x, y, self._cell, self._cell), theme.sp(2), theme.sp(2))
        p.end()


class BarList(QWidget):
    """一组横向占比条：[(标签, 比例, 说明, 颜色)]"""

    def __init__(self, rows: list[tuple[str, float, str, str]],
                 height: int | None = None, parent=None):
        super().__init__(parent)
        self._rows = rows
        self._row_h = theme.sp(30)
        self._gap = theme.sp(12)
        self._track = qc(theme.P["soft"])
        self._font = qfont("Cascadia Mono", theme.sp(10))
        self._font_bold = qfont("Cascadia Mono", theme.sp(10), weight=qfont("").weight())
        self._ink = qc(theme.P["ink"])
        self._muted = qc(theme.P["muted"])
        self._bar_h = theme.sp(height or 8)
        self.setFixedHeight(len(rows) * (self._row_h + self._gap))

    def paintEvent(self, event) -> None:  # noqa: N802
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        fm = p.fontMetrics()
        p.setFont(self._font)
        y = 0
        bar_x = theme.sp(96)
        for name, frac, note, color in self._rows:
            p.setPen(self._ink)
            p.drawText(0, y + fm.ascent() + theme.sp(2), name)
            track_w = self.width() - bar_x - theme.sp(96)
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(self._track)
            by = y + theme.sp(4)
            p.drawRoundedRect(QRectF(bar_x, by, track_w, self._bar_h),
                              self._bar_h / 2, self._bar_h / 2)
            frac = max(0.0, min(1.0, frac))
            if frac > 0:
                p.setBrush(QColor(color))
                p.drawRoundedRect(QRectF(bar_x, by, max(track_w * frac, self._bar_h), self._bar_h),
                                  self._bar_h / 2, self._bar_h / 2)
            p.setPen(self._muted)
            note_fm = p.fontMetrics()
            p.drawText(self.width() - note_fm.horizontalAdvance(note),
                       y + fm.ascent() + theme.sp(2), note)
            y += self._row_h + self._gap
        p.end()


# ---------------------------------------------------------------- 布局

class BentoGrid(QGridLayout):
    """便当格布局：按 span 自动排布卡片，放不下就换行"""

    def __init__(self, columns: int = 4, gap: int | None = None, row_min: int | None = None):
        super().__init__()
        self._columns = max(1, columns)
        self._col = 0
        self._row = 0
        self._row_min = row_min or 0
        self._max_row = 0
        self.setSpacing(gap or theme.sp(16))
        for c in range(self._columns):
            self.setColumnStretch(c, 1)

    @property
    def columns(self) -> int:
        return self._columns

    def add_card(self, widget, span: int = 1, min_height: int | None = None):
        span = max(1, min(span, self._columns))
        if self._col + span > self._columns:
            self._row += 1
            self._col = 0
        self.addWidget(widget, self._row, self._col, 1, span)
        self._max_row = max(self._max_row, self._row)
        self._col += span
        if self._col >= self._columns:
            self._row += 1
            self._col = 0
        height = min_height or self._row_min
        if height:
            target = self._row if self._col else self._row - 1
            if target >= 0:
                self.setRowMinimumHeight(target, max(height, self.rowMinimumHeight(target)))
        return widget

    def finish(self) -> None:
        """在末尾补一行弹簧，避免卡片被纵向拉伸"""
        row = self._row if self._col == 0 else self._row + 1
        self.setRowStretch(row, 1)

    def reset(self) -> None:
        """清空所有卡片并重置游标（重新渲染页面时调用）"""
        clear_layout(self)
        for r in range(self._max_row + 2):
            self.setRowMinimumHeight(r, 0)
            self.setRowStretch(r, 0)
        self._col = 0
        self._row = 0
        self._max_row = 0


class BentoPage(QWidget):
    """页面骨架：标题行 + 可滚动的便当格（或自定义内容）"""

    def __init__(self, title: str, meta: str = "", columns: int = 4,
                 use_grid: bool = True, scroll: bool = True, row_min: int = 0, parent=None):
        super().__init__(parent)
        self._outer = QVBoxLayout(self)
        self._outer.setContentsMargins(0, 0, 0, 0)
        self._outer.setSpacing(0)

        header = QHBoxLayout()
        header.setSpacing(theme.sp(10))
        self.title_label = label(title, "pageTitle")
        self.meta_label = label(meta, "pageMeta")
        header.addWidget(self.title_label, 0, Qt.AlignmentFlag.AlignVCenter)
        self._meta_slot = QHBoxLayout()
        self._meta_slot.setSpacing(theme.sp(10))
        self._meta_slot.addWidget(self.meta_label)
        header.addLayout(self._meta_slot)
        header.addStretch()
        self.actions = QHBoxLayout()
        self.actions.setSpacing(theme.sp(10))
        header.addLayout(self.actions)
        self._outer.addLayout(header)
        self._outer.addSpacing(theme.sp(12))

        self.grid: BentoGrid | None = None
        if scroll:
            area = QScrollArea()
            area.setWidgetResizable(True)
            area.setFrameShape(QFrame.Shape.NoFrame)
            area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            inner = QWidget()
            inner.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
            self.content = QVBoxLayout(inner)
            self.content.setContentsMargins(0, 0, theme.sp(6), 0)
            self.content.setSpacing(theme.sp(16))
            if use_grid:
                self.grid = BentoGrid(columns, row_min=row_min)
                self.content.addLayout(self.grid)
            self.content.addStretch()
            area.setWidget(inner)
            self._outer.addWidget(area, 1)
        else:
            self.content = QVBoxLayout()
            self.content.setSpacing(theme.sp(16))
            if use_grid:
                self.grid = BentoGrid(columns, row_min=row_min)
                self.content.addLayout(self.grid)
            self._outer.addLayout(self.content, 1)

    def add_action(self, widget) -> None:
        self.actions.addWidget(widget)

    def add_footer(self, widget) -> None:
        """在滚动区下方固定一行（如设置页的保存条）"""
        self._outer.addSpacing(theme.sp(16))
        self._outer.addWidget(widget)

    def add(self, widget, span: int = 1, min_height: int | None = None):
        """向便当格添加卡片（需 use_grid=True）"""
        return self.grid.add_card(widget, span, min_height)

    def finish(self) -> None:
        if self.grid is not None:
            self.grid.finish()

    def set_meta(self, text: str) -> None:
        self.meta_label.setText(text)

    def clear_meta(self) -> None:
        """清空标题行右侧的元信息与操作区"""
        while self._meta_slot.count():
            item = self._meta_slot.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()
        while self.actions.count():
            item = self.actions.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()


def clear_layout(layout) -> None:
    """递归清空布局中的所有控件"""
    while layout.count():
        item = layout.takeAt(0)
        widget = item.widget()
        if widget is not None:
            widget.deleteLater()
        elif item.layout() is not None:
            clear_layout(item.layout())
