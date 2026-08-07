"""
gui/widgets/device_card.py - 多设备卡片组件
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QGroupBox, QFormLayout, QLabel, QScrollArea,
)
from PySide6.QtCore import Qt


class DeviceCard(QGroupBox):
    """单个设备的卡片（GroupBox + FormLayout）"""

    def __init__(self, title: str, data: dict, parent=None):
        super().__init__(title, parent)
        self._build(data)

    def _build(self, data: dict) -> None:
        form = QFormLayout(self)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        for key, value in data.items():
            label = QLabel(f"{key}:")
            label.setStyleSheet("font-weight: bold;")

            if isinstance(value, dict):
                # 嵌套 dict 展平为多行
                for sub_key, sub_val in value.items():
                    form.addRow(QLabel(f"  {sub_key}:"), QLabel(self._fmt(sub_val)))
            elif isinstance(value, list):
                if all(not isinstance(v, (dict, list)) for v in value):
                    form.addRow(label, QLabel(", ".join(str(v) for v in value)))
                else:
                    form.addRow(label, QLabel(f"[{len(value)} 项]"))
            else:
                form.addRow(label, QLabel(self._fmt(value)))

    @staticmethod
    def _fmt(value) -> str:
        if value is None:
            return "-"
        return str(value)


class DeviceCardList(QScrollArea):
    """多设备卡片列表（可滚动）"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.setFrameShape(QScrollArea.Shape.NoFrame)

        self._container = QWidget()
        self._container.setStyleSheet("background-color: #f5f5f5;")
        self._layout = QVBoxLayout(self._container)
        self._layout.setSpacing(12)
        self._layout.addStretch()
        self.setWidget(self._container)

    def set_devices(self, devices: list[dict], title_field: str = "名称") -> None:
        """从设备列表生成卡片"""
        self._clear()

        for i, device in enumerate(devices):
            if not isinstance(device, dict):
                continue
            title = str(device.get(title_field, f"设备 {i + 1}"))
            card = DeviceCard(title, device)
            self._layout.insertWidget(self._layout.count() - 1, card)

    def _clear(self) -> None:
        """清空所有卡片"""
        while self._layout.count() > 1:  # 保留末尾 stretch
            item = self._layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
