"""
gui/theme.py - 设计 tokens 与全局 QSS

手写风单页版式（纯白底、蓝色分类名、无卡片无圆角）：

    顶栏：品牌 · 主机 / 系统 · 采集状态 · 全部|精简 · 标签 · 搜索 · 计数
    画板：9 个类别，一行一个字段，按窗口宽度分栏，字号自适应到一屏放下

界面只有浅色一种主题。这里集中定义颜色、间距与 QSS，页面只从这里取值。
画板本身的字号由 gui.board 按窗口尺寸实时计算，不跟这里的缩放系数走。
"""
from gui.zoom import get_zoom

# ============================================================
# 调色板（浅色单主题）
# ============================================================

P = {
    "bg": "#FFFFFF",
    "card": "#FFFFFF",
    "ink": "#1D1D1F",
    "text2": "#333336",
    "muted": "#6F7075",
    "faint": "#9A9AA0",
    "tertiary": "#9A9AA0",
    "line": "#E6E6E9",
    "line_soft": "#F1F1F4",
    "accent": "#1668DC",
    "accent_soft": "rgba(22, 104, 220, 0.10)",
    "ok": "#1D8A3C",
    "warn": "#B26A00",
    "err": "#C62828",
    "off": "#8E8E93",
    "field": "#F2F2F5",
    "hover": "#F5F5F7",
    "on_accent": "#FFFFFF",
    "shadow": "#000000",
}

# 密度：名称 → 间距比例（紧凑 / 舒适 / 大）
DENSITY = {"compact": 0.86, "comfortable": 1.0, "large": 1.16}
DENSITY_LABELS = {"compact": "紧凑", "comfortable": "舒适", "large": "大"}
THEME_LABELS = {"light": "浅色"}

_state = {"theme": "light", "density": "comfortable"}


# ============================================================
# 状态读写
# ============================================================

def set_theme(name: str) -> None:
    """只保留浅色主题；传入其它值也保持浅色。"""
    _state["theme"] = "light"


def get_theme() -> str:
    return _state["theme"]


def set_density(name: str) -> None:
    """切换密度：compact / comfortable / large"""
    if name in DENSITY:
        _state["density"] = name


def get_density() -> str:
    return _state["density"]


def accent(key: str = "") -> str:
    """强调色（画板分类名统一用同一个蓝）"""
    return P["accent"]


def sp(value: float) -> int:
    """间距/尺寸换算：密度 × 缩放，最小 1 像素"""
    return max(1, round(value * DENSITY[_state["density"]] * get_zoom()))


def shadow_params() -> tuple[str, int, int]:
    """保留给旧调用：卡片阴影（新版式不再使用）"""
    return P["shadow"], sp(26), sp(8)


# ============================================================
# 全局 QSS
# ============================================================

