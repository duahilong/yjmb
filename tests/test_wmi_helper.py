"""
tests/test_wmi_helper.py - WMI 日期解析测试（纯逻辑部分）
"""
import pytest
from utils.wmi_helper import parse_wmi_datetime, parse_wmi_date_only


class TestParseWmiDatetime:
    def test_full_datetime(self):
        result = parse_wmi_datetime("20240315102030.123456+480")
        assert result == "2024-03-15 10:20:30"

    def test_date_with_stars(self):
        """只有日期部分有效，时间部分为星号"""
        result = parse_wmi_datetime("20240926******.******+***")
        assert result == "2024-09-26"

    def test_date_only_8chars(self):
        result = parse_wmi_datetime("20250101")
        assert result == "2025-01-01"

    def test_none_input(self):
        assert parse_wmi_datetime(None) is None

    def test_empty_string(self):
        assert parse_wmi_datetime("") is None

    def test_short_string(self):
        """短于8位的字符串原样返回"""
        result = parse_wmi_datetime("2024")
        assert result == "2024"

    def test_zero_padded(self):
        result = parse_wmi_datetime("20250301080509.000000+480")
        assert result == "2025-03-01 08:05:09"


class TestParseWmiDateOnly:
    def test_full_datetime_returns_date(self):
        result = parse_wmi_date_only("20240315102030.123456+480")
        assert result == "2024-03-15"

    def test_date_only(self):
        result = parse_wmi_date_only("20240926******.******+***")
        assert result == "2024-09-26"

    def test_none(self):
        assert parse_wmi_date_only(None) is None

    def test_short_returns_as_is(self):
        """短字符串无法截取10位，返回原值"""
        result = parse_wmi_date_only("2024")
        assert result == "2024"
