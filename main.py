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
        # 第二阶段实现 GUI
        print("HWInfo - Windows 硬件检测工具 v0.1.0")
        print()
        print("GUI 模式尚未实现，请使用命令行参数运行。")
        print("用法: python main.py all")
        print("      python main.py cpu gpu memory")
        print("      python main.py all --json")
        print("      python main.py --help")
        sys.exit(1)

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
