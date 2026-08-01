"""
core/manager.py - CollectorManager 采集调度中心
"""
import time
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError as FuturesTimeoutError

from core.base import BaseCollector, CollectorError


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
    ) -> CollectResult:
        """
        执行采集。

        Args:
            categories: 要采集的类别列表。None 表示全部。
            exclude: 要排除的类别列表。
            parallel: 是否并行采集。

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
            self._collect_parallel(targets, result)
        else:
            self._collect_sequential(targets, result)

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

    def _collect_parallel(self, targets: list[BaseCollector], result: CollectResult) -> None:
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

        with ThreadPoolExecutor(max_workers=len(targets)) as executor:
            future_map = {
                executor.submit(_run_collector, collector): collector
                for collector in targets
            }

            for future in as_completed(future_map, timeout=self.TIMEOUT + 5):
                collector = future_map[future]
                try:
                    data, elapsed = future.result(timeout=self.TIMEOUT)
                    result.data[collector.name] = data
                    result.timings[collector.name] = elapsed
                except FuturesTimeoutError:
                    result.errors.append({"模块": collector.name, "错误": "采集超时"})
                    result.timings[collector.name] = self.TIMEOUT
                except CollectorError as e:
                    result.errors.append({"模块": collector.name, "错误": str(e)})
                except Exception as e:
                    result.errors.append({"模块": collector.name, "错误": f"未知错误: {e}"})

    def _collect_sequential(self, targets: list[BaseCollector], result: CollectResult) -> None:
        """顺序采集（调试用）"""
        for collector in targets:
            t0 = time.perf_counter()
            try:
                data = collector.collect()
                result.data[collector.name] = data
                result.timings[collector.name] = round(time.perf_counter() - t0, 3)
            except CollectorError as e:
                result.errors.append({"模块": collector.name, "错误": str(e)})
                result.timings[collector.name] = round(time.perf_counter() - t0, 3)
            except Exception as e:
                result.errors.append({"模块": collector.name, "错误": f"未知错误: {e}"})
                result.timings[collector.name] = round(time.perf_counter() - t0, 3)

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
