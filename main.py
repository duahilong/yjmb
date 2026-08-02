"""
HWInfo - Windows 硬件检测工具
主入口：无参数 → GUI（未来），有参数 → CLI
"""
import sys
import os

# 将项目根目录加入 sys.path，确保模块导入正常
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def main():
    # 首先处理编码问题
    from utils.format_utils import force_utf8_stdout
    force_utf8_stdout()

    if len(sys.argv) > 1:
        from cli.app import run_cli
        run_cli(sys.argv[1:])
    else:
        from gui.app import run_gui
        run_gui()

    # 程序退出前清理 COM 对象，抑制 pythoncom C 扩展的 "Win32 exception" 消息
    # 这些消息是 COM 对象在解释器关闭时被 GC 释放产生的，不影响功能
    import gc
    gc.collect()
    gc.collect()
    try:
        _devnull = os.open(os.devnull, os.O_WRONLY)
        os.dup2(_devnull, 2)  # 将 stderr 重定向到 devnull，不恢复
        os.close(_devnull)
    except Exception:
        pass


if __name__ == "__main__":
    main()
