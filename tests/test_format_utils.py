"""
tests/test_format_utils.py - 单位换算与格式化工具测试
"""
import pytest
from utils.format_utils import (
    bytes_to_gb, bytes_to_mb, kb_to_mb, bps_to_gbps,
    millivolts_to_volts, format_size,
)


class TestBytesToGb:
    def test_1gb(self):
        assert bytes_to_gb(1024 ** 3) == 1.0

    def test_500gb(self):
        assert bytes_to_gb(500 * 1024 ** 3) == 500.0

    def test_fractional(self):
        # 1.5 GB
        assert bytes_to_gb(int(1.5 * 1024 ** 3)) == 1.5

    def test_none(self):
        assert bytes_to_gb(None) is None

    def test_zero(self):
        assert bytes_to_gb(0) == 0.0


class TestBytesToMb:
    def test_1mb(self):
        assert bytes_to_mb(1024 ** 2) == 1

    def test_11264mb(self):
        # RTX 2080 Ti 显存
        assert bytes_to_mb(11264 * 1024 ** 2) == 11264

    def test_none(self):
        assert bytes_to_mb(None) is None


class TestKbToMb:
    def test_32mb(self):
        assert kb_to_mb(32 * 1024) == 32

    def test_rounding(self):
        assert kb_to_mb(1536) == 2  # 1.5 MB → 2

    def test_none(self):
        assert kb_to_mb(None) is None


class TestBpsToGbps:
    def test_1gbps(self):
        assert bps_to_gbps(1_000_000_000) == 1.0

    def test_2_5gbps(self):
        assert bps_to_gbps(2_500_000_000) == 2.5

    def test_100mbps(self):
        assert bps_to_gbps(100_000_000) == 0.1

    def test_none(self):
        assert bps_to_gbps(None) is None


class TestMillivoltsToVolts:
    def test_1350mv(self):
        assert millivolts_to_volts(1350) == 1.35

    def test_1200mv(self):
        assert millivolts_to_volts(1200) == 1.2

    def test_none(self):
        assert millivolts_to_volts(None) is None


class TestFormatSize:
    def test_gb(self):
        assert format_size(500.0) == "500.0 GB"

    def test_tb(self):
        assert format_size(2048.0) == "2.0 TB"

    def test_none(self):
        assert format_size(None) == "未知"

    def test_boundary(self):
        assert format_size(1024.0) == "1.0 TB"
