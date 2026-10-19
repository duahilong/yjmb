"""
gui/theme.py - 设计 tokens 与全局 QSS

便当格（Bento）风格：

    浅灰背景 + 白色大圆角卡片 + 柔和阴影 + 每类一色的图标块

这里集中定义颜色、间距、字体与 QSS，页面与组件都从这里取值，
避免各处硬编码。主题（浅色 / 深色）与密度（紧凑 / 舒适 / 大）切换时
只需改本模块状态并重建界面。
"""
from gui.zoom import get_zoom

# ============================================================
# 调色板
# ============================================================

_LIGHT = {
    "bg": "#EEF1F4",
    "card": "#FFFFFF",
    "card_grad": "#F1F5FF",
    "ink": "#1B2430",
    "muted": "#8A93A0",
    "faint": "#A0A8B4",
    "line": "#E6EAF0",
    "soft": "#EDF0F4",
    "shadow": "#A9B4C4",
    "shadow_alpha": 60,
    "hover": "#F7F9FC",
    "ghost_border": "#DDE3EA",
    "track": "#EDEBFA",
    "ok": "#12B886",
    "warn": "#F59F00",
    "err": "#E03131",
    "on_accent": "#FFFFFF",
}

_DARK = {
    "bg": "#0F1216",
    "card": "#181D24",
    "card_grad": "#1D2530",
    "ink": "#E9EEF5",
    "muted": "#8C97A5",
    "faint": "#697485",
    "line": "#262D36",
    "soft": "#222932",
    "shadow": "#000000",
    "shadow_alpha": 150,
    "hover": "#202732",
    "ghost_border": "#333C47",
    "track": "#242C37",
    "ok": "#2FBF87",
    "warn": "#F0A93B",
    "err": "#EF5350",
    "on_accent": "#FFFFFF",
}

_THEMES = {"light": _LIGHT, "dark": _DARK}

# 每类一色（浅色主题用深一档，深色主题自动提亮）
_ACCENTS_LIGHT = {
    "os": "#0EA5E9",
    "motherboard": "#5C7CFA",
    "cpu": "#4C6EF5",
    "memory": "#12B886",
    "gpu": "#F76707",
    "storage": "#7048E8",
    "network": "#1098AD",
    "audio": "#F59F00",
    "monitor": "#E64980",
    "overview": "#4C6EF5",
}

_ACCENTS_DARK = {
    "os": "#38BDF8",
    "motherboard": "#818CF8",
    "cpu": "#7C93FF",
    "memory": "#34D399",
    "gpu": "#FB923C",
    "storage": "#A78BFA",
    "network": "#22D3EE",
    "audio": "#FBBF24",
    "monitor": "#F472B6",
    "overview": "#7C93FF",
}

# 类别 → 图标名（icons.py 中的键）
CATEGORY_ICONS = {
    "overview": "overview",
    "os": "os",
    "motherboard": "motherboard",
    "cpu": "cpu",
    "memory": "memory",
    "gpu": "gpu",
    "storage": "storage",
    "network": "network",
    "audio": "audio",
    "monitor": "monitor",
    "settings": "settings",
}

# 密度：名称 → 间距/尺寸比例
DENSITY = {"compact": 0.86, "comfortable": 1.0, "large": 1.16}
DENSITY_LABELS = {"compact": "紧凑", "comfortable": "舒适", "large": "大"}
THEME_LABELS = {"light": "浅色", "dark": "深色"}

_state = {"theme": "light", "density": "comfortable"}

# 当前生效的 token（原地更新，保证组件持有的引用始终有效）
P: dict = {}
ACCENTS: dict = {}


def _apply() -> None:
    """按当前主题刷新 token 与强调色"""
    name = _state["theme"]
    P.clear()
    P.update(_THEMES.get(name, _LIGHT))
    ACCENTS.clear()
    ACCENTS.update(_ACCENTS_DARK if name == "dark" else _ACCENTS_LIGHT)


_apply()


# ============================================================
# 状态读写
# ============================================================

