"""渲染便当格的整套页面原型为 PNG。

用法:
    python prototypes/styles/render_pages.py
"""
import os
import sys

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

    from bento import build_window as overview
    from bento_detail import build_window as detail_cpu
    from bento_detail_storage import build_window as detail_storage
    from bento_settings import build_window as settings
    from bento_states import build_window as states

    pages = [
        ("03_bento", overview),
        ("06_detail_cpu", detail_cpu),
        ("07_detail_storage", detail_storage),
        ("08_settings", settings),
        ("09_states", states),
    ]
    for name, builder in pages:
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
