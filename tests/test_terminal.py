"""
tests/test_terminal.py - 终端格式化器测试
"""
import pytest
from core.manager import CollectResult
from formatters.terminal import TerminalFormatter


@pytest.fixture
def formatter():
    """无颜色、无 Unicode 的格式化器（方便断言）"""
    return TerminalFormatter(use_color=False, use_unicode=False)


@pytest.fixture
def unicode_formatter():
    """Unicode 格式化器"""
    return TerminalFormatter(use_color=False, use_unicode=True)


class TestTerminalFormatter:
    def test_render_contains_header(self, formatter, sample_collect_result):
        output = formatter.render(sample_collect_result)
        assert "HWInfo" in output
        assert "v0.1.0" in output

    def test_render_contains_section(self, formatter, sample_collect_result):
        output = formatter.render(sample_collect_result)
        assert "处理器" in output  # cpu 的 label

    def test_render_contains_data(self, formatter, sample_collect_result):
        output = formatter.render(sample_collect_result)
        assert "Intel(R) Core(TM) i7-13700K" in output
        assert "Samsung SSD 980 PRO 1TB" in output

    def test_render_footer(self, formatter, sample_collect_result):
        output = formatter.render(sample_collect_result)
        assert "采集完成" in output
        assert "1.23s" in output
        assert "0 错误" in output

    def test_brief_mode(self, formatter, sample_collect_result):
        output = formatter.render(sample_collect_result, brief=True)
        # brief 模式应包含关键字段
        assert "Intel(R) Core(TM) i7-13700K" in output
        # 不应包含非关键字段
        assert "指令集" not in output

    def test_none_value_shows_unknown(self, formatter):
        result = CollectResult(
            data={"cpu": {"名称": "test", "虚拟化": None}},
            elapsed_seconds=0.1,
        )
        output = formatter.render(result)
        assert "未知" in output

    def test_bool_value(self, formatter):
        result = CollectResult(
            data={"motherboard": {"UEFI": True}},
            elapsed_seconds=0.1,
        )
        output = formatter.render(result)
        assert "是" in output

    def test_list_value(self, formatter):
        result = CollectResult(
            data={"cpu": {"指令集": ["SSE", "SSE2", "AVX"]}},
            elapsed_seconds=0.1,
        )
        output = formatter.render(result)
        assert "SSE, SSE2, AVX" in output

    def test_errors_displayed(self, formatter):
        result = CollectResult(
            data={},
            errors=[{"模块": "gpu", "错误": "驱动异常"}],
            elapsed_seconds=0.1,
        )
        output = formatter.render(result)
        assert "gpu" in output
        assert "驱动异常" in output

    def test_warnings_displayed(self, formatter):
        result = CollectResult(
            data={"cpu": {"名称": "test"}},
            warnings=["温度需管理员权限"],
            elapsed_seconds=0.1,
        )
        output = formatter.render(result)
        assert "温度需管理员权限" in output


class TestTerminalUnicode:
    def test_unicode_box(self, unicode_formatter, sample_collect_result):
        output = unicode_formatter.render(sample_collect_result)
        assert "╔" in output
        assert "╝" in output

    def test_ascii_fallback(self, formatter, sample_collect_result):
        output = formatter.render(sample_collect_result)
        assert "+" in output
        assert "=" in output
        assert "╔" not in output


class TestDisplayWidth:
    def test_ascii(self):
        assert TerminalFormatter._display_width("hello") == 5

    def test_chinese(self):
        assert TerminalFormatter._display_width("你好") == 4

    def test_mixed(self):
        assert TerminalFormatter._display_width("hi你好") == 6
