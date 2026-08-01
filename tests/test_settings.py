"""
tests/test_settings.py - 配置系统测试
"""
import os
import pytest
from config.settings import Settings


class TestSettingsDefault:
    """测试默认配置加载"""

    def test_load_default(self):
        s = Settings()
        # 默认所有类别启用
        assert s.is_display_enabled("cpu") is True
        assert s.is_display_enabled("gpu") is True

    def test_default_color_mode(self):
        s = Settings()
        assert s.get_color_mode() == "auto"

    def test_default_unicode_mode(self):
        s = Settings()
        assert s.get_unicode_mode() == "auto"

    def test_default_timeout(self):
        s = Settings()
        assert s.get_timeout() == 10

    def test_default_parallel(self):
        s = Settings()
        assert s.is_parallel() is True


class TestSettingsUserConfig:
    """测试用户配置覆盖"""

    def test_override_display(self, tmp_path):
        config_file = tmp_path / "config.yaml"
        config_file.write_text(
            "display:\n  gpu: false\n", encoding="utf-8"
        )
        s = Settings(config_path=str(config_file))
        assert s.is_display_enabled("gpu") is False
        assert s.is_display_enabled("cpu") is True  # 未覆盖的保持默认

    def test_override_timeout(self, tmp_path):
        config_file = tmp_path / "config.yaml"
        config_file.write_text(
            "collect:\n  timeout: 30\n", encoding="utf-8"
        )
        s = Settings(config_path=str(config_file))
        assert s.get_timeout() == 30

    def test_override_color(self, tmp_path):
        config_file = tmp_path / "config.yaml"
        config_file.write_text(
            "output:\n  color: never\n", encoding="utf-8"
        )
        s = Settings(config_path=str(config_file))
        assert s.get_color_mode() == "never"

    def test_nonexistent_config(self, tmp_path):
        """不存在的配置文件不应报错"""
        s = Settings(config_path=str(tmp_path / "no_such.yaml"))
        assert s.get_timeout() == 10  # 回退到默认

    def test_invalid_yaml(self, tmp_path):
        """无效 YAML 不应崩溃"""
        config_file = tmp_path / "bad.yaml"
        config_file.write_text("{{{{invalid yaml", encoding="utf-8")
        s = Settings(config_path=str(config_file))
        assert s.get_timeout() == 10


class TestSettingsCliOverrides:
    """测试 CLI 参数覆盖"""

    def test_no_color_override(self):
        s = Settings()

        class FakeArgs:
            no_color = True

        s.apply_cli_overrides(FakeArgs())
        assert s.get_color_mode() == "never"

    def test_no_override_when_false(self):
        s = Settings()

        class FakeArgs:
            no_color = False

        s.apply_cli_overrides(FakeArgs())
        assert s.get_color_mode() == "auto"


class TestSettingsMerge:
    """测试递归合并逻辑"""

    def test_deep_merge(self):
        s = Settings()
        base = {"a": {"b": 1, "c": 2}, "d": 3}
        override = {"a": {"b": 99}, "e": 5}
        s._merge(base, override)
        assert base["a"]["b"] == 99
        assert base["a"]["c"] == 2  # 未被覆盖
        assert base["d"] == 3
        assert base["e"] == 5
