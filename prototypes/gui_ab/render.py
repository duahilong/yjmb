"""把 A/B 两版原型渲染成 PNG，便于并排评审。

用法:
    python prototypes/gui_ab/render.py
"""
import os
import sys

# offscreen 平台在 Windows 上拿不到系统字体，会让中文变成方框；
# 这里使用 windows 平台，仅把窗口渲染到 QPixmap，不依赖真实显示。
os.environ.setdefault("QT_QPA_PLATFORM", "windows")
os.environ["QT_SCALE_FACTOR"] = "1"

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from PySide6.QtCore import Qt  # noqa: E402
from PySide6.QtTest import QTest  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

from prototype_a import build_window as build_a  # noqa: E402
from prototype_b import build_window as build_b  # noqa: E402


def main() -> None:
    app = QApplication(sys.argv)
    out_dir = os.path.join(HERE, "out")
    os.makedirs(out_dir, exist_ok=True)

    for name, builder in [("a_bench_sheet", build_a), ("b_night_bench", build_b)]:
        window = builder()
        window.resize(1440, 900)
        window.show()
        QTest.qWait(120)
        app.processEvents()
        pixmap = window.grab()
        # 屏幕 DPR 可能是 1.75/1.5，统一缩到逻辑尺寸便于并排比较
        logical = pixmap.scaled(
            window.width(), window.height(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        path = os.path.join(out_dir, f"{name}.png")
        logical.save(path)
        print(f"{name}: {logical.width()}x{logical.height()} (grab {pixmap.width()}x{pixmap.height()}) -> {path}")
        window.close()


if __name__ == "__main__":
    main()
