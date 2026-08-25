"""
tests/test_cli_resolve.py - CLI 类别解析逻辑测试
"""
from cli.app import resolve_categories
from config.settings import Settings


ALL = ["cpu", "gpu", "memory", "storage", "network", "audio"]


def test_all_returns_none(monkeypatch):
    monkeypatch.setattr("cli.app.ALL_CATEGORIES", ALL)
    assert resolve_categories(["all"], "") is None


def test_empty_returns_none(monkeypatch):
    monkeypatch.setattr("cli.app.ALL_CATEGORIES", ALL)
    assert resolve_categories([], "") is None


def test_specific_categories(monkeypatch):
    monkeypatch.setattr("cli.app.ALL_CATEGORIES", ALL)
    assert resolve_categories(["cpu", "gpu"], "") == ["cpu", "gpu"]


def test_invalid_categories_filtered(monkeypatch):
    monkeypatch.setattr("cli.app.ALL_CATEGORIES", ALL)
    assert resolve_categories(["cpu", "foo"], "") == ["cpu"]


def test_hide_filters_all_category(monkeypatch):
    monkeypatch.setattr("cli.app.ALL_CATEGORIES", ALL)
    result = resolve_categories(["all"], "audio,os")
    assert "audio" not in result and "os" not in result
    assert "cpu" in result


def test_specified_but_hidden_returns_empty(monkeypatch):
    """指定类别全部被隐藏时应返回空列表而非回退全量采集"""
    monkeypatch.setattr("cli.app.ALL_CATEGORIES", ALL)
    assert resolve_categories(["audio"], "audio") == []


def test_case_and_whitespace_normalized(monkeypatch):
    monkeypatch.setattr("cli.app.ALL_CATEGORIES", ALL)
    assert resolve_categories([" CPU ", "GPU"], "") == ["cpu", "gpu"]


def test_settings_disabled_excluded(monkeypatch):
    monkeypatch.setattr("cli.app.ALL_CATEGORIES", ALL)

    settings = Settings.__new__(Settings)  # 跳过文件加载
    settings._config = {"display": {cat: (cat != "gpu") for cat in ALL}}

    result = resolve_categories(["all"], "", settings)
    assert "gpu" not in result
