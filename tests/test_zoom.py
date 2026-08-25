"""
tests/test_zoom.py - 界面缩放纯函数测试
"""
from gui.zoom import scale_qss, scaled, set_zoom, get_zoom


class TestScaleQss:
    def test_scale_px_values(self):
        qss = "QWidget { font-size: 12px; padding: 8px; }"
        result = scale_qss(qss, 1.5)
        assert "18px" in result
        assert "12px" in result  # 8*1.5 = 12

    def test_zoom_100_returns_original(self):
        qss = "font-size: 14px; margin: 2px;"
        assert scale_qss(qss, 1.0) == qss

    def test_fractional_px_rounds(self):
        assert "10px" in scale_qss("font-size: 7px;", 1.4)  # 9.8 → 10

    def test_non_px_numbers_untouched(self):
        qss = "color: #FF0000; border-radius: 50%;"
        assert scale_qss(qss, 1.5) == qss

    def test_decimal_px_value(self):
        # 1.5px * 2.0 = 3px（小数 px 值也参与缩放）
        assert "3px" in scale_qss("margin: 1.5px;", 2.0)

    def test_default_zoom_used_when_none(self):
        set_zoom(2.0)
        try:
            assert "20px" in scale_qss("width: 10px;")
        finally:
            set_zoom(1.0)


class TestScaled:
    def test_scales_value(self):
        set_zoom(1.2)
        try:
            assert scaled(100) == 120
        finally:
            set_zoom(1.0)

    def test_minimum_one(self):
        set_zoom(0.7)
        try:
            assert scaled(1) == 1  # round(0.7) = 1，避免尺寸归零
        finally:
            set_zoom(1.0)
