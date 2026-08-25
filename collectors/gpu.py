"""
collectors/gpu.py - 显卡信息采集
"""
import re

from core.base import BaseCollector, CollectorError
from core.registry import register_collector
from utils.wmi_helper import get_wmi, parse_wmi_date_only
from utils.format_utils import bytes_to_mb

# pynvml 可用性缓存（避免无 N 卡机器每次采集都重复 import/init）
_NVML: object | None = None       # pynvml 模块引用（None=不可用）
_NVML_CHECKED = False             # 是否已检测过可用性


def _get_nvml():
    """获取 pynvml 模块（首次调用检测，结果缓存）"""
    global _NVML, _NVML_CHECKED
    if _NVML_CHECKED:
        return _NVML
    _NVML_CHECKED = True
    try:
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", FutureWarning)
            import pynvml
        pynvml.nvmlInit()
        _NVML = pynvml
    except Exception:
        _NVML = None
    return _NVML


@register_collector
class GPUCollector(BaseCollector):
    name = "gpu"
    label = "显卡"
    order = 50

    def collect(self) -> dict:
        """采集显卡信息"""
        try:
            c = get_wmi()
            controllers = c.Win32_VideoController()
        except Exception as e:
            raise CollectorError(self.name, f"无法访问显卡信息: {e}")

        if not controllers:
            raise CollectorError(self.name, "未检测到显卡")

        gpu_list = []
        for gpu in controllers:
            gpu_info = self._parse_gpu(gpu)
            gpu_list.append(gpu_info)

        # 尝试用 pynvml 补充 NVIDIA 显卡实时数据
        self._enrich_nvidia_data(gpu_list)

        return {"显卡列表": gpu_list}

    def get_brief_fields(self) -> list[str]:
        return ["显卡列表"]

    def _parse_gpu(self, gpu) -> dict:
        """解析单个显卡信息"""
        name = gpu.Name or ""
        adapter_compat = gpu.AdapterCompatibility or ""

        # WMI 名称/厂商缺失时，用离线 pci.ids 数据库兜底翻译
        name, adapter_compat = self._fallback_pci_info(
            name, adapter_compat, gpu.PNPDeviceID
        )
        if not name:
            name = "未知显卡"

        # 判断独显/核显
        gpu_type = self._classify_gpu(name, adapter_compat, gpu.PNPDeviceID)

        # 显存（WMI 的 AdapterRAM 是 32 位整数，超过 4GB 会溢出）
        vram_mb = None
        if gpu.AdapterRAM:
            vram_mb = bytes_to_mb(int(gpu.AdapterRAM))
            # 如果值异常（负数或超过 64GB），可能是溢出
            if vram_mb and (vram_mb < 0 or vram_mb > 65536):
                vram_mb = None

        # 分辨率
        resolution = None
        if gpu.CurrentHorizontalResolution and gpu.CurrentVerticalResolution:
            resolution = f"{gpu.CurrentHorizontalResolution}×{gpu.CurrentVerticalResolution}"

        # 状态
        status = gpu.Status or "未知"
        if status == "OK":
            status = "正常"
        elif gpu.ConfigManagerErrorCode and gpu.ConfigManagerErrorCode != 0:
            status = "已禁用"

        return {
            "类型": gpu_type,
            "名称": name,
            "厂商": adapter_compat or None,
            "显存_MB": vram_mb,
            "驱动版本": gpu.DriverVersion or None,
            "驱动日期": parse_wmi_date_only(gpu.DriverDate),
            "当前分辨率": resolution,
            "刷新率_Hz": gpu.CurrentRefreshRate or None,
            "状态": status,
            "负载_百分比": None,   # 由 pynvml 补充
            "显存使用_MB": None,   # 由 pynvml 补充
        }

    def _fallback_pci_info(
        self, name: str, vendor: str, pnp_id: str | None
    ) -> tuple[str, str]:
        """WMI 名称/厂商缺失时，用内置 pci.ids 离线库兜底翻译。

        降级链（需求文档）：WMI 名称 → pci.ids 设备名 → 原始名称。
        数据库按需加载（首次调用才解析 data/pci.ids），
        名称/厂商齐全的主流机器不会触发加载开销。
        """
        if not pnp_id or "PCI\\" not in pnp_id.upper():
            return name, vendor

        generic_names = ("", "未知显卡")
        needs_name = name in generic_names or "video controller" in name.lower()
        needs_vendor = not vendor
        if not (needs_name or needs_vendor):
            return name, vendor

        try:
            from utils.pci_ids import get_pci_db
            db = get_pci_db()
            if not db.is_loaded:
                return name or "未知显卡", vendor

            if needs_name:
                resolved = db.resolve_name(pnp_id)
                if resolved:
                    # 完整设备名（含厂商前缀），厂商字段无需重复填充
                    return resolved, vendor
            elif needs_vendor:
                m = re.search(r"VEN_([0-9A-F]{4})", pnp_id.upper())
                if m:
                    vendor_name = db.get_vendor(m.group(1))
                    if vendor_name:
                        return name, vendor_name
        except Exception:
            pass
        return name or "未知显卡", vendor

    def _classify_gpu(self, name: str, adapter_compat: str, pnp_id: str | None) -> str:
        """判断是独显还是核显"""
        name_lower = name.lower()
        compat_lower = adapter_compat.lower()

        # Intel 核显关键词
        intel_igpu_keywords = ["uhd graphics", "iris", "hd graphics", "arc a3"]
        for kw in intel_igpu_keywords:
            if kw in name_lower:
                return "核显"

        # AMD 核显关键词（兼容字段可能是缩写或公司全称）
        amd_igpu_keywords = ["radeon graphics", "vega"]
        is_amd_vendor = (
            "amd" in compat_lower
            or "ati" in compat_lower
            or "advanced micro devices" in compat_lower
        )
        if is_amd_vendor:
            for kw in amd_igpu_keywords:
                if kw in name_lower and "rx" not in name_lower:
                    return "核显"

        # 名称含 Radeon 但厂商信息缺失：默认按独显处理（核显名称通常带 Graphics 后缀）
        if "nvidia" in compat_lower:
            return "独显"

        # 默认：如果有 "GeForce" / "Radeon RX" / "Arc" 等则为独显
        discrete_keywords = ["geforce", "radeon rx", "quadro", "tesla", "rtx", "gtx", "arc a7"]
        for kw in discrete_keywords:
            if kw in name_lower:
                return "独显"

        return "未知"

    def _enrich_nvidia_data(self, gpu_list: list[dict]) -> None:
        """尝试用 pynvml 补充 NVIDIA 显卡的实时数据"""
        nvml = _get_nvml()
        if nvml is None:
            return

        try:
            device_count = nvml.nvmlDeviceGetCount()

            nvidia_gpus = [g for g in gpu_list if "nvidia" in (g.get("厂商") or "").lower()]

            for i in range(min(device_count, len(nvidia_gpus))):
                handle = nvml.nvmlDeviceGetHandleByIndex(i)

                # GPU 利用率
                try:
                    util = nvml.nvmlDeviceGetUtilizationRates(handle)
                    nvidia_gpus[i]["负载_百分比"] = util.gpu
                except Exception:
                    pass

                # 显存使用
                try:
                    mem_info = nvml.nvmlDeviceGetMemoryInfo(handle)
                    nvidia_gpus[i]["显存使用_MB"] = round(mem_info.used / (1024 ** 2))
                    # WMI AdapterRAM 是 uint32，>4GB 会溢出成错误值；
                    # pynvml 数据可靠，总是用它覆盖总量
                    nvidia_gpus[i]["显存_MB"] = round(mem_info.total / (1024 ** 2))
                except Exception:
                    pass
        except Exception:
            pass  # 初始化失败（无 N 卡等），跳过
