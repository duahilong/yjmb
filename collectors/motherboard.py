"""
collectors/motherboard.py - 主板信息采集
"""
from core.base import BaseCollector, CollectorError
from core.registry import register_collector
from utils.wmi_helper import get_wmi, parse_wmi_date_only


@register_collector
class MotherboardCollector(BaseCollector):
    name = "motherboard"
    label = "主板"
    order = 20

    def collect(self) -> dict:
        """采集主板信息"""
        try:
            c = get_wmi()
        except Exception as e:
            raise CollectorError(self.name, f"无法访问 WMI: {e}")

        warnings = []

        # 主板基本信息
        try:
            boards = c.Win32_BaseBoard()
            board = boards[0] if boards else None
        except Exception:
            board = None
            warnings.append("无法获取主板信息")

        # BIOS 信息
        try:
            bios_list = c.Win32_BIOS()
            bios = bios_list[0] if bios_list else None
        except Exception:
            bios = None
            warnings.append("无法获取 BIOS 信息")

        result = {
            "厂商": (board.Manufacturer or "").strip() if board else None,
            "型号": (board.Product or "").strip() if board else None,
            "版本": (board.Version or "").strip() if board else None,
            "序列号": (board.SerialNumber or "").strip() if board else None,
            "BIOS_厂商": (bios.Manufacturer or "").strip() if bios else None,
            "BIOS_版本": (bios.SMBIOSBIOSVersion or "").strip() if bios else None,
            "BIOS_日期": parse_wmi_date_only(bios.ReleaseDate) if bios else None,
            "UEFI": self._check_uefi(),
        }

        if warnings:
            result["_警告"] = warnings

        return result

    def get_brief_fields(self) -> list[str]:
        return ["厂商", "型号", "BIOS_版本"]

    def _check_uefi(self) -> bool | None:
        """检测是否为 UEFI 启动"""
        try:
            import os
            # UEFI 系统会有此目录
            efi_path = os.path.join(os.environ.get("SystemRoot", r"C:\Windows"), "Boot", "EFI")
            if os.path.exists(efi_path):
                return True
            # 也可以通过注册表检查
            import winreg
            try:
                key = winreg.OpenKey(
                    winreg.HKEY_LOCAL_MACHINE,
                    r"SYSTEM\CurrentControlSet\Control\SecureBoot\State",
                )
                winreg.CloseKey(key)
                return True
            except FileNotFoundError:
                return False
        except Exception:
            return None
