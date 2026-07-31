"""
collectors/audio.py - 音频设备信息采集
"""
from core.base import BaseCollector, CollectorError
from core.registry import register_collector
from utils.wmi_helper import get_wmi


@register_collector
class AudioCollector(BaseCollector):
    name = "audio"
    label = "音频设备"
    order = 80

    def collect(self) -> dict:
        """采集音频设备信息"""
        try:
            c = get_wmi()
            devices = c.Win32_SoundDevice()
        except Exception as e:
            raise CollectorError(self.name, f"无法访问音频设备信息: {e}")

        if not devices:
            raise CollectorError(self.name, "未检测到音频设备")

        audio_list = []
        for device in devices:
            info = self._parse_device(device)
            audio_list.append(info)

        return {"音频设备列表": audio_list}

    def get_brief_fields(self) -> list[str]:
        return ["音频设备列表"]

    def _parse_device(self, device) -> dict:
        """解析单个音频设备"""
        name = device.Name or "未知音频设备"
        manufacturer = device.Manufacturer or ""

        # 判断位置（板载/GPU附带/USB外接）
        location = self._guess_location(name, manufacturer, device.PNPDeviceID)

        # 状态
        status = device.Status or "未知"
        if status == "OK":
            status = "正常"

        return {
            "名称": name,
            "厂商": manufacturer or None,
            "位置": location,
            "状态": status,
        }

    def _guess_location(self, name: str, manufacturer: str, pnp_id: str | None) -> str:
        """推断音频设备的位置"""
        name_lower = name.lower()
        pnp_lower = (pnp_id or "").lower()
        mfr_lower = (manufacturer or "").lower()

        # USB 音频
        if "usb" in pnp_lower or "usb" in name_lower:
            return "USB 外接"

        # NVIDIA / AMD HDMI 音频（GPU 附带）
        # 注意：使用更精确的匹配避免误判
        gpu_name_keywords = ["nvidia", "hdmi", "displayport"]
        for kw in gpu_name_keywords:
            if kw in name_lower:
                return "GPU 附带 (HDMI/DP)"

        # 厂商名精确匹配（避免 "ati" 匹配到 "Corporation"）
        gpu_mfr_keywords = ["nvidia", "amd", "ati technologies"]
        for kw in gpu_mfr_keywords:
            if kw in mfr_lower:
                return "GPU 附带 (HDMI/DP)"

        # PNP ID 中检查是否挂在 GPU 总线下
        if "ven_10de" in pnp_lower or "ven_1002" in pnp_lower:  # NVIDIA / AMD PCI ID
            return "GPU 附带 (HDMI/DP)"

        # 默认板载
        return "板载"
