"""
tests/test_gui_integration.py - GUI 与采集调度的集成测试

使用离屏 Qt + 假采集器验证：
MainWindow → CollectWorker(QThread) → CollectorManager → 画板回填 → 二次刷新
不依赖真实硬件，避免 CI 环境不稳定。
"""
import json
import os
import time

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

pytest.importorskip("PySide6")

from core.base import BaseCollector


class FakeCollector(BaseCollector):
    """返回固定数据的采集器，用于验证 GUI 信号链路。"""

    def __init__(self, name: str, label: str, order: int, data: dict):
        self.name = name
        self.label = label
        self.order = order
        self._data = data

    def collect(self) -> dict:
        time.sleep(0.01)
        return dict(self._data)


@pytest.fixture(scope="module")
def qapp():
    from PySide6.QtWidgets import QApplication

    app = QApplication.instance() or QApplication([])
    app.setStyle("Fusion")
    return app


def _wait_for_result(window, app, timeout: float = 5.0):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        app.processEvents()
        if window._result is not None and window._worker is None:
            return window._result
        time.sleep(0.005)
    raise AssertionError("等待 GUI 采集结果超时")


def test_main_window_backend_integration(
    qapp, monkeypatch, tmp_path, sample_cpu_data, sample_storage_data
):
    from gui import theme
    from gui.main_window import MainWindow

    enabled = ["cpu", "storage"]
    monkeypatch.setattr(
        "gui.main_window.prefs.enabled_categories", lambda: list(enabled)
    )
    monkeypatch.setattr(
        "core.registry.get_all_collectors",
        lambda: [
            FakeCollector("cpu", "处理器", 10, sample_cpu_data),
            FakeCollector("storage", "存储设备", 60, sample_storage_data),
        ],
    )
    qapp.setStyleSheet(theme.build_qss())

    from gui.icons import app_icon, app_icon_path

    assert os.path.isfile(app_icon_path())
    icon = app_icon()
    assert not icon.isNull()
    icon_sizes = {(size.width(), size.height()) for size in icon.availableSizes()}
    assert (16, 16) in icon_sizes
    assert (256, 256) in icon_sizes

    window = MainWindow(auto_collect=False)
    try:
        assert not window.windowIcon().isNull()
        window.start_collect()
        result = _wait_for_result(window, qapp)

        assert result.errors == []
        assert set(result.data) == set(enabled)
        assert window._status.text() == "完成 2/2"

        overview = window._pages["overview"]
        board = overview.board
        visible, mode_fields, all_fields = board.counts()
        assert visible == mode_fields > 0
        assert all_fields >= mode_fields

        # 关键字段确实进了画板（不是空壳）
        labels = {row.label for unit in board._units for row in unit.rows}
        assert "名称" in labels
        assert "容量" in labels or "序列号" in labels

        # 全部 / 精简切换
        window._set_mode("all")
        qapp.processEvents()
        assert board.mode() == "all"
        _, mode_all, all_all = board.counts()
        assert mode_all == all_all
        assert mode_all >= mode_fields
        window._set_mode("brief")
        qapp.processEvents()
        assert board.mode() == "brief"

        # 标签开关
        window._labels_btn.setChecked(False)
        qapp.processEvents()
        assert board.labels() is False
        window._labels_btn.setChecked(True)
        qapp.processEvents()
        assert board.labels() is True

        # 搜索：命中数与计数文案（精简档 cpu 保留「名称」）
        window._search.setText("13700K")
        qapp.processEvents()
        assert board.query() == "13700K"
        hit, total, _ = board.counts()
        assert 0 < hit < total
        assert window._count.text().startswith("命中 ")
        window._search.clear()
        qapp.processEvents()
        assert board.query() == ""

        # 布局：自适应字号与栏数在合理范围内
        window.resize(1440, 900)
        window.show()
        qapp.processEvents()
        metrics = board.layout_metrics()
        assert 8 <= metrics["font"] <= 40
        assert 1 <= metrics["cols"] <= 6
        assert metrics["rows"] > 0

        # 导出：验证 UI 读取 CollectResult 后写入完整 JSON
        export_path = tmp_path / "export.json"
        monkeypatch.setattr(
            "gui.main_window.QFileDialog.getSaveFileName",
            lambda *args, **kwargs: (str(export_path), "JSON 文件 (*.json)"),
        )
        window.export_json()
        payload = json.loads(export_path.read_text(encoding="utf-8"))
        assert set(payload["data"]) == set(enabled)
        assert payload["errors"] == []

        # 二次刷新：验证 QThread 可重复启动、画板继续接收新结果
        first_result = result
        window.start_collect()
        second_result = _wait_for_result(window, qapp)

        assert second_result is not first_result
        assert second_result.errors == []
        assert window._status.text() == "完成 2/2"
        assert board._data == second_result.data
    finally:
        window.close()
        qapp.processEvents()
