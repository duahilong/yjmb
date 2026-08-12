"""
collectors/cpu.py - 处理器信息采集
"""
import winreg

from core.base import BaseCollector, CollectorError
from core.registry import register_collector
from utils.wmi_helper import get_wmi
from utils.format_utils import kb_to_mb


# CPU 架构代码映射
_ARCH_MAP = {
    0: "x86",
    1: "MIPS",
    2: "Alpha",
    3: "PowerPC",
    5: "ARM",
    6: "Itanium",
    9: "x64",
    12: "ARM64",
}


@register_collector
class CPUCollector(BaseCollector):
    name = "cpu"
    label = "处理器"
    order = 30

    def collect(self) -> dict:
        """采集 CPU 信息"""
        try:
            c = get_wmi()
            processors = c.Win32_Processor()
        except Exception as e:
            raise CollectorError(self.name, f"无法访问处理器信息: {e}")

        if not processors:
            raise CollectorError(self.name, "未检测到处理器")

        cpu = processors[0]

        result = {
            "名称": (cpu.Name or "").strip(),
            "厂商": cpu.Manufacturer or None,
            "架构": _ARCH_MAP.get(cpu.Architecture, f"未知({cpu.Architecture})"),
            "插槽": cpu.SocketDesignation or None,
            "核心数": cpu.NumberOfCores,
            "线程数": cpu.NumberOfLogicalProcessors,
            "基础频率_MHz": cpu.MaxClockSpeed or None,
            "L2缓存_MB": kb_to_mb(cpu.L2CacheSize) if cpu.L2CacheSize else None,
            "L3缓存_MB": kb_to_mb(cpu.L3CacheSize) if cpu.L3CacheSize else None,
            "指令集": self._get_instruction_sets(),
            "虚拟化": self._get_virtualization_status(),
            "当前负载_百分比": self._get_cpu_load(),
        }

        return result

    def get_brief_fields(self) -> list[str]:
        return ["名称", "核心数", "线程数", "基础频率_MHz"]

    def _get_instruction_sets(self) -> list[str]:
        """推断 CPU 指令集（基于架构和型号）"""
        try:
            key = winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE,
                r"HARDWARE\DESCRIPTION\System\CentralProcessor\0",
            )
            identifier, _ = winreg.QueryValueEx(key, "Identifier")
            winreg.CloseKey(key)
        except Exception:
            return []

        # 现代 x64 CPU 基本都支持这些
        sets = ["SSE", "SSE2", "SSE3", "SSSE3", "SSE4.1", "SSE4.2"]

        # AVX/AVX2 判断：
        # - Intel 2nd gen+ (Sandy Bridge 2011) 支持 AVX
        # - Intel 4th gen+ (Haswell 2013) / AMD Zen+ 支持 AVX2
        # - 当前所有 x64 CPU 均为 2013 年后产品，默认包含
        # - Identifier 示例：Intel "Intel64 Family 6 Model 186..." / AMD "AuthenticAMD Family 25 Model 33..."
        id_lower = (identifier or "").lower()
        is_x64 = "intel64" in id_lower or "authenticamd" in id_lower

        if is_x64:
            sets.append("AVX")
            sets.append("AVX2")

        return sets

    def _get_virtualization_status(self) -> bool | None:
        """检测虚拟化是否启用（通过 WMI，避免调用极慢的 systeminfo）"""
        try:
            c = get_wmi()
            # Win32_ComputerSystem.HypervisorPresent 或 Win32_Processor 属性
            systems = c.Win32_ComputerSystem()
            if systems:
                hypervisor = getattr(systems[0], 'HypervisorPresent', None)
                if hypervisor is not None:
                    return bool(hypervisor)
        except Exception:
            pass

        # 降级：检查注册表中 VT-x/AMD-V 特性
        try:
            key = winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE,
                r"SYSTEM\CurrentControlSet\Control\DeviceGuard",
            )
            try:
                val, _ = winreg.QueryValueEx(key, "EnableVirtualizationBasedSecurity")
                winreg.CloseKey(key)
                return bool(val)
            except FileNotFoundError:
                winreg.CloseKey(key)
        except Exception:
            pass

        return None

    def _get_cpu_load(self) -> float | None:
        """获取当前 CPU 负载（psutil 首次调用返回 0.0，先预热启动采样）"""
        try:
            import psutil
            psutil.cpu_percent(interval=None)  # 预热：记录采样起点
            return psutil.cpu_percent(interval=0.1)
        except Exception:
            return None
