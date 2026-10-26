"""
gui/app.py - GUI 应用入口
"""
import os
import sys


def resource_path(rel_path: str) -> str:
    """
    返回资源文件的绝对路径，兼容 PyInstaller 打包环境。

    开发模式: <项目根>/gui/<rel_path>
    打包模式: <解压临时目录>/<rel_path>（spec 中 datas 需包含对应目录）
    """
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, rel_path)
    return os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), rel_path)


def _suppress_com_noise() -> None:
    """程序退出前清理 COM 对象，并将 stderr 重定向到 devnull，抑制
    pythoncom C 扩展在解释器关闭时产生的 "Win32 exception" 消息。
    这些消息是 COM 对象被 GC 释放产生的，不影响功能。
    仅 GUI 模式调用（CLI 需保留 stderr 输出 --debug 信息）。"""
    import gc
    gc.collect()
    gc.collect()
    try:
        _devnull = os.open(os.devnull, os.O_WRONLY)
        os.dup2(_devnull, 2)  # 将 stderr 重定向到 devnull，不恢复
        os.close(_devnull)
    except Exception:
        pass


def _preload_backend() -> None:
    """在主线程预热采集依赖。

    pywin32 的扩展 DLL（pywintypes）首次导入会持有导入锁并等待系统加载器锁；
    如果这一步发生在采集线程，而主线程正在做首次绘制（同样会加载 Qt 的 DLL），
    两者可能互相等待，表现为所有类别「采集超时」。提前在主线程导入即可避免。
    """
    try:
        import pythoncom  # noqa: F401
        import wmi  # noqa: F401
    except Exception:  # noqa: BLE001
        pass
    try:
        import pynvml  # noqa: F401
    except Exception:  # noqa: BLE001
        pass
    try:
        import collectors
        collectors.load_all()
    except Exception:  # noqa: BLE001
        pass


def run_gui() -> None:
    """启动 GUI 应用"""
    from PySide6.QtWidgets import QApplication
    from PySide6.QtCore import Qt
    from gui.icons import app_icon

    _preload_backend()

    # 高 DPI 支持
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setApplicationName("HWInfo")
    app.setApplicationDisplayName("Windows 硬件检测工具")
    app.setOrganizationName("HWInfo")
    app.setWindowIcon(app_icon())
    # Fusion 对 QSS 圆角/边框的渲染最稳定，不受 Windows 原生控件主题干扰
    app.setStyle("Fusion")

    # 主题、密度与缩放来自 config.yaml 的 gui 段
    from gui import prefs, theme
    from gui.zoom import ZOOM_MAX, ZOOM_MIN, set_zoom

    saved = prefs.gui_prefs()
    theme.set_theme(saved.get("theme", "light"))
    theme.set_density(saved.get("density", "comfortable"))
    try:
        set_zoom(max(ZOOM_MIN, min(ZOOM_MAX, float(saved.get("zoom", 1.0)))))
    except (TypeError, ValueError):
        set_zoom(1.0)

    app.setStyleSheet(theme.build_qss())

    from gui.main_window import MainWindow
    window = MainWindow()
    window.show()

    exit_code = app.exec()
    # 事件循环退出后（而非 sys.exit 内部）执行清理，确保清理代码可达
    _suppress_com_noise()
    sys.exit(exit_code)
