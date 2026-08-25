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
            "芯片组": self._get_chipset(c),
            "BIOS_厂商": (bios.Manufacturer or "").strip() if bios else None,
            "BIOS_版本": (bios.SMBIOSBIOSVersion or "").strip() if bios else None,
            "BIOS_日期": parse_wmi_date_only(bios.ReleaseDate) if bios else None,
            "UEFI": self._check_uefi(),
            "TPM": self._get_tpm_info(),
        }

        if warnings:
            result["_警告"] = warnings

        return result

    def get_brief_fields(self) -> list[str]:
        return ["厂商", "型号", "BIOS_版本"]

    def _get_chipset(self, c) -> str | None:
        """通过注册表扫描 PCI 设备中的 LPC/ISA 桥接设备推断芯片组（快速，<50ms）"""
        import winreg

        try:
            pci_key = winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE,
                r"SYSTEM\CurrentControlSet\Enum\PCI"
            )
        except Exception:
            return self._get_chipset_fallback(c)

        try:
            i = 0
            while True:
                try:
                    subkey_name = winreg.EnumKey(pci_key, i)
                    i += 1
                except OSError:
                    break

                upper = subkey_name.upper()
                is_intel = "VEN_8086" in upper
                is_amd = "VEN_1022" in upper

                if not (is_intel or is_amd):
                    continue

                dev_id = self._extract_dev_id(upper)
                if dev_id is None:
                    continue

                # 检查设备 ID 是否在芯片组范围内
                if is_intel and not self._is_intel_lpc_device(dev_id):
                    continue
                if is_amd and not self._is_amd_chipset_device(dev_id):
                    continue

                # 读取 DeviceDesc 确认是 LPC/ISA 桥接设备
                desc = self._read_device_desc(subkey_name)
                if desc and self._is_chipset_description(desc):
                    return desc
        finally:
            winreg.CloseKey(pci_key)

        return self._get_chipset_fallback(c)

    def _get_chipset_fallback(self, c) -> str | None:
        """芯片组检测回退方案：从 IDE 控制器推断"""
        try:
            ide_devices = c.Win32_IDEController()
            if ide_devices:
                name = ide_devices[0].Name or ""
                if name:
                    return name
        except Exception:
            pass
        return None

    @staticmethod
    def _extract_dev_id(pci_key_upper: str) -> int | None:
        """从 PCI 注册表键名提取设备 ID（如 'VEN_8086&DEV_7A84...' → 0x7A84）"""
        import re
        match = re.search(r"DEV_([0-9A-F]{4})", pci_key_upper)
        if match:
            return int(match.group(1), 16)
        return None

    @staticmethod
    def _is_intel_lpc_device(dev_id: int) -> bool:
        """判断是否为 Intel LPC/eSPI 控制器（芯片组南桥标识）"""
        # Intel PCH LPC 控制器设备 ID 范围（覆盖各代平台）
        return (
            0x0000 <= dev_id <= 0x0FFF or   # 早期客户端
            0x1000 <= dev_id <= 0x1FFF or   # 服务器平台 (C621 等)
            0x3000 <= dev_id <= 0x3FFF or   # HEDT (X299 等)
            0x4000 <= dev_id <= 0x4FFF or   # 新平台
            0x5000 <= dev_id <= 0x5FFF or   # 新平台
            0x7000 <= dev_id <= 0x7FFF or   # 600/700/800 系列 (Z790=0x7A84)
            0x8000 <= dev_id <= 0x8FFF or   # 移动平台
            0x9000 <= dev_id <= 0x9FFF or   # 移动平台 (HM 系列)
            0xA000 <= dev_id <= 0xAFFF      # 未来平台
        )

    @staticmethod
    def _is_amd_chipset_device(dev_id: int) -> bool:
        """判断是否为 AMD FCH 芯片组设备"""
        return (
            0x7900 <= dev_id <= 0x79FF or   # FCH 系列 (790E=LPC)
            0x1400 <= dev_id <= 0x14FF or   # Zen 内部桥接
            0x1500 <= dev_id <= 0x15FF or   # Zen 内部桥接
            0x1600 <= dev_id <= 0x16FF      # Zen 内部桥接
        )

    @staticmethod
    def _is_chipset_description(desc: str) -> bool:
        """判断 DeviceDesc 是否为芯片组 LPC/ISA 桥接设备"""
        desc_lower = desc.lower()
        chipset_keywords = ["lpc", "espi", "isa bridge", "fch"]
        return any(kw in desc_lower for kw in chipset_keywords)

    @staticmethod
    def _read_device_desc(pci_subkey_name: str) -> str | None:
        """从注册表读取设备描述名（需进入 instance 子键）"""
        import winreg
        try:
            hw_key = winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE,
                rf"SYSTEM\CurrentControlSet\Enum\PCI\{pci_subkey_name}"
            )
            try:
                # 枚举第一个 instance 子键
                instance = winreg.EnumKey(hw_key, 0)
            except OSError:
                return None
            finally:
                winreg.CloseKey(hw_key)

            inst_key = winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE,
                rf"SYSTEM\CurrentControlSet\Enum\PCI\{pci_subkey_name}\{instance}"
            )
            try:
                desc, _ = winreg.QueryValueEx(inst_key, "DeviceDesc")
                # DeviceDesc 可能含前缀如 "@oem123.inf,%desc%;Intel(R) ..."
                if ";" in desc:
                    desc = desc.split(";")[-1]
                return desc.strip() or None
            finally:
                winreg.CloseKey(inst_key)
        except Exception:
            return None

    def _get_tpm_info(self) -> str | None:
        """检测 TPM 版本与状态（通过注册表 + ACPI 设备，避免慢速 WMI 命名空间连接）"""
        import winreg

        # 方法 1：检查 ACPI TPM 设备（最可靠且快速）
        # 常见 TPM 硬件 ID：
        #   MSFT0101 = TPM 2.0 (Microsoft 通用)
        #   MSFT0102 = TPM 1.2
        #   INTC0B00 / INTC0C00 = Intel PTT (fTPM 2.0)
        #   ATMEL  = Atmel TPM
        #   NTC0602 / NTC0700 = Nuvoton TPM
        try:
            tpm_devices_key = winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE,
                r"SYSTEM\CurrentControlSet\Enum\ACPI"
            )
            try:
                i = 0
                while True:
                    try:
                        subkey = winreg.EnumKey(tpm_devices_key, i)
                        i += 1
                    except OSError:
                        break

                    subkey_upper = subkey.upper()
                    if "MSFT0101" in subkey_upper:
                        return "已检测到 (v2.0)"
                    elif "MSFT0102" in subkey_upper:
                        return "已检测到 (v1.2)"
                    elif "INTC0B00" in subkey_upper or "INTC0C00" in subkey_upper:
                        return "已检测到 (v2.0, Intel PTT)"
                    elif subkey_upper.startswith(("ATMEL", "NTC", "STM", "IFX")):
                        return "已检测到"
            finally:
                winreg.CloseKey(tpm_devices_key)
        except Exception:
            pass

        # 方法 2：检查 TPM 服务是否存在
        try:
            svc_key = winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE,
                r"SYSTEM\CurrentControlSet\Services\TPM"
            )
            winreg.CloseKey(svc_key)
            return "已检测到"
        except Exception:
            pass

        # 方法 3：检查 TPM 管理注册表键
        try:
            tpm_key = winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE,
                r"SOFTWARE\Microsoft\Tpm"
            )
            winreg.CloseKey(tpm_key)
            return "已检测到"
        except Exception:
            pass

        return "未检测到"

    def _check_uefi(self) -> bool | None:
        """检测是否为 UEFI 启动，分层降级：

        1. 注册表 PEFirmwareType（微软官方方式）：
           1 = BIOS(传统)，2 = UEFI，3 = 混合(UEFI+BIOS)
        2. 检测 GPT 磁盘上的 EFI 系统分区（ESP）：存在即 UEFI 启动
           （BIOS 只能从 MBR 磁盘引导，不会存在 ESP）
        """
        # 层 1：注册表
        try:
            import winreg
            key = winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE,
                r"SYSTEM\CurrentControlSet\Control",
            )
            try:
                value, _ = winreg.QueryValueEx(key, "PEFirmwareType")
            finally:
                winreg.CloseKey(key)
            if value in (2, 3):
                return True
            if value == 1:
                return False
        except Exception:
            pass  # 部分系统无此键，进入层 2

        # 层 2：EFI 系统分区检测（约 100ms）
        try:
            import wmi
            ns = wmi.WMI(namespace=r"root\Microsoft\Windows\Storage")
            esps = ns.query(
                "SELECT GptType FROM MSFT_Partition "
                "WHERE GptType = '{C12A7328-F81F-11D2-BA4B-00A0C93EC93B}'"
            )
            return len(esps) > 0
        except Exception:
            return None
