"""
gui/pages/settings.py - 设置页（显示控制）
"""
import os

from PySide6.QtWidgets import (
    QLabel, QCheckBox, QVBoxLayout, QGroupBox, QPushButton, QHBoxLayout,
)
from PySide6.QtCore import Qt

from gui.pages.base_page import BasePage
from core.constants import ALL_CATEGORIES


# 类别中文名
CATEGORY_LABELS = {
    "os": "操作系统",
    "motherboard": "主板",
    "cpu": "处理器",
    "memory": "内存",
    "gpu": "显卡",
    "storage": "存储",
    "network": "网络",
    "audio": "音频",
    "monitor": "显示器",
}


class SettingsPage(BasePage):
    """设置页：控制各类别的显示/隐藏"""

    def __init__(self, parent=None):
        super().__init__(parent)

        title = QLabel("设置")
        title.setStyleSheet("font-size: 18px; font-weight: bold; margin-bottom: 8px;")
        self._layout.addWidget(title)

        # 显示控制分组
        group = QGroupBox("显示控制")
        group_layout = QVBoxLayout(group)

        self._checkboxes: dict[str, QCheckBox] = {}
        for cat in ALL_CATEGORIES:
            label = CATEGORY_LABELS.get(cat, cat)
            cb = QCheckBox(label)
            cb.setChecked(True)
            self._checkboxes[cat] = cb
            group_layout.addWidget(cb)

        self._layout.addWidget(group)

        # 按钮行
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("保存设置")
        save_btn.clicked.connect(self._save_settings)
        btn_layout.addWidget(save_btn)

        reset_btn = QPushButton("恢复默认")
        reset_btn.clicked.connect(self._reset_defaults)
        btn_layout.addWidget(reset_btn)

        btn_layout.addStretch()
        self._layout.addLayout(btn_layout)

        self._status_label = QLabel("")
        self._status_label.setStyleSheet("color: green; margin-top: 8px;")
        self._layout.addWidget(self._status_label)

        self._layout.addStretch()

        # 加载当前配置
        self._load_current()

    def update_data(self, data) -> None:
        """设置页不需要采集数据"""
        pass

    def _load_current(self) -> None:
        """从配置文件加载当前显示设置"""
        try:
            from config.settings import Settings
            settings = Settings()
            for cat, cb in self._checkboxes.items():
                cb.setChecked(settings.is_display_enabled(cat))
        except Exception:
            pass

    def _save_settings(self) -> None:
        """保存显示设置到 config.yaml"""
        try:
            import yaml

            # 构建 display 配置
            display_config = {}
            for cat, cb in self._checkboxes.items():
                display_config[cat] = cb.isChecked()

            # 读取现有配置或创建新的
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            config_path = os.path.join(project_root, "config.yaml")

            config = {}
            if os.path.exists(config_path):
                with open(config_path, "r", encoding="utf-8") as f:
                    config = yaml.safe_load(f) or {}

            config["display"] = display_config

            with open(config_path, "w", encoding="utf-8") as f:
                yaml.dump(config, f, allow_unicode=True, default_flow_style=False)

            self._status_label.setText("✓ 设置已保存")
        except Exception as e:
            self._status_label.setText(f"✗ 保存失败: {e}")
            self._status_label.setStyleSheet("color: red; margin-top: 8px;")

    def _reset_defaults(self) -> None:
        """恢复默认（全部显示）"""
        for cb in self._checkboxes.values():
            cb.setChecked(True)
        self._status_label.setText("已恢复默认（需点击保存生效）")
        self._status_label.setStyleSheet("color: green; margin-top: 8px;")
