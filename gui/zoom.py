"""
gui/zoom.py - 界面缩放工具

全局缩放系数：所有 QSS 中的 px 数值与 Python 侧硬编码尺寸按同一比例缩放，
保证字体与页面布局整体协调，不会出现"文字变大但样式未同步"。

缩放状态保存在模块级（不持久化），程序重启后自动恢复默认 1.0。
"""
import re

# 缩放范围与步进
ZOOM_MIN = 0.7
ZOOM_MAX = 1.6
ZOOM_STEP = 0.1

# 匹配 "Npx" / "N.Npx"（不影响颜色、百分比、无单位值）
_PX_RE = re.compile(r"(\d+(?:\.\d+)?)px")

# 当前全局缩放系数（模块级，进程内共享；程序重启后恢复默认 1.2）
_current_zoom = 1.2


def set_zoom(zoom: float) -> None:
    """设置当前全局缩放系数"""
    global _current_zoom
    _current_zoom = zoom


def get_zoom() -> float:
    """获取当前全局缩放系数"""
    return _current_zoom


def scaled(value: int) -> int:
    """Python 侧尺寸按当前缩放系数换算（最小 1，避免尺寸归零）"""
    return max(1, round(value * _current_zoom))


def scale_qss(qss_text: str, zoom: float | None = None) -> str:
    """将 QSS 文本中所有 px 数值按缩放系数换算"""
    if zoom is None:
        zoom = _current_zoom
    if zoom == 1.0:
        return qss_text
    return _PX_RE.sub(lambda m: f"{round(float(m.group(1)) * zoom)}px", qss_text)
