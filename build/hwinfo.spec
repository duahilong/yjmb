# -*- mode: python ; coding: utf-8 -*-
# PyInstaller 打包配置：hwinfo 单文件 EXE
# 构建命令: pyinstaller --clean build/hwinfo.spec
import os

_ROOT = os.path.normpath(os.path.join(SPECPATH, ".."))

a = Analysis(
    [os.path.join(_ROOT, 'main.py')],
    pathex=[_ROOT],
    binaries=[],
    datas=[
        (os.path.join(_ROOT, 'data', 'pci.ids'), 'data'),
    ],
    hiddenimports=[
        'wmi',
        'pythoncom',
        'pynvml',
        'collectors.os_info',
        'collectors.motherboard',
        'collectors.cpu',
        'collectors.memory',
        'collectors.gpu',
        'collectors.storage',
        'collectors.network',
        'collectors.audio',
        'collectors.monitor',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter'],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='HWInfo',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,          # 禁用 UPX：UPX 加壳的 DLL 加载时执行解压 stub，
                        # 且杀毒软件会对 UPX 文件深度扫描，导致启动卡顿/误报
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,          # GUI 程序，无控制台窗口
    disable_windowed_traceback=False,
    icon=None,
)
