"""
utils/powershell.py - PowerShell 命令调用封装
"""
import subprocess
import json
import locale


def _no_window_flags() -> int:
    """Windows 下禁止子进程创建控制台窗口（避免 GUI 程序启动时闪现黑窗口）；
    非 Windows 平台返回 0（无该标志）。"""
    return getattr(subprocess, "CREATE_NO_WINDOW", 0)


def _ansi_encoding() -> str:
    """本地 ANSI 代码页编码（中文系统为 cp936）。
    netsh 等控制台程序按此编码输出，用 utf-8 强解码会导致乱码。"""
    return locale.getpreferredencoding(False)


def run_powershell(command: str, timeout: int = 10) -> str:
    """
    执行 PowerShell 命令，返回 stdout 文本。

    通过先设置 [Console]::OutputEncoding 强制 PowerShell 输出 UTF-8，
    避免中文系统默认 GBK 输出与 utf-8 解码不匹配导致的乱码。

    Args:
        command: PowerShell 命令字符串
        timeout: 超时秒数

    Returns:
        命令输出的文本

    Raises:
        subprocess.TimeoutExpired: 超时
        subprocess.CalledProcessError: 命令执行失败
    """
    full_command = (
        "[Console]::OutputEncoding=[System.Text.Encoding]::UTF8; "
        + command
    )
    result = subprocess.run(
        ["powershell", "-NoProfile", "-NonInteractive", "-Command", full_command],
        capture_output=True,
        text=True,
        timeout=timeout,
        encoding="utf-8",
        errors="replace",
        creationflags=_no_window_flags(),
    )
    if result.returncode != 0:
        raise subprocess.CalledProcessError(
            result.returncode, command, result.stdout, result.stderr
        )
    return result.stdout.strip()


def run_powershell_json(command: str, timeout: int = 10) -> list | dict:
    """
    执行 PowerShell 命令并以 JSON 解析输出。
    命令应包含 '| ConvertTo-Json' 管道。

    Returns:
        解析后的 Python 对象（list 或 dict）
    """
    output = run_powershell(command, timeout)
    if not output:
        return {}
    return json.loads(output)


def run_command(command: list[str], timeout: int = 10) -> str:
    """
    执行任意命令行程序，返回 stdout 文本。
    用于调用 netsh、wmic 等。

    按本地 ANSI 代码页解码输出（中文系统为 cp936/GBK），
    保证 "信号强度" 等中文字段可被正确解析。

    Args:
        command: 命令及参数列表，如 ["netsh", "wlan", "show", "interfaces"]
        timeout: 超时秒数
    """
    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        timeout=timeout,
        encoding=_ansi_encoding(),
        errors="replace",
        creationflags=_no_window_flags(),
    )
    if result.returncode != 0:
        raise subprocess.CalledProcessError(
            result.returncode, command, result.stdout, result.stderr
        )
    return result.stdout.strip()