def build_qss() -> str:
    """生成当前密度 / 缩放下的全局 QSS"""
    return f"""
* {{
    font-family: "Microsoft YaHei UI", "Segoe UI", sans-serif;
    font-size: {sp(12)}px;
}}

QWidget {{
    color: {P['ink']};
}}

#root {{
    background-color: {P['bg']};
}}

/* ---------- 顶栏 ---------- */
#topbar {{
    background-color: {P['card']};
    border-bottom: 1px solid {P['line']};
}}
#brand {{
    color: {P['ink']};
    font-size: {sp(13)}px;
    font-weight: 600;
}}
#brandSub {{
    color: {P['faint']};
    font-size: {sp(11)}px;
}}
#hostText {{
    color: {P['muted']};
    font-size: {sp(11)}px;
}}
#statusText {{
    color: {P['muted']};
    font-size: {sp(11)}px;
}}
#metaText {{
    color: {P['faint']};
    font-size: {sp(10)}px;
}}
#countText {{
    color: {P['faint']};
    font-size: {sp(11)}px;
}}

/* ---------- 顶栏分段开关 ---------- */
QPushButton#segItem {{
    background-color: transparent;
    border: none;
    border-radius: {sp(4)}px;
    padding: 0 {sp(8)}px;
    min-height: {sp(22)}px;
    max-height: {sp(22)}px;
    color: {P['muted']};
    font-size: {sp(11)}px;
}}
QPushButton#segItem:hover {{
    background-color: {P['field']};
    color: {P['ink']};
}}
QPushButton#segItem:checked {{
    background-color: {P['accent_soft']};
    color: {P['accent']};
    font-weight: 600;
}}

/* ---------- 顶栏图标按钮 ---------- */
QToolButton#toolIcon {{
    background-color: transparent;
    border: none;
    border-radius: {sp(4)}px;
    padding: {sp(3)}px;
}}
QToolButton#toolIcon:hover {{
    background-color: {P['field']};
}}

/* ---------- 搜索框 ---------- */
QLineEdit#searchBox {{
    background-color: {P['card']};
    border: 1px solid {P['line']};
    border-radius: {sp(5)}px;
    padding: 0 {sp(8)}px;
    min-height: {sp(24)}px;
    max-height: {sp(24)}px;
    color: {P['ink']};
    font-size: {sp(11)}px;
    selection-background-color: {P['accent_soft']};
    selection-color: {P['ink']};
}}
QLineEdit#searchBox:focus {{
    border: 1px solid {P['accent']};
}}
QLineEdit#searchBox::placeholder {{
    color: {P['faint']};
}}

/* ---------- 画板 ---------- */
QScrollArea#boardScroll {{
    background-color: {P['bg']};
    border: none;
}}
QScrollArea#boardScroll > QWidget > QWidget {{
    background-color: {P['bg']};
}}
QScrollBar:vertical {{
    background: transparent;
    width: {sp(10)}px;
    margin: 0;
}}
QScrollBar::handle:vertical {{
    background: rgba(0, 0, 0, 0.22);
    border: 3px solid transparent;
    background-clip: content-box;
    border-radius: {sp(5)}px;
    min-height: {sp(30)}px;
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}
QScrollBar:horizontal {{ height: 0; }}

/* ---------- 设置对话框 ---------- */
QDialog#settingsDialog {{
    background-color: {P['bg']};
}}
QLabel#dialogTitle {{
    color: {P['ink']};
    font-size: {sp(15)}px;
    font-weight: 600;
}}
QLabel#groupTitle {{
    color: {P['muted']};
    font-size: {sp(11)}px;
}}
QCheckBox {{
    color: {P['ink']};
    font-size: {sp(12)}px;
    spacing: {sp(8)}px;
}}
QSpinBox {{
    background-color: {P['card']};
    border: 1px solid {P['line']};
    border-radius: {sp(4)}px;
    padding: {sp(3)}px {sp(6)}px;
    min-height: {sp(20)}px;
    color: {P['ink']};
}}
QPushButton#dialogCancel {{
    background-color: transparent;
    border: 1px solid {P['line']};
    border-radius: {sp(5)}px;
    padding: {sp(5)}px {sp(16)}px;
    color: {P['ink']};
    font-size: {sp(12)}px;
}}
QPushButton#dialogCancel:hover {{
    background-color: {P['field']};
}}
QPushButton#dialogSave {{
    background-color: {P['accent']};
    border: none;
    border-radius: {sp(5)}px;
    padding: {sp(6)}px {sp(18)}px;
    color: {P['on_accent']};
    font-size: {sp(12)}px;
    font-weight: 600;
}}
QPushButton#dialogSave:hover {{
    background-color: #0F5AC0;
}}

/* ---------- 提示 ---------- */
QToolTip {{
    background-color: {P['ink']};
    color: {P['bg']};
    border: none;
    padding: {sp(5)}px {sp(8)}px;
    border-radius: {sp(4)}px;
    font-size: {sp(10)}px;
}}
"""
