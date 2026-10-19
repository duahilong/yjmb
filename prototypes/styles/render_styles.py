"""渲染 5 套风格原型为 PNG。

用法:
    python prototypes/styles/render_styles.py
"""
import os
import sys

# offscreen 在 Windows 上取不到系统字体，会让中文变方框；
# 这里用 windows 平台，仅把窗口抓成 QPixmap。
os.environ.setdefault("QT_QPA_PLATFORM", "windows")
os.environ["QT_SCALE_FACTOR"] = "1"

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from PySide6.QtCore import Qt                                # noqa: E402
from PySide6.QtTest import QTest                             # noqa: E402
from PySide6.QtWidgets import QApplication                   # noqa: E402


def main() -> None:
    app = QApplication(sys.argv)
    out_dir = os.path.join(HERE, "out")
    os.makedirs(out_dir, exist_ok=True)

    from blueprint import build_window as bp
    from editorial import build_window as ed
    from bento import build_window as be
    from glass import build_window as gl
    from printout import build_window as po

    styles = [
        ("01_blueprint", bp),
        ("02_editorial", ed),
        ("03_bento", be),
        ("04_glass", gl),
        ("05_printout", po),
    ]
    for name, builder in styles:
        try:
            window = builder()
        except Exception as exc:  # noqa: BLE001
            print(f"{name}: BUILD FAILED -> {type(exc).__name__}: {exc}")
            continue
        window.resize(1440, 900)
        window.show()
        QTest.qWait(140)
        app.processEvents()
        pixmap = window.grab()
        logical = pixmap.scaled(
            window.width(), window.height(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        path = os.path.join(out_dir, f"{name}.png")
        logical.save(path)
        print(f"{name}: {logical.width()}x{logical.height()} -> {path}")
        window.close()


if __name__ == "__main__":
    main()
