"""
gui/pages/settings.py - 设置页（显示控制）
"""
import os

from PySide6.QtWidgets import (
    QLabel, QCheckBox, QVBoxLayout, QGroupBox, QPushButton, QHBoxLayout,
)
from PySide6.QtCore import Qt, Signal

from gui.pages.base_page import BasePage
from core.constants import ALL_CATEGORIES, CATEGORY_LABELS


class SettingsPage(BasePage):
    """设置页：控制各类别的显示/隐藏"""

    # 设置保存成功信号（主窗口据此重建导航并重新采集）
    settings_saved = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        title = self._make_title("设置")

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
        self._status_label.setObjectName("statusLabel")
        self._status_label.setStyleSheet("color: green;")
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

            # 读取现有配置或创建新的（打包模式下写入 EXE 同目录，避免 _MEIPASS 临时目录丢失）
            from config.settings import get_user_config_path
            config_path = get_user_config_path()

            config = {}
            if os.path.exists(config_path):
                with open(config_path, "r", encoding="utf-8") as f:
                    config = yaml.safe_load(f) or {}

            config["display"] = display_config

            with open(config_path, "w", encoding="utf-8") as f:
                yaml.dump(config, f, allow_unicode=True, default_flow_style=False)

            self._status_label.setText("✓ 设置已保存")
            self._status_label.setStyleSheet("color: green;")
            self.settings_saved.emit()
        except Exception as e:
            self._status_label.setText(f"✗ 保存失败: {e}")
            self._status_label.setStyleSheet("color: red;")

    def _reset_defaults(self) -> None:
        """恢复默认（全部显示）"""
        for cb in self._checkboxes.values():
            cb.setChecked(True)
        self._status_label.setText("已恢复默认（需点击保存生效）")
        self._status_label.setStyleSheet("color: green;")
