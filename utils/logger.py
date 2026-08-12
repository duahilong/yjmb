"""
utils/logger.py - 统一日志配置

日志输出到 stderr：
- CLI 模式直接可见（配合 --debug 可输出 DEBUG 级）
- GUI windowed 模式默认无控制台，可通过环境变量 HWINFO_LOG_LEVEL 调整级别，
  或在开发模式下从终端启动观察
"""
import logging
import os
import sys

_CONFIGURED = False


def setup_logging(debug: bool = False) -> None:
    """初始化根日志器（幂等，重复调用无副作用）"""
    global _CONFIGURED
    if _CONFIGURED:
        return

    level_name = os.environ.get("HWINFO_LOG_LEVEL", "").upper()
    if level_name in ("DEBUG", "INFO", "WARNING", "ERROR"):
        level = getattr(logging, level_name)
    else:
        level = logging.DEBUG if debug else logging.INFO

    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(
        logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s",
                          datefmt="%H:%M:%S")
    )
    root = logging.getLogger()
    root.setLevel(level)
    root.addHandler(handler)
    _CONFIGURED = True


def get_logger(name: str) -> logging.Logger:
    """获取带模块名的 logger（首次调用自动初始化）"""
    setup_logging()
    return logging.getLogger(name)
