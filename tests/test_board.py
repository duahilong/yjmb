"""
tests/test_board.py - 画板数据模型与格式化

不创建窗口，只验证从采集结果到「类别 / 设备 / 字段行」的转换口径：
键名拆分、单位、千分位、布尔、状态上色、精简白名单与搜索。
"""
import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

pytest.importorskip("PySide6")

from gui.board import (  # noqa: E402
    build_items, build_model, count_fields, filter_units, format_value,
    split_key,
)


DATA = {
    "os": {
        "系统名称": "Microsoft Windows 11 专业工作站版",
        "版本号": "10.0.26300",
        "系统架构": "64 位",
        "系统目录": "C:\\WINDOWS",
        "用户名": "tester",
    },
    "cpu": {
        "名称": "Genuine Intel(R) 0000",
        "厂商": "GenuineIntel",
        "核心数": 24,
        "线程数": 32,
        "基础频率_MHz": 1690,
        "L2缓存_MB": 32,
        "指令集": ["SSE", "AVX2"],
        "虚拟化": True,
    },
    "motherboard": {
        "厂商": "Micro-Star International Co., Ltd.",
        "型号": "Z790MPOWER",
        "BIOS_版本": "P.60",
        "UEFI": True,
        "TPM": "已检测到 (v2.0)",
    },
    "memory": {
        "总容量_GB": 32.0,
        "通道模式": "双通道",
        "内存条": [
            {"插槽": "Controller0-DIMMA1", "厂商": "Golden Empire",
             "容量_GB": 16.0, "频率_MHz": 7200, "序列号": "16011049"},
        ],
    },
    "gpu": {
        "显卡列表": [
            {"类型": "独显", "名称": "NVIDIA GeForce RTX 2080 Ti", "厂商": "NVIDIA",
             "显存_MB": 11264, "状态": "正常"},
            {"类型": "核显", "名称": "Intel(R) UHD Graphics", "厂商": "Intel",
             "显存_MB": 2048},
        ],
    },
    "storage": {
        "磁盘列表": [
            {"型号": "GXF-512 PRO", "类型": "SSD", "接口": "NVMe",
             "容量_GB": 476.9, "固件": "SN08193", "序列号": "0000",
             "分区": [
                 {"盘符": "C:", "标签": "系统", "文件系统": "NTFS",
                  "已用_GB": 100.0, "总计_GB": 476.9},
             ]},
        ],
    },
    "network": {
        "网卡列表": [
            {"名称": "Realtek 2.5GbE", "类型": "以太网", "厂商": "Realtek",
             "MAC": "D8:43:AE:8B:1A:01", "状态": "已连接", "速率_Gbps": 1.0},
            {"名称": "Wi-Fi 6E", "类型": "无线", "厂商": "Intel",
             "MAC": "8C:E9:EE:1B:4E:E6", "状态": "媒体断开"},
        ],
    },
    "audio": {
        "音频设备列表": [
            {"名称": "Realtek High Definition Audio", "位置": "板载",
             "厂商": "Realtek", "状态": "正常"},
        ],
    },
    "monitor": {
        "显示器列表": [
            {"型号": "G322U", "厂商": "GTR", "分辨率": "3840×2160",
             "刷新率_Hz": 120, "状态": "活动"},
            {"型号": "DELL SE2416H", "厂商": "DELL", "分辨率": "1920×1080",
             "刷新率_Hz": 60, "状态": "未连接"},
        ],
    },
}


class TestFormat:
    def test_split_key_with_unit(self):
        assert split_key("基础频率_MHz") == ("基础频率", "MHz")
        assert split_key("L2缓存_MB") == ("L2 缓存", "MB")
        assert split_key("刷新率_Hz") == ("刷新率", "Hz")

    def test_split_key_without_unit(self):
        assert split_key("BIOS_版本") == ("BIOS 版本", None)
        assert split_key("通道模式") == ("通道模式", None)

    def test_numbers_keep_original_unit(self):
        assert format_value("基础频率_MHz", 1690) == ("1,690 MHz", "")
        assert format_value("显存_MB", 11264) == ("11,264 MB", "")
        assert format_value("总容量_GB", 47.7) == ("47.7 GB", "")
        assert format_value("使用率_百分比", 47.2) == ("47.2%", "")

    def test_bool_and_missing(self):
        assert format_value("UEFI", True) == ("支持", "")
        assert format_value("虚拟化", False) == ("不支持", "no")
        assert format_value("TPM", None) == ("—", "null")

    def test_list_joined(self):
        assert format_value("指令集", ["SSE", "AVX2"])[0] == "SSE · AVX2"

    def test_status_tone(self):
        assert format_value("状态", "已连接") == ("已连接", "ok")
        assert format_value("状态", "媒体断开") == ("媒体断开", "off")
        assert format_value("状态", "未知") == ("未知", "neutral")

    def test_year_is_not_thousands_separated(self):
        assert format_value("制造年份", 2023) == ("2023", "")
        assert format_value("核心数", 24) == ("24", "")


