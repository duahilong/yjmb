"""
gui/prefs.py - GUI 配置读写

与 CLI 共用同一份 config.yaml：

    display:  各类别是否显示（CLI 的 all/brief 也读这里）
    collect:  超时等采集设置
    gui:      仅界面使用的偏好（主题、密度、窗口置顶、缩放）

读写都直接操作 YAML 文件，写回时保留其它段落，避免把手写配置冲掉。
"""
import copy

from config.settings import get_user_config_path
from utils.logger import get_logger

logger = get_logger(__name__)

# gui 段默认值
GUI_DEFAULTS = {
    "theme": "light",
    "density": "comfortable",
    "on_top": False,
    "zoom": 1.0,
}


def _load_yaml() -> dict:
    path = get_user_config_path()
    try:
        import yaml
        import os
        if not os.path.exists(path):
            return {}
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except Exception:  # noqa: BLE001
        logger.warning("读取 GUI 配置失败，使用默认值")
        return {}


def _save_yaml(data: dict) -> bool:
    path = get_user_config_path()
    try:
        import yaml
        with open(path, "w", encoding="utf-8") as f:
            yaml.safe_dump(data, f, allow_unicode=True, sort_keys=True, default_flow_style=False)
        return True
    except Exception:  # noqa: BLE001
        logger.exception("写入 GUI 配置失败")
        return False


def gui_prefs() -> dict:
    """界面偏好（缺项用默认值补齐）"""
    prefs = copy.deepcopy(GUI_DEFAULTS)
    prefs.update(_load_yaml().get("gui") or {})
    return prefs


def set_gui_pref(key: str, value) -> bool:
    """写入单个界面偏好"""
    data = _load_yaml()
    data.setdefault("gui", {})[key] = value
    return _save_yaml(data)


def display_map() -> dict:
    """各类别的显示开关"""
    from core.constants import ALL_CATEGORIES
    stored = _load_yaml().get("display") or {}
    return {cat: bool(stored.get(cat, True)) for cat in ALL_CATEGORIES}


def set_display(categories: dict) -> bool:
    """写入各类别的显示开关"""
    data = _load_yaml()
    section = data.setdefault("display", {})
    for cat, enabled in categories.items():
        section[cat] = bool(enabled)
    return _save_yaml(data)


def get_timeout() -> int:
    """单模块超时秒数"""
    try:
        return int((_load_yaml().get("collect") or {}).get("timeout", 10))
    except (TypeError, ValueError):
        return 10


def set_timeout(seconds: int) -> bool:
    data = _load_yaml()
    data.setdefault("collect", {})["timeout"] = int(seconds)
    return _save_yaml(data)


def enabled_categories() -> list[str]:
    """按 ORDER_MAP 顺序返回已启用的类别。

    注意：返回空列表表示「全部关闭」，调用方必须与 None（全部采集）区分开。
    """
    from core.constants import ALL_CATEGORIES
    shown = display_map()
    return [cat for cat in ALL_CATEGORIES if shown.get(cat, True)]