def set_theme(name: str) -> None:
    """切换主题：light / dark"""
    if name in _THEMES:
        _state["theme"] = name
        _apply()


def get_theme() -> str:
    return _state["theme"]


def set_density(name: str) -> None:
    """切换密度：compact / comfortable / large"""
    if name in DENSITY:
        _state["density"] = name


def get_density() -> str:
    return _state["density"]


def accent(key: str) -> str:
    """取类别强调色"""
    return ACCENTS.get(key, ACCENTS.get("overview", "#4C6EF5"))


def sp(value: float) -> int:
    """间距/尺寸换算：密度 × 缩放，最小 1 像素"""
    return max(1, round(value * DENSITY[_state["density"]] * get_zoom()))


def shadow_params() -> tuple[str, int, int]:
    """卡片阴影：(颜色, 模糊半径, 偏移)，随缩放变化"""
    return P["shadow"], sp(26), sp(8)


# ============================================================
# 全局 QSS
# ============================================================

def build_qss() -> str:
    """生成当前主题 / 密度 / 缩放下完整的全局 QSS"""
    shadow = P["shadow"]
    return f"""
* {{
    font-family: "Microsoft YaHei UI", "Segoe UI", sans-serif;
    font-size: {sp(13)}px;
}}

QWidget {{
    color: {P['ink']};
}}

#root {{
    background-color: {P['bg']};
}}

/* ---------- 顶栏 ---------- */
#brand {{
    font-family: "Bahnschrift", "Microsoft YaHei UI", sans-serif;
    font-size: {sp(20)}px;
    font-weight: 700;
    color: {P['ink']};
}}
#hostText {{
    font-family: "Cascadia Mono", Consolas, monospace;
    font-size: {sp(11)}px;
    color: {P['muted']};
}}
#metaText {{
    font-family: "Cascadia Mono", Consolas, monospace;
    font-size: {sp(11)}px;
    color: {P['faint']};
}}

/* ---------- 导航胶囊 ---------- */
QPushButton#navItem {{
    background-color: transparent;
    border: none;
    border-radius: {sp(13)}px;
    padding: {sp(7)}px {sp(14)}px;
    color: {P['muted']};
    font-size: {sp(12)}px;
}}
QPushButton#navItem:hover {{
    background-color: {P['soft']};
    color: {P['ink']};
}}
QPushButton#navActive {{
    background-color: {P['card']};
    border: none;
    border-radius: {sp(13)}px;
    padding: {sp(7)}px {sp(14)}px;
    color: {P['ink']};
    font-size: {sp(12)}px;
    font-weight: 600;
}}

/* ---------- 按钮 ---------- */
QPushButton#btnDefault {{
    background-color: {P['card']};
    border: none;
    border-radius: {sp(13)}px;
    padding: {sp(8)}px {sp(16)}px;
    color: {P['ink']};
    font-size: {sp(12)}px;
}}
QPushButton#btnDefault:hover {{ background-color: {P['hover']}; }}
QPushButton#btnGhost {{
    background-color: transparent;
    border: 1px solid {P['ghost_border']};
    border-radius: {sp(13)}px;
    padding: {sp(7)}px {sp(16)}px;
    color: {P['ink']};
    font-size: {sp(12)}px;
}}
QPushButton#btnGhost:hover {{ background-color: {P['card']}; }}
QPushButton#btnPrimary {{
    background-color: {accent('cpu')};
    border: none;
    border-radius: {sp(13)}px;
    padding: {sp(8)}px {sp(18)}px;
    color: {P['on_accent']};
    font-size: {sp(12)}px;
    font-weight: 600;
}}
QPushButton#btnPrimary:hover {{ background-color: {P['ink']}; }}
QPushButton#btnIcon {{
    background-color: {P['card']};
    border: none;
    border-radius: {sp(15)}px;
    color: {P['muted']};
    font-size: {sp(11)}px;
}}
QPushButton#btnIcon:hover {{ background-color: {P['hover']}; }}

/* ---------- 分段控件 ---------- */
#segTrack {{
    background-color: {P['soft']};
    border-radius: {sp(13)}px;
}}
QPushButton#segItem {{
    background-color: transparent;
    border: none;
    border-radius: {sp(13)}px;
    padding: {sp(7)}px {sp(15)}px;
    color: {P['muted']};
    font-size: {sp(12)}px;
}}
QPushButton#segItem:hover {{ color: {P['ink']}; }}
QPushButton#segActive {{
    background-color: {P['card']};
    border: none;
    border-radius: {sp(13)}px;
    padding: {sp(7)}px {sp(15)}px;
    color: {P['ink']};
    font-size: {sp(12)}px;
    font-weight: 600;
}}

/* ---------- 卡片 ---------- */
#card {{
    background-color: {P['card']};
    border-radius: {sp(20)}px;
}}
#heroCard {{
    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 {P['card']}, stop:1 {P['card_grad']});
    border-radius: {sp(20)}px;
}}
#actionBar {{
    background-color: {P['card']};
    border-radius: {sp(18)}px;
}}

/* ---------- 文本角色 ---------- */
#kicker {{ font-family: "Cascadia Mono", Consolas, monospace; font-size: {sp(11)}px; color: {P['faint']}; }}
#idModel {{ font-family: "Bahnschrift", "Microsoft YaHei UI", sans-serif; font-size: {sp(34)}px; font-weight: 700; color: {P['ink']}; }}
#idSub {{ font-size: {sp(12)}px; color: {P['muted']}; }}
#cardTitle {{ font-size: {sp(13)}px; color: {P['muted']}; }}
#cardValue {{ font-family: "Bahnschrift", "Microsoft YaHei UI", sans-serif; font-size: {sp(27)}px; font-weight: 700; color: {P['ink']}; }}
#cardSub {{ font-size: {sp(12)}px; color: {P['muted']}; }}
#miniLabel {{ font-size: {sp(11)}px; color: {P['faint']}; }}
#miniValue {{ font-family: "Bahnschrift", "Microsoft YaHei UI", sans-serif; font-size: {sp(19)}px; font-weight: 600; color: {P['ink']}; }}
#rowName {{ font-size: {sp(12)}px; color: {P['ink']}; font-weight: 600; }}
#rowSub {{ font-size: {sp(12)}px; color: {P['muted']}; }}
#pageTitle {{ font-family: "Bahnschrift", "Microsoft YaHei UI", sans-serif; font-size: {sp(30)}px; font-weight: 700; color: {P['ink']}; }}
#pageMeta {{ font-size: {sp(12)}px; color: {P['muted']}; }}
#specKey {{ font-size: {sp(12)}px; color: {P['muted']}; }}
#specValue {{ font-family: "Cascadia Mono", Consolas, monospace; font-size: {sp(12)}px; color: {P['ink']}; }}
#stateTitle {{ font-size: {sp(14)}px; font-weight: 700; color: {P['ink']}; }}
#stateBody {{ font-size: {sp(12)}px; color: {P['muted']}; }}
#hintText {{ font-size: {sp(12)}px; color: {P['faint']}; }}
#placeholder {{ color: {P['faint']}; font-size: {sp(13)}px; }}

/* ---------- 滚动区 ---------- */
QScrollArea {{ background-color: transparent; border: none; }}
QScrollArea > QWidget > QWidget {{ background-color: transparent; }}
QScrollBar:vertical {{ background: transparent; width: {sp(9)}px; margin: 0; }}
QScrollBar::handle:vertical {{ background: {P['line']}; border-radius: {sp(4)}px; min-height: {sp(30)}px; }}
QScrollBar::handle:vertical:hover {{ background: {P['faint']}; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
QScrollBar:horizontal {{ height: 0; }}

/* ---------- 提示 ---------- */
QToolTip {{
    background-color: {P['ink']};
    color: {P['bg']};
    border: none;
    padding: {sp(6)}px {sp(10)}px;
    border-radius: {sp(6)}px;
    font-size: {sp(11)}px;
}}
"""
