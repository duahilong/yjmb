"""
gui/pages/settings.py - 设置对话框

显示类别与 CLI 共用 config.yaml 的 display 段；
窗口置顶与采集超时写入 gui / collect 段。
"""
from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QCheckBox, QDialog, QDialogButtonBox, QGridLayout, QHBoxLayout, QLabel,
    QPushButton, QSpinBox, QVBoxLayout, QWidget,
)

from core.constants import ALL_CATEGORIES, CATEGORY_LABELS
from gui import prefs, theme

# 每个类别在设置里的用途说明
DESCRIPTIONS = {
    "os": "版本、安装与启动时间",
    "motherboard": "芯片组与 BIOS",
    "cpu": "型号、核心与指令集",
    "memory": "容量、频率与插槽",
    "gpu": "显卡、显存与驱动",
    "storage": "磁盘、分区与占用",
    "network": "网卡、IP 与速率",
    "audio": "输出设备与驱动",
    "monitor": "型号、分辨率与刷新率",
}


class SettingsDialog(QDialog):
    """类别开关 + 置顶 + 超时"""

    saved = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("settingsDialog")
        self.setWindowTitle("设置")
        self.setModal(True)
        self.setMinimumWidth(theme.sp(420))

        display = prefs.display_map()
        self._boxes: dict[str, QCheckBox] = {}

        root = QVBoxLayout(self)
        root.setContentsMargins(theme.sp(22), theme.sp(18), theme.sp(22), theme.sp(16))
        root.setSpacing(theme.sp(10))

        title = QLabel("设置")
        title.setObjectName("dialogTitle")
        root.addWidget(title)

        hint = QLabel("类别开关与命令行共用同一份 config.yaml")
        hint.setObjectName("groupTitle")
        root.addWidget(hint)

        grid = QGridLayout()
        grid.setContentsMargins(0, theme.sp(6), 0, theme.sp(4))
        grid.setHorizontalSpacing(theme.sp(18))
        grid.setVerticalSpacing(theme.sp(4))
        for index, cat in enumerate(ALL_CATEGORIES):
            box = QCheckBox(CATEGORY_LABELS.get(cat, cat))
            box.setChecked(bool(display.get(cat, True)))
            box.setToolTip(DESCRIPTIONS.get(cat, ""))
            self._boxes[cat] = box
            grid.addWidget(box, index // 3, index % 3)
        root.addLayout(grid)

        line = QWidget()
        line.setFixedHeight(1)
        line.setStyleSheet(f"background-color: {theme.P['line']};")
        root.addWidget(line)

        options = QHBoxLayout()
        options.setSpacing(theme.sp(10))
        self._on_top = QCheckBox("窗口置顶")
        self._on_top.setChecked(bool(prefs.gui_prefs().get("on_top", False)))
        options.addWidget(self._on_top)
        options.addStretch()
        options.addWidget(QLabel("采集超时"))
        self._timeout = QSpinBox()
        self._timeout.setRange(3, 120)
        self._timeout.setSuffix(" 秒")
        self._timeout.setValue(prefs.get_timeout())
        self._timeout.setFixedWidth(theme.sp(88))
        options.addWidget(self._timeout)
        root.addLayout(options)

        buttons = QDialogButtonBox()
        cancel = QPushButton("取消")
        cancel.setObjectName("dialogCancel")
        save = QPushButton("保存")
        save.setObjectName("dialogSave")
        save.setDefault(True)
        buttons.addButton(cancel, QDialogButtonBox.ButtonRole.RejectRole)
        buttons.addButton(save, QDialogButtonBox.ButtonRole.AcceptRole)
        cancel.clicked.connect(self.reject)
        save.clicked.connect(self.accept)
        root.addWidget(buttons)

    def accept(self) -> None:  # noqa: D102
        prefs.set_display({cat: box.isChecked() for cat, box in self._boxes.items()})
        prefs.set_gui_pref("on_top", self._on_top.isChecked())
        prefs.set_timeout(self._timeout.value())
        self.saved.emit()
        super().accept()
