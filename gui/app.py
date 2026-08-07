"""
gui/app.py - GUI 应用入口
"""
import os
import sys


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
    qss_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resources", "style.qss")
    if os.path.exists(qss_path):
        with open(qss_path, "r", encoding="utf-8") as f:
            app.setStyleSheet(f.read())

    from gui.main_window import MainWindow
    window = MainWindow()
    window.show()

    sys.exit(app.exec())
