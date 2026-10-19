"""
gui/worker.py - 后台采集线程

比 CLI 多一件事：每采集完一个类别就发出一次信号，
界面可以逐张卡片填充，而不是等到全部结束才刷新。
"""
from PySide6.QtCore import QThread, Signal

from core.manager import CollectorManager, CollectResult
from utils.logger import get_logger

logger = get_logger(__name__)


class CollectWorker(QThread):
    """后台硬件信息采集线程"""

    # 开始采集时发出本次要采集的类别（界面先把它们置为「等待」）
    started_categories = Signal(list)
    # 单个类别完成：名称、数据（失败为 None）、耗时
    category_done = Signal(str, object, float)
    # 全部完成，携带 CollectResult
    # 注意：不能命名为 finished，否则会遮蔽 QThread 内建的 finished 信号
    collect_finished = Signal(object)
    # 采集整体失败
    error = Signal(str)
    # 状态文本（初始化等）
    progress = Signal(str)

    def __init__(self, categories: list[str] | None = None,
                 timeout: float | None = None, parent=None):
        super().__init__(parent)
        self._categories = categories
        self._timeout = timeout

    def run(self) -> None:  # noqa: D102
        try:
            if self.isInterruptionRequested():
                return

            self.progress.emit("正在初始化采集…")
            import collectors
            collectors.load_all()

            from core.registry import get_all_collectors
            manager = CollectorManager()
            for collector in get_all_collectors():
                manager.register(collector)
            if self._timeout:
                # 仅并行采集路径有整体超时兜底；GUI 走顺序采集，
                # 该值不生效（保留是为了与 config.yaml 的 collect.timeout 保持一致）。
                manager.TIMEOUT = float(self._timeout)

            pending = self._categories or [c["name"] for c in manager.list_collectors()]
            self.started_categories.emit(list(pending))
            self.progress.emit(f"正在采集 {len(pending)} 个类别…")

            result: CollectResult = manager.collect(
                categories=self._categories,
                # GUI 用顺序采集：win32com 的动态分发有全局类型缓存，
                # 多线程并发做首次属性访问会互相等待（CLI 里偶发、GUI 必现）。
                # 顺序执行的另一个好处是能逐类回填界面。
                parallel=False,
                on_category=self._on_category,
            )
            if self.isInterruptionRequested():
                return
            self.collect_finished.emit(result)
        except Exception as exc:  # noqa: BLE001
            logger.exception("GUI 采集线程异常")
            self.error.emit(str(exc))

    def _on_category(self, name: str, data, elapsed: float) -> None:
        """采集调度线程内的回调 → 转成 Qt 信号（队列投递到界面线程）"""
        self.category_done.emit(name, data, elapsed)
