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


def run_gui() -> None:
    """启动 GUI 应用"""
    from PySide6.QtWidgets import QApplication
    from PySide6.QtCore import Qt

    # 高 DPI 支持
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setApplicationName("HWInfo")
    app.setApplicationDisplayName("HWInfo - Windows 硬件检测工具")
    app.setOrganizationName("HWInfo")

    # 加载全局样式表
    qss_path = resource_path(os.path.join("gui", "resources", "style.qss"))
    if os.path.exists(qss_path):
        with open(qss_path, "r", encoding="utf-8") as f:
            app.setStyleSheet(f.read())

    from gui.main_window import MainWindow
    window = MainWindow()
    window.show()

    exit_code = app.exec()
    # 事件循环退出后（而非 sys.exit 内部）执行清理，确保清理代码可达
    _suppress_com_noise()
    sys.exit(exit_code)
