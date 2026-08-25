"""
collectors/network.py - 网络设备信息采集
"""
from core.base import BaseCollector, CollectorError
from core.registry import register_collector
from utils.wmi_helper import get_wmi
from utils.format_utils import bps_to_gbps
from utils.registry import get_driver_version


@register_collector
class NetworkCollector(BaseCollector):
    name = "network"
    label = "网络设备"
    order = 70

    def collect(self) -> dict:
        """采集网络设备信息"""
        try:
            c = get_wmi()
            adapters = c.Win32_NetworkAdapter(PhysicalAdapter=True)
        except Exception as e:
            raise CollectorError(self.name, f"无法访问网络设备信息: {e}")

        if not adapters:
            raise CollectorError(self.name, "未检测到网络适配器")

        # 获取网络配置（IP 等）
        config_map = self._build_config_map(c)

        # 获取无线信息
        wifi_info = self._get_wifi_info()

        adapter_list = []
        for adapter in adapters:
            # 过滤掉没有连接 ID 的虚拟适配器
            if not adapter.NetConnectionID and adapter.NetConnectionStatus != 2:
                continue

            info = self._parse_adapter(adapter, config_map, wifi_info)
            if info:
                adapter_list.append(info)

        if not adapter_list:
            raise CollectorError(self.name, "未检测到有效网络适配器")

        return {"网卡列表": adapter_list}

    def get_brief_fields(self) -> list[str]:
        return ["网卡列表"]

    def _parse_adapter(self, adapter, config_map: dict, wifi_info: dict | None) -> dict | None:
        """解析单个网络适配器"""
        name = adapter.Name or "未知网卡"
        adapter_type = adapter.AdapterType or ""

        # 判断有线/无线
        is_wireless = self._is_wireless(name, adapter_type, adapter.PNPDeviceID)
        net_type = "无线" if is_wireless else "以太网"

        # 状态（MSDN Win32_NetworkAdapter.NetConnectionStatus）
        status_code = adapter.NetConnectionStatus
        status_map = {
            0: "未连接",
            1: "正在连接",
            2: "已连接",
            3: "正在断开",
            4: "硬件不存在",
            5: "硬件禁用",
            6: "硬件故障",
            7: "媒体断开",
            8: "认证中",
            9: "认证成功",
            10: "认证失败",
            11: "无效地址",
            12: "凭证不足",
        }
        if status_code is not None:
            status = status_map.get(status_code, f"状态码: {status_code}")
        else:
            status = "未知"

        # 速率
        speed_gbps = None
        if adapter.Speed:
            try:
                speed_val = int(adapter.Speed)
                # 过滤无效值（如 int64 最大值 9223372036854775807）
                # >10Gbps 通常是虚拟适配器的假速率，真实 10G 网卡取等号保留
                if 0 < speed_val <= 10_000_000_000:
                    speed_gbps = bps_to_gbps(speed_val)
            except (ValueError, TypeError):
                pass

        # IP 配置
        config = config_map.get(adapter.Index, {})
        ipv4 = config.get("IPv4")
        subnet = config.get("子网掩码")
        gateway = config.get("网关")

        result = {
            "类型": net_type,
            "名称": name,
            "厂商": adapter.Manufacturer or None,
            "MAC": adapter.MACAddress or None,
            "速率_Gbps": speed_gbps,
            "状态": status,
            "IPv4": ipv4,
            "子网掩码": subnet,
            "网关": gateway,
            "驱动版本": get_driver_version(adapter.PNPDeviceID or ""),
        }

        # 无线额外信息
        if is_wireless and wifi_info and status == "已连接":
            result["SSID"] = wifi_info.get("SSID")
            result["信号_dBm"] = wifi_info.get("信号_dBm")

        return result

    def _build_config_map(self, c) -> dict:
        """构建网卡 Index → IP 配置的映射"""
        result = {}
        try:
            configs = c.Win32_NetworkAdapterConfiguration(IPEnabled=True)
            for cfg in configs:
                info = {}
                # 取第一个 IPv4 地址
                if cfg.IPAddress:
                    for addr in cfg.IPAddress:
                        if "." in addr:  # IPv4
                            info["IPv4"] = addr
                            break
                if cfg.IPSubnet:
                    info["子网掩码"] = cfg.IPSubnet[0]
                if cfg.DefaultIPGateway:
                    info["网关"] = cfg.DefaultIPGateway[0]
                result[cfg.Index] = info
        except Exception:
            pass
        return result

    def _is_wireless(self, name: str, adapter_type: str, pnp_id: str | None) -> bool:
        """判断是否为无线网卡"""
        name_lower = name.lower()
        wireless_keywords = ["wi-fi", "wifi", "wireless", "wlan", "802.11", "ax2", "ac9"]
        for kw in wireless_keywords:
            if kw in name_lower:
                return True
        if "wireless" in adapter_type.lower():
            return True
        return False

    def _get_wifi_info(self) -> dict | None:
        """通过 netsh 获取当前 WiFi 连接信息"""
        try:
            from utils.powershell import run_command
            output = run_command(["netsh", "wlan", "show", "interfaces"], timeout=5)

            info = {}
            for line in output.split("\n"):
                line = line.strip()
                if ":" in line:
                    key, _, value = line.partition(":")
                    key = key.strip()
                    value = value.strip()

                    if "SSID" in key and "BSSID" not in key:
                        info["SSID"] = value
                    elif "Signal" in key or "信号" in key:
                        # 信号强度通常是百分比，转为大约的 dBm
                        try:
                            percent = int(value.replace("%", ""))
                            # 粗略换算: dBm ≈ (percent - 100) / 2
                            info["信号_dBm"] = round((percent - 100) / 2)
                        except ValueError:
                            pass

            return info if info else None
        except Exception:
            return None
