"""
core/manager.py - CollectorManager 采集调度中心
"""
import time
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError as FuturesTimeoutError

from core.base import BaseCollector, CollectorError
from utils.logger import get_logger

logger = get_logger(__name__)

# 模块级共享线程池（进程内复用，避免每次采集新建线程）。
# 注意：Python 3.9+ 的 ThreadPoolExecutor 工作线程是非 daemon 的，
# 解释器正常退出时会 join 全部线程。极端情况下若某个 WMI COM 调用
# 无限阻塞，可能延迟进程退出（本模块的采集等待已有整体超时兜底，
# 只是放弃等待后该工作线程仍在后台占用）。GUI 强制结束进程不受影响。
_executor: ThreadPoolExecutor | None = None


def _get_shared_executor(max_workers: int) -> ThreadPoolExecutor:
    """获取全局共享线程池（首次创建后复用）"""
    global _executor
    if _executor is None:
        _executor = ThreadPoolExecutor(
            max_workers=max_workers, thread_name_prefix="hwinfo-collect"
        )
    return _executor


@dataclass
class CollectResult:
    """采集结果汇总"""
    data: dict = field(default_factory=dict)          # {"cpu": {...}, "gpu": {...}}
    errors: list[dict] = field(default_factory=list)  # [{"模块": "cpu", "错误": "..."}]
    warnings: list[str] = field(default_factory=list)  # ["磁盘SMART需管理员权限"]
    elapsed_seconds: float = 0.0                      # 总耗时
    timings: dict = field(default_factory=dict)       # {"cpu": 0.35, "gpu": 1.2} 每模块耗时


class CollectorManager:
    """采集调度中心"""

    TIMEOUT = 10  # 单模块超时秒数

    def __init__(self):
        self._collectors: dict[str, BaseCollector] = {}

    def register(self, collector: BaseCollector) -> None:
        """注册一个 Collector 实例"""
        self._collectors[collector.name] = collector

    def collect(
        self,
        categories: list[str] | None = None,
        exclude: list[str] | None = None,
        parallel: bool = True,
        on_category: callable = None,
    ) -> CollectResult:
        """
        执行采集。

        Args:
            categories: 要采集的类别列表。None 表示全部。
            exclude: 要排除的类别列表。
            parallel: 是否并行采集。
            on_category: 可选进度回调，每完成一个类别就调用一次，
                         签名为 (name, data | None, elapsed_seconds)。
                         data 为 None 表示该类别采集失败。GUI 用它做渐进填充。

        Returns:
            CollectResult 包含数据、错误、警告、耗时。
        """
        start = time.perf_counter()

        # 筛选要执行的 collectors
        targets = self._filter_collectors(categories, exclude)

        result = CollectResult()

        if not targets:
            result.elapsed_seconds = round(time.perf_counter() - start, 2)
            return result

        if parallel and len(targets) > 1:
            self._collect_parallel(targets, result, on_category)
        else:
            self._collect_sequential(targets, result, on_category)

        # 从各模块数据中提取 _警告
        for name, data in result.data.items():
            if isinstance(data, dict) and "_警告" in data:
                warnings = data.pop("_警告")
                if isinstance(warnings, list):
                    result.warnings.extend(warnings)
                elif isinstance(warnings, str):
                    result.warnings.append(warnings)

        result.elapsed_seconds = round(time.perf_counter() - start, 2)
        return result

    def _collect_parallel(self, targets: list[BaseCollector], result: CollectResult,
                          on_category: callable = None) -> None:
        """并行采集"""
        def _run_collector(collector: BaseCollector) -> tuple[dict, float]:
            """在工作线程中执行采集，完成后清理 COM"""
            t0 = time.perf_counter()
            try:
                data = collector.collect()
                return data, round(time.perf_counter() - t0, 3)
            finally:
                from utils.wmi_helper import cleanup_com
                cleanup_com()

        executor = _get_shared_executor(len(targets))
        future_map = {
            executor.submit(_run_collector, collector): collector
            for collector in targets
        }

        try:
            # as_completed 的 timeout 是整体兜底：WMI COM 调用可能无限阻塞，
            # 超时后放弃等待，未完成模块由外层 except 标记为超时。
            # 注意：as_completed 只产出已完成的 future，
            # 因此 future.result() 不会超时，无需再传 timeout。
            for future in as_completed(future_map, timeout=self.TIMEOUT + 5):
                collector = future_map[future]
                try:
                    data, elapsed = future.result()
                    result.data[collector.name] = data
                    result.timings[collector.name] = elapsed
                    if on_category:
                        on_category(collector.name, data, elapsed)
                except CollectorError as e:
                    result.errors.append({"模块": collector.name, "错误": str(e)})
                    logger.warning("模块 %s 采集失败: %s", collector.name, e)
                    if on_category:
                        on_category(collector.name, None, result.timings.get(collector.name, 0.0))
                except Exception as e:
                    result.errors.append({"模块": collector.name, "错误": f"未知错误: {e}"})
                    logger.exception("模块 %s 采集异常", collector.name)
                    if on_category:
                        on_category(collector.name, None, result.timings.get(collector.name, 0.0))
        except FuturesTimeoutError:
            # as_completed 总超时兜底：WMI COM 调用可能无限阻塞，
            # 整体超时后将未完成模块标记为超时，避免整个采集抛异常
            logger.error("并行采集整体超时(%ss)，未完成模块标记为超时", self.TIMEOUT + 5)
            for collector in future_map.values():
                if collector.name not in result.data:
                    result.errors.append({"模块": collector.name, "错误": "采集超时"})
                    result.timings[collector.name] = self.TIMEOUT
                    if on_category:
                        on_category(collector.name, None, float(self.TIMEOUT))

    def _collect_sequential(self, targets: list[BaseCollector], result: CollectResult,
                            on_category: callable = None) -> None:
        """顺序采集（调试用）"""
        for collector in targets:
            t0 = time.perf_counter()
            try:
                data = collector.collect()
                elapsed = round(time.perf_counter() - t0, 3)
                result.data[collector.name] = data
                result.timings[collector.name] = elapsed
                if on_category:
                    on_category(collector.name, data, elapsed)
            except CollectorError as e:
                result.errors.append({"模块": collector.name, "错误": str(e)})
                result.timings[collector.name] = round(time.perf_counter() - t0, 3)
                logger.warning("模块 %s 采集失败: %s", collector.name, e)
                if on_category:
                    on_category(collector.name, None, result.timings[collector.name])
            except Exception as e:
                result.errors.append({"模块": collector.name, "错误": f"未知错误: {e}"})
                result.timings[collector.name] = round(time.perf_counter() - t0, 3)
                logger.exception("模块 %s 采集异常", collector.name)
                if on_category:
                    on_category(collector.name, None, result.timings[collector.name])

    def _filter_collectors(
        self,
        categories: list[str] | None,
        exclude: list[str] | None,
    ) -> list[BaseCollector]:
        """根据类别和排除列表筛选 Collector"""
        collectors = list(self._collectors.values())

        # 按类别筛选
        if categories:
            collectors = [c for c in collectors if c.name in categories]

        # 排除
        if exclude:
            collectors = [c for c in collectors if c.name not in exclude]

        # 按 order 排序
        return sorted(collectors, key=lambda c: c.order)

    def list_collectors(self) -> list[dict]:
        """返回所有已注册 Collector 的 name 和 label"""
        return [
            {"name": c.name, "label": c.label, "order": c.order}
            for c in sorted(self._collectors.values(), key=lambda x: x.order)
        ]
