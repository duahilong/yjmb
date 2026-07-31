"""
cli/app.py - CLI 命令行解析与执行
"""
import sys
import time
import argparse

from core.manager import CollectorManager
from core.registry import get_all_collectors
from core.constants import VERSION, ALL_CATEGORIES
from formatters.terminal import TerminalFormatter
from formatters.json_fmt import JsonFormatter
from config.settings import Settings


def build_parser() -> argparse.ArgumentParser:
    """构建命令行参数解析器"""
    parser = argparse.ArgumentParser(
        prog="hwinfo",
        description="HWInfo - Windows 硬件检测工具",
        epilog="示例: python main.py all | python main.py cpu gpu --json",
    )

    # 位置参数：要显示的类别
    parser.add_argument(
        "categories",
        nargs="*",
        default=["all"],
        help="要显示的硬件类别 (cpu/gpu/memory/storage/network/audio/monitor/os/motherboard/all)",
    )

    # 可选参数
    parser.add_argument("--hide", type=str, default="",
                        help="要隐藏的类别，逗号分隔")
    parser.add_argument("--json", action="store_true",
                        help="以 JSON 格式输出")
    parser.add_argument("--brief", action="store_true",
                        help="简洁模式，只显示关键字段")
    parser.add_argument("--no-color", action="store_true",
                        help="禁用彩色输出")
    parser.add_argument("--debug", action="store_true",
                        help="输出调试信息到 stderr")
    parser.add_argument("--config", type=str, default=None,
                        help="指定配置文件路径")
    parser.add_argument("--version", action="version",
                        version=f"HWInfo v{VERSION}")

    return parser


def resolve_categories(
    categories: list[str],
    hide: str,
    settings: Settings = None,
) -> list[str] | None:
    """
    解析要采集的类别列表。

    Returns:
        类别列表，None 表示全部。
    """
    # 处理 hide
    exclude = set()
    if hide:
        exclude = {h.strip().lower() for h in hide.split(",") if h.strip()}

    # 从配置文件读取禁用的类别
    if settings:
        for cat in ALL_CATEGORIES:
            if not settings.is_display_enabled(cat):
                exclude.add(cat)

    # 处理 categories
    if not categories or "all" in categories:
        # 全部类别，减去 exclude
        if exclude:
            return [c for c in ALL_CATEGORIES if c not in exclude]
        return None  # None 表示全部
    else:
        # 指定类别
        result = []
        for cat in categories:
            cat = cat.strip().lower()
            if cat in ALL_CATEGORIES and cat not in exclude:
                result.append(cat)
        return result if result else None


def run_cli(argv: list[str]) -> None:
    """CLI 模式主入口"""
    parser = build_parser()
    args = parser.parse_args(argv)

    # 加载配置
    settings = Settings(config_path=args.config)
    settings.apply_cli_overrides(args)

    # 调试模式
    if args.debug:
        print(f"[DEBUG] 参数: {args}", file=sys.stderr)
        print(f"[DEBUG] 配置: color={settings.get_color_mode()}, "
              f"unicode={settings.get_unicode_mode()}, "
              f"timeout={settings.get_timeout()}s, "
              f"parallel={settings.is_parallel()}", file=sys.stderr)

    # 确定要采集的类别
    categories = resolve_categories(args.categories, args.hide, settings)

    if args.debug:
        print(f"[DEBUG] 采集类别: {categories or '全部'}", file=sys.stderr)

    # 加载所有 collector 模块（触发注册）
    import collectors
    collectors.load_all()

    # 创建 manager 并注册所有 collector
    manager = CollectorManager()
    manager.TIMEOUT = settings.get_timeout()
    for c in get_all_collectors():
        manager.register(c)

    if args.debug:
        print(f"[DEBUG] 已注册: {[c['name'] for c in manager.list_collectors()]}", file=sys.stderr)

    # 执行采集
    start_time = time.perf_counter()
    result = manager.collect(
        categories=categories,
        parallel=settings.is_parallel(),
    )
    total_time = time.perf_counter() - start_time

    if args.debug:
        print(f"[DEBUG] 采集耗时: {result.elapsed_seconds}s (总耗时: {total_time:.2f}s)", file=sys.stderr)
        print(f"[DEBUG] 采集结果: {list(result.data.keys())}", file=sys.stderr)
        if result.errors:
            print(f"[DEBUG] 错误: {result.errors}", file=sys.stderr)
        if result.warnings:
            print(f"[DEBUG] 警告: {result.warnings}", file=sys.stderr)

    # 选择 formatter 并输出
    if args.json:
        formatter = JsonFormatter()
    else:
        # 根据配置决定颜色/unicode
        use_color = not args.no_color and settings.get_color_mode() != "never"
        use_unicode = settings.get_unicode_mode() != "never"
        formatter = TerminalFormatter(
            use_color=use_color,
            use_unicode=use_unicode,
        )

    output = formatter.render(result, brief=args.brief)
    print(output)
