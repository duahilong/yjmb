"""
tests/test_json_fmt.py - JSON 格式化器测试
"""
import json
import pytest
from core.manager import CollectResult
from formatters.json_fmt import JsonFormatter


@pytest.fixture
def formatter():
    return JsonFormatter()


class TestJsonFormatter:
    def test_valid_json_output(self, formatter, sample_collect_result):
        output = formatter.render(sample_collect_result)
        parsed = json.loads(output)
        assert "_元信息" in parsed

    def test_meta_info(self, formatter, sample_collect_result):
        output = formatter.render(sample_collect_result)
        parsed = json.loads(output)
        meta = parsed["_元信息"]
        assert meta["工具版本"] == "0.1.0"
        assert meta["耗时_秒"] == 1.23
        assert meta["错误数"] == 0
        assert meta["警告数"] == 0

    def test_data_present(self, formatter, sample_collect_result):
        output = formatter.render(sample_collect_result)
        parsed = json.loads(output)
        assert "cpu" in parsed
        assert "storage" in parsed
        assert parsed["cpu"]["名称"] == "Intel(R) Core(TM) i7-13700K"

    def test_brief_mode_filters_fields(self, formatter, sample_collect_result):
        output = formatter.render(sample_collect_result, brief=True)
        parsed = json.loads(output)
        cpu = parsed["cpu"]
        # brief 模式只保留 BRIEF_FIELDS_MAP 中的字段
        assert "名称" in cpu
        assert "核心数" in cpu
        assert "当前负载_百分比" not in cpu
        assert "指令集" not in cpu

    def test_errors_included(self, formatter):
        result = CollectResult(
            data={"cpu": {"名称": "test"}},
            errors=[{"模块": "gpu", "错误": "失败"}],
            warnings=["某警告"],
            elapsed_seconds=0.5,
        )
        output = formatter.render(result)
        parsed = json.loads(output)
        assert "_错误" in parsed
        assert "_警告" in parsed
        assert parsed["_错误"][0]["模块"] == "gpu"

    def test_no_errors_key_when_empty(self, formatter, sample_collect_result):
        output = formatter.render(sample_collect_result)
        parsed = json.loads(output)
        assert "_错误" not in parsed
        assert "_警告" not in parsed

    def test_ensure_ascii_false(self, formatter, sample_collect_result):
        """中文不应被转义"""
        output = formatter.render(sample_collect_result)
        assert "处理器" not in output or True  # 中文直接输出
        assert "\\u" not in output  # 无 unicode 转义

    def test_ordering(self, formatter):
        """输出应按 ORDER_MAP 排序"""
        result = CollectResult(
            data={
                "monitor": {"型号": "test"},
                "cpu": {"名称": "test"},
                "os": {"系统名称": "test"},
            },
            elapsed_seconds=0.1,
        )
        output = formatter.render(result)
        # os 应在 cpu 前面，cpu 应在 monitor 前面
        os_pos = output.index('"os"')
        cpu_pos = output.index('"cpu"')
        mon_pos = output.index('"monitor"')
        assert os_pos < cpu_pos < mon_pos
