"""
collectors/memory.py - 内存信息采集
"""
import re

from core.base import BaseCollector, CollectorError
from core.registry import register_collector
from utils.wmi_helper import get_wmi
from utils.format_utils import bytes_to_gb, millivolts_to_volts


# SMBIOS 内存类型映射
_MEMORY_TYPE_MAP = {
    0: "未知",
    1: "Other",
    2: "DRAM",
    3: "Synchronous DRAM",
    4: "Cache DRAM",
    5: "EDO",
    6: "EDRAM",
    7: "VRAM",
    8: "SRAM",
    9: "RAM",
    10: "ROM",
    11: "Flash",
    12: "EEPROM",
    13: "FEPROM",
    14: "EPROM",
    15: "CDRAM",
    16: "3DRAM",
    17: "SDRAM",
    18: "SGRAM",
    19: "RDRAM",
    20: "DDR",
    21: "DDR2",
    22: "DDR2 FB-DIMM",
    24: "DDR3",
    25: "FBD2",
    26: "DDR4",
    34: "DDR5",
}


@register_collector
class MemoryCollector(BaseCollector):
    name = "memory"
    label = "内存"
    order = 40

    def collect(self) -> dict:
        """采集内存信息"""
        try:
            c = get_wmi()
        except Exception as e:
            raise CollectorError(self.name, f"无法访问 WMI: {e}")

        warnings = []

        # 获取物理内存条信息
        try:
            sticks = c.Win32_PhysicalMemory()
        except Exception:
            sticks = []
            warnings.append("无法获取内存条详细信息")

        # 获取插槽总数
        total_slots = None
        try:
            arrays = c.Win32_PhysicalMemoryArray()
            if arrays:
                total_slots = arrays[0].MemoryDevices
        except Exception:
            pass

        # 实时使用量
        used_gb = None
        usage_percent = None
        total_gb = None
        try:
            import psutil
            mem = psutil.virtual_memory()
            total_gb = bytes_to_gb(mem.total)
            used_gb = bytes_to_gb(mem.used)
            usage_percent = mem.percent
        except Exception:
            # 如果 psutil 不可用，从 WMI 内存条容量求和
            if sticks:
                total_bytes = sum(int(s.Capacity) for s in sticks if s.Capacity)
                total_gb = bytes_to_gb(total_bytes)

        # 构建每条内存的信息
        memory_sticks = []
        for stick in sticks:
            part_number = (stick.PartNumber or "").strip()
            stick_info = {
                "插槽": stick.DeviceLocator or None,
                "厂商": (stick.Manufacturer or "").strip() or None,
                "型号": part_number or None,
                "容量_GB": bytes_to_gb(int(stick.Capacity)) if stick.Capacity else None,
                "类型": _MEMORY_TYPE_MAP.get(stick.SMBIOSMemoryType, f"类型{stick.SMBIOSMemoryType}"),
                "频率_MHz": stick.Speed or None,
                "CL": self._parse_cl(part_number),
                "位宽_bit": stick.DataWidth or None,
                "电压_V": millivolts_to_volts(stick.ConfiguredVoltage) if stick.ConfiguredVoltage else None,
                "序列号": (stick.SerialNumber or "").strip() or None,
            }
            memory_sticks.append(stick_info)

        # 推断通道模式
        channel_mode = self._guess_channel_mode(len(sticks), total_slots)

        result = {
            "总容量_GB": total_gb,
            "已使用_GB": used_gb,
            "使用率_百分比": usage_percent,
            "插槽总数": total_slots,
            "已用插槽": len(sticks),
            "通道模式": channel_mode,
            "内存条": memory_sticks,
        }

        if warnings:
            result["_警告"] = warnings

        return result

    def get_brief_fields(self) -> list[str]:
        return ["总容量_GB", "已用插槽"]

    @staticmethod
    def _parse_cl(part_number: str) -> int | None:
        """
        从型号字符串解析 CL 值。

        常见格式：
        - "CL36-44-44 D5-7200" → 36
        - "F5-7200J3646G24GX2-TZ5RK"（部分厂商型号不含显式 CL）→ None
        """
        if not part_number:
            return None
        # 优先匹配 "CL36" 这类显式写法（大小写不敏感）
        m = re.search(r"CL\s*(\d+)", part_number, re.IGNORECASE)
        if m:
            return int(m.group(1))
        return None

    def _guess_channel_mode(self, stick_count: int, total_slots: int | None) -> str:
        """根据内存条数推断通道模式"""
        if stick_count == 0:
            return "未知"
        elif stick_count == 1:
            return "单通道"
        elif stick_count == 2:
            return "双通道"
        elif stick_count == 4:
            return "四通道" if (total_slots and total_slots >= 8) else "双通道"
        else:
            return f"{stick_count} 条"
