"""
HWInfo - Windows 硬件检测工具
主入口：无参数 → GUI，有参数 → CLI
"""
import sys
import os

# 将项目根目录加入 sys.path，确保模块导入正常
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def main():
    # 首先处理编码问题
    from utils.format_utils import force_utf8_stdout
    force_utf8_stdout()

    # 初始化日志（CLI --debug 时输出 DEBUG 级）
    from utils.logger import setup_logging
    setup_logging(debug="--debug" in sys.argv)

    if len(sys.argv) > 1:
        from cli.app import run_cli
        run_cli(sys.argv[1:])
    else:
        from gui.app import run_gui
        run_gui()


if __name__ == "__main__":
    main()