class TestModel:
    def test_category_order(self):
        units = build_model(DATA, "brief")
        names = []
        for unit in units:
            if unit.cat.name not in names:
                names.append(unit.cat.name)
        assert names == ["操作系统", "处理器", "主板", "内存", "显卡",
                         "存储", "网络", "音频", "显示器"]

    def test_brief_network_only_connected(self):
        brief = build_model(DATA, "brief")
        net = [u for u in brief if u.cat.key == "network"]
        assert len(net) == 1
        assert net[0].dev.name == "Realtek 2.5GbE"
        assert net[0].cat.meta == "1 / 2 已连接"

        full = build_model(DATA, "all")
        net_all = [u for u in full if u.cat.key == "network"]
        assert len(net_all) == 2
        assert net_all[0].cat.meta == "2 个 · 1 已连接"

    def test_memory_sticks_are_devices(self):
        units = build_model(DATA, "brief")
        memory = [u for u in units if u.cat.key == "memory"]
        sticks = [u for u in memory if u.dev]
        assert len(sticks) == 1
        assert sticks[0].dev.name == "内存条 1"
        assert sticks[0].dev.meta == "Controller0-DIMMA1"
        labels = {row.label for row in sticks[0].rows}
        assert "序列号" in labels
        assert "插槽" not in labels

    def test_storage_partition_is_nested_device(self):
        units = build_model(DATA, "brief")
        parts = [u for u in units if u.dev and u.dev.part]
        assert len(parts) == 1
        assert parts[0].dev.name == "C: 系统"
        assert parts[0].dev.meta == "NTFS"
        assert {row.label for row in parts[0].rows} == {"已用", "总计"}

    def test_monitor_tone_and_order(self):
        units = build_model(DATA, "brief")
        monitors = [u for u in units if u.cat.key == "monitor"]
        assert monitors[0].dev.name == "G322U"
        assert monitors[0].dev.tone == "ok"
        assert monitors[1].dev.tone == "off"
        assert monitors[0].cat.meta == "2 台 · 1 活动"

    def test_all_has_more_fields_than_brief(self):
        brief = build_model(DATA, "brief")
        full = build_model(DATA, "all")
        assert count_fields(full) > count_fields(brief)
        assert len(build_items(full)) > len(build_items(brief))

    def test_search_by_device_and_row(self):
        units = build_model(DATA, "brief")
        by_dev = filter_units(units, "RTX")
        assert [u.dev.name for u in by_dev if u.dev] == ["NVIDIA GeForce RTX 2080 Ti"]
        by_row = filter_units(units, "GXF")
        assert by_row and by_row[0].dev.name == "GXF-512 PRO"
        assert filter_units(units, "不存在的词") == []

    def test_search_marks_match_count(self):
        units = build_model(DATA, "brief")
        hits = filter_units(units, "Genuine")
        assert hits
        assert hits[0].cat.meta == "1 个匹配"


class TestFilterWhitelist:
    def test_brief_drops_dynamic_fields(self):
        units = build_model(DATA, "brief")
        os_rows = [row.label for unit in units if unit.cat.key == "os" for row in unit.rows]
        assert "系统目录" not in os_rows
        assert "用户名" in os_rows

        cpu = [u for u in units if u.cat.key == "cpu"][0]
        cpu_labels = {row.label for row in cpu.rows}
        assert "厂商" not in cpu_labels
        assert "指令集" not in cpu_labels
        assert "架构" not in cpu_labels
        assert "名称" in cpu_labels
        assert "虚拟化" in cpu_labels

    def test_all_keeps_dynamic_fields(self):
        units = build_model(DATA, "all")
        cpu = [u for u in units if u.cat.key == "cpu"][0]
        cpu_labels = {row.label for row in cpu.rows}
        assert "指令集" in cpu_labels
        assert "厂商" in cpu_labels
