"""
utils/wmi_helper.py - WMI 连接管理与通用工具

注意：WMI 基于 COM，每个线程必须独立初始化 COM 并创建自己的连接。
不能使用全局共享连接跨线程。
"""
import threading

# 使用线程本地存储，每个线程拥有独立的 WMI 连接
_thread_local = threading.local()

# win32com 动态分发（Dispatch/GetObject）存在全局类型缓存，
# 多线程并发首次初始化会触发竞态（"接口未知"/"参数错误"等间歇性 COM 错误），
# 因此连接的首次创建需全局串行化。
_init_lock = threading.Lock()

_DEFAULT_NAMESPACE = "root\\cimv2"


def _connections() -> dict[str, object]:
    """当前线程的 命名空间 → WMI 连接 缓存。"""
    conns = getattr(_thread_local, "connections", None)
    if conns is None:
        conns = {}
        _thread_local.connections = conns
    return conns


def get_wmi(namespace: str = _DEFAULT_NAMESPACE):
    """获取当前线程指定命名空间的 WMI 连接（线程本地缓存）。

    默认 root\\cimv2；其他常用命名空间：
    - root\\wmi（显示器 EDID 等）
    - root\\Microsoft\\Windows\\Storage（MSFT_PhysicalDisk 等）
    """
    conns = _connections()
    conn = conns.get(namespace)
    if conn is None:
        with _init_lock:
            # 双重检查：等待锁期间可能已被本线程创建
            conn = conns.get(namespace)
            if conn is None:
                import pythoncom
                import wmi
                pythoncom.CoInitialize()
                conn = wmi.WMI(namespace=namespace)
                conns[namespace] = conn
    return conn


def get_wmi_namespace(namespace: str):
    """按命名空间获取 WMI 连接（get_wmi 的显式别名，便于调用方阅读）。"""
    return get_wmi(namespace)


def get_wmi_root():
    """获取当前线程的 root\\wmi WMI 连接（用于显示器等）"""
    return get_wmi("root\\wmi")


def cleanup_com():
    """清理当前线程的 COM 资源（在线程结束前调用）

    注意：不调用 CoUninitialize()，因为 WMI 库内部会创建大量 COM 对象，
    部分对象可能在 gc 之前就被 CoUninitialize 报错。
    线程池线程结束时 OS 会自动清理 COM 状态。
    """
    try:
        import gc

        # 显式释放 WMI 连接对象（含所有命名空间），释放 COM 引用
        conns = getattr(_thread_local, "connections", None)
        if conns is not None:
            conns.clear()
            del _thread_local.connections

        # 强制垃圾回收，尽早释放 COM 接口
        gc.collect()
    except Exception:
        pass


def parse_wmi_datetime(wmi_date_str: str | None) -> str | None:
    """
    将 WMI 时间格式转为可读字符串。
    输入: '20240315102030.123456+480'
    输出: '2024-03-15 10:20:30'

    如果只有日期部分（如 '20240315******.******+***'），输出 '2024-03-15'
    """
    if not wmi_date_str:
        return None

    try:
        # 取前 14 位: YYYYMMDDHHmmss
        date_part = wmi_date_str.split(".")[0]

        if "*" in date_part:
            # 只有日期部分有效
            valid = date_part.replace("*", "")
            if len(valid) >= 8:
                return f"{date_part[:4]}-{date_part[4:6]}-{date_part[6:8]}"
            return None

        if len(date_part) >= 14:
            return (
                f"{date_part[0:4]}-{date_part[4:6]}-{date_part[6:8]} "
                f"{date_part[8:10]}:{date_part[10:12]}:{date_part[12:14]}"
            )
        elif len(date_part) >= 8:
            return f"{date_part[0:4]}-{date_part[4:6]}-{date_part[6:8]}"
        else:
            return wmi_date_str
    except (IndexError, ValueError):
        return wmi_date_str


def parse_wmi_date_only(wmi_date_str: str | None) -> str | None:
    """
    只取日期部分。
    输入: '20240315102030.123456+480'
    输出: '2024-03-15'
    """
    full = parse_wmi_datetime(wmi_date_str)
    if full and len(full) >= 10:
        return full[:10]
    return full
