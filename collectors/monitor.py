"""
collectors/monitor.py - 显示器信息采集
"""
from core.base import BaseCollector, CollectorError
from core.registry import register_collector
from utils.wmi_helper import get_wmi, get_wmi_root


@register_collector
class MonitorCollector(BaseCollector):
    name = "monitor"
    label = "显示器"
    order = 90

    def collect(self) -> dict:
        """采集显示器信息"""
        try:
            c = get_wmi()
        except Exception as e:
            raise CollectorError(self.name, f"无法访问 WMI: {e}")

        warnings = []
        monitor_list = []

        # 从 root\wmi 获取显示器 EDID 信息
        edid_info = self._get_edid_info(warnings)

        # 从 Win32_VideoController 获取当前输出信息
        controllers = []
        try:
            controllers = c.Win32_VideoController()
        except Exception:
            warnings.append("无法获取显示输出信息")

        # 合并信息
        if edid_info:
            for i, monitor in enumerate(edid_info):
                # 尝试匹配对应的 VideoController
                ctrl = controllers[i] if i < len(controllers) else None
                info = self._merge_monitor_info(monitor, ctrl)
                monitor_list.append(info)
        elif controllers:
            # 如果 EDID 获取失败，仅从 VideoController 获取基本信息
            for ctrl in controllers:
                if ctrl.CurrentHorizontalResolution:
                    info = {
                        "型号": ctrl.Name or "未知显示器",
                        "厂商": None,
                        "分辨率": f"{ctrl.CurrentHorizontalResolution}×{ctrl.CurrentVerticalResolution}",
                        "刷新率_Hz": ctrl.CurrentRefreshRate or None,
                        "连接方式": None,
                        "状态": "活动",
                    }
                    monitor_list.append(info)

        if not monitor_list:
            raise CollectorError(self.name, "未检测到显示器")

        result = {"显示器列表": monitor_list}
        if warnings:
            result["_警告"] = warnings
        return result

    def get_brief_fields(self) -> list[str]:
        return ["显示器列表"]

    def _get_edid_info(self, warnings: list) -> list[dict] | None:
        """从 root\\wmi 的 WmiMonitorID 获取显示器信息"""
        try:
            wmi_root = get_wmi_root()
            monitors = wmi_root.WmiMonitorID()
        except Exception:
            warnings.append("无法获取显示器 EDID 信息（可能需要管理员权限）")
            return None

        if not monitors:
            return None

        result = []
        for mon in monitors:
            info = {
                "型号": self._bytes_to_str(mon.UserFriendlyName),
                "厂商": self._parse_manufacturer(mon.ManufacturerName),
                "制造年份": mon.YearOfManufacture or None,
                "制造周": mon.WeekOfManufacture or None,
                "序列号": self._bytes_to_str(mon.SerialNumberID),
            }
            result.append(info)

        return result

    def _merge_monitor_info(self, edid: dict, ctrl) -> dict:
        """合并 EDID 信息和 VideoController 信息"""
        resolution = None
        refresh_rate = None
        status = "未连接"

        if ctrl:
            if ctrl.CurrentHorizontalResolution and ctrl.CurrentVerticalResolution:
                resolution = f"{ctrl.CurrentHorizontalResolution}×{ctrl.CurrentVerticalResolution}"
                status = "活动"
            refresh_rate = ctrl.CurrentRefreshRate

        return {
            "型号": edid.get("型号") or "未知",
            "厂商": edid.get("厂商"),
            "制造年份": edid.get("制造年份"),
            "制造周": edid.get("制造周"),
            "分辨率": resolution,
            "刷新率_Hz": refresh_rate,
            "连接方式": None,  # WMI 难以可靠获取，留空
            "状态": status,
        }

    @staticmethod
    def _bytes_to_str(byte_list) -> str | None:
        """将 WMI 返回的字节数组转为字符串（过滤空字节）"""
        if not byte_list:
            return None
        try:
            # WMI 返回的是 uint16 数组
            chars = [chr(b) for b in byte_list if b != 0]
            result = "".join(chars).strip()
            return result if result else None
        except Exception:
            return None

    @staticmethod
    def _parse_manufacturer(manufacturer_bytes) -> str | None:
        """
        解析显示器厂商代码。
        WMI 返回的是 PNP ID 编码（如 [0x04, 0x72] → 'ACR' 即 Acer）
        简化处理：直接转字符串
        """
        if not manufacturer_bytes:
            return None
        try:
            chars = [chr(b) for b in manufacturer_bytes if b != 0]
            result = "".join(chars).strip()
            return result if result else None
        except Exception:
            return None
