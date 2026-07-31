"""
utils/format_utils.py - 格式化工具、终端检测、权限检测
"""
import os
import sys


# ============================================================
# 单位换算
# ============================================================

def bytes_to_gb(value: int | float | None) -> float | None:
    """字节转 GB，保留 1 位小数"""
    if value is None:
        return None
    return round(value / (1024 ** 3), 1)


def bytes_to_mb(value: int | float | None) -> int | None:
    """字节转 MB，取整"""
    if value is None:
        return None
    return round(value / (1024 ** 2))


def kb_to_mb(value: int | float | None) -> int | None:
    """KB 转 MB，取整"""
    if value is None:
        return None
    return round(value / 1024)


def bps_to_gbps(value: int | float | None) -> float | None:
    """bps 转 Gbps，保留 1 位小数"""
    if value is None:
        return None
    return round(value / (1000 ** 3), 1)


def millivolts_to_volts(value: int | float | None) -> float | None:
    """毫伏转伏，保留 2 位小数"""
    if value is None:
        return None
    return round(value / 1000, 2)


def format_size(gb: float | None) -> str:
    """将 GB 数值格式化为人类可读字符串"""
    if gb is None:
        return "未知"
    if gb >= 1024:
        return f"{gb / 1024:.1f} TB"
    return f"{gb:.1f} GB"


# ============================================================
# 终端兼容性检测
# ============================================================

def supports_unicode() -> bool:
    """检测终端是否支持 Unicode 框线字符"""
    if os.environ.get("HWINFO_FORCE_ASCII"):
        return False
    # Windows Terminal 设置此环境变量
    if os.environ.get("WT_SESSION"):
        return True
    # 尝试检测代码页
    try:
        encoding = sys.stdout.encoding or ""
        return encoding.lower().replace("-", "") == "utf8"
    except Exception:
        return False


def supports_color() -> bool:
    """检测终端是否支持 ANSI 颜色"""
    if os.environ.get("HWINFO_NO_COLOR") or os.environ.get("NO_COLOR"):
        return False
    if os.environ.get("WT_SESSION"):
        return True
    # 尝试启用 Windows VT100 模式
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        handle = kernel32.GetStdHandle(-11)  # STD_OUTPUT_HANDLE
        mode = ctypes.c_ulong()
        kernel32.GetConsoleMode(handle, ctypes.byref(mode))
        # ENABLE_VIRTUAL_TERMINAL_PROCESSING = 0x0004
        if mode.value & 0x0004:
            return True
        # 尝试启用
        return bool(kernel32.SetConsoleMode(handle, mode.value | 0x0004))
    except Exception:
        return False


def force_utf8_stdout():
    """强制 stdout 使用 UTF-8 编码，解决 GBK 乱码"""
    import io
    try:
        current_encoding = (sys.stdout.encoding or "").lower().replace("-", "")
        if current_encoding != "utf8":
            sys.stdout = io.TextIOWrapper(
                sys.stdout.buffer, encoding="utf-8", errors="replace"
            )
    except Exception:
        pass  # 如果无法设置，保持原样


# ============================================================
# 权限检测
# ============================================================

def is_admin() -> bool:
    """检测当前是否以管理员身份运行"""
    try:
        import ctypes
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


# ============================================================
# ANSI 颜色代码
# ============================================================

class Colors:
    """ANSI 颜色转义序列"""
    RESET = "\033[0m"
    BOLD = "\033[1m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    CYAN = "\033[36m"
    RED_BOLD = "\033[31;1m"
    CYAN_BOLD = "\033[36;1m"
    GREEN_BOLD = "\033[32;1m"


class NoColors:
    """无颜色（降级模式）"""
    RESET = ""
    BOLD = ""
    RED = ""
    GREEN = ""
    YELLOW = ""
    CYAN = ""
    RED_BOLD = ""
    CYAN_BOLD = ""
    GREEN_BOLD = ""


def get_colors(use_color: bool = True):
    """根据是否启用颜色返回对应的颜色类"""
    if use_color and supports_color():
        return Colors
    return NoColors
