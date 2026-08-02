"""
gui/worker.py - 后台采集线程
"""
from PySide6.QtCore import QThread, Signal

from core.manager import CollectorManager, CollectResult


class CollectWorker(QThread):
    """后台硬件信息采集线程"""

    # 采集完成信号，携带 CollectResult
    finished = Signal(object)
    # 进度信号，携带当前状态文本
    progress = Signal(str)

    def __init__(self, categories: list[str] | None = None, parent=None):
        super().__init__(parent)
        self._categories = categories

    def run(self) -> None:
        """在工作线程中执行采集"""
        self.progress.emit("正在初始化采集...")

        # 加载所有 collector 模块（触发注册）
        import collectors
        collectors.load_all()

        from core.registry import get_all_collectors

        manager = CollectorManager()
        for c in get_all_collectors():
            manager.register(c)

        self.progress.emit("正在采集硬件信息...")

        result = manager.collect(
            categories=self._categories,
            parallel=True,
        )

        self.progress.emit(f"采集完成，耗时 {result.elapsed_seconds}s")
        self.finished.emit(result)
