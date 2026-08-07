@echo off
rem ============================================================
rem  HWInfo 打包脚本 - 生成单文件 EXE (dist/HWInfo.exe)
rem  依赖: pip install pyinstaller
rem ============================================================
cd /d %~dp0..
if not exist .venv\Scripts\python.exe (
    echo [INFO] 使用系统 Python
    set PY=python
) else (
    echo [INFO] 使用虚拟环境 .venv
    set PY=.venv\Scripts\python.exe
)

%PY% -m pip install -r requirements.txt pyinstaller
if errorlevel 1 exit /b 1

%PY% -m PyInstaller --clean --noconfirm build\hwinfo.spec
if errorlevel 1 exit /b 1

echo.
echo [OK] 打包完成: dist\HWInfo.exe
pause
