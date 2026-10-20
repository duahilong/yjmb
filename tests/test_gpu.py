"""
tests/test_gpu.py - GPU 采集纯逻辑测试
"""
from unittest.mock import MagicMock, patch

from collectors.gpu import GPUCollector


class TestClassifyGpu:
    def setup_method(self):
        self.collector = GPUCollector()

    # === Intel 核显关键词 ===
    def test_intel_uhd(self):
        assert self.collector._classify_gpu(
            "Intel(R) UHD Graphics 770", "Intel Corporation", None
        ) == "核显"

    def test_intel_iris(self):
        assert self.collector._classify_gpu(
            "Intel(R) Iris(R) Xe Graphics", "Intel Corporation", None
        ) == "核显"

    def test_intel_hd(self):
        assert self.collector._classify_gpu(
            "Intel(R) HD Graphics 620", "Intel Corporation", None
        ) == "核显"

    # === AMD 核显 vs 独显 ===
    def test_amd_igpu(self):
        assert self.collector._classify_gpu(
            "AMD Radeon Graphics", "Advanced Micro Devices, Inc.", None
        ) == "核显"

    def test_amd_vega_igpu(self):
        assert self.collector._classify_gpu(
            "AMD Radeon Vega 8 Graphics", "Advanced Micro Devices, Inc.", None
        ) == "核显"

    def test_amd_rx_discrete(self):
        """RX 独显即使名字带 Radeon 也不应判成核显"""
        assert self.collector._classify_gpu(
            "AMD Radeon RX 7900 XTX", "Advanced Micro Devices, Inc.", None
        ) == "独显"

    # === NVIDIA ===
    def test_nvidia_discrete_by_compat(self):
        assert self.collector._classify_gpu(
            "NVIDIA GeForce RTX 4070 Ti", "NVIDIA", None
        ) == "独显"

    def test_geforce_keyword_fallback(self):
        """厂商字段为空时靠名称关键词兜底"""
        assert self.collector._classify_gpu("GeForce GTX 1660", "", None) == "独显"

    # === 未知 ===
    def test_unknown_generic_name(self):
        assert self.collector._classify_gpu(
            "Video Controller (VGA Compatible)", "", None
        ) == "未知"


class TestVramResolution:
    """显存解析：注册表 qwMemorySize 优先，uint32 饱和值判为未知。"""

    def setup_method(self):
        self.collector = GPUCollector()

    def test_registry_value_wins(self):
        assert self.collector._resolve_vram_mb(0xFFFFFFFF, 11264) == 11264

    def test_saturated_adapter_ram_is_unknown(self):
        # 8GB/16GB 卡常见饱和值，不能当成 4095MB
        assert self.collector._resolve_vram_mb(0xFFFFFFFF, None) is None
        assert self.collector._resolve_vram_mb(0xFFF00000, None) is None

    def test_negative_adapter_ram_is_unknown(self):
        assert self.collector._resolve_vram_mb(-1048576, None) is None

    def test_valid_adapter_ram(self):
        assert self.collector._resolve_vram_mb(2 * 1024 ** 3, None) == 2048

    @patch.object(GPUCollector, "_read_vram_from_registry", return_value=11264)
    def test_parse_gpu_uses_registry_vram(self, mock_vram):
        gpu = MagicMock()
        gpu.Name = "NVIDIA GeForce RTX 2080 Ti"
        gpu.AdapterCompatibility = "NVIDIA"
        gpu.PNPDeviceID = "PCI\\VEN_10DE&DEV_1E07&SUBSYS_A0181B4C"
        gpu.AdapterRAM = 0xFFFFFFFF
        gpu.DriverVersion = "32.0.16.1088"
        gpu.DriverDate = None
        gpu.CurrentHorizontalResolution = 3840
        gpu.CurrentVerticalResolution = 2160
        gpu.CurrentRefreshRate = 120
        gpu.Status = "OK"
        gpu.ConfigManagerErrorCode = 0

        info = self.collector._parse_gpu(gpu)
        assert info["显存_MB"] == 11264


class TestFallbackPciInfo:
    """pci.ids 兜底翻译逻辑（数据库未加载时应安全返回原值）"""

    def setup_method(self):
        self.collector = GPUCollector()

    def test_non_pci_pnp_id_untouched(self):
        name, vendor = self.collector._fallback_pci_info(
            "未知显卡", "", r"PCI\VEN_10DE&DEV_2782"
        )
        # 数据库可能加载成功也可能失败，但不应抛异常
        assert isinstance(name, str)
        assert isinstance(vendor, str)

    def test_empty_pnp_id_passthrough(self):
        name, vendor = self.collector._fallback_pci_info("RTX 4070", "NVIDIA", None)
        assert name == "RTX 4070"
        assert vendor == "NVIDIA"

    def test_complete_info_skips_lookup(self):
        """名称与厂商齐全时不触发 pci.ids 查询，原样返回"""
        name, vendor = self.collector._fallback_pci_info(
            "GeForce RTX 4090", "NVIDIA", r"PCI\VEN_10DE&DEV_2684"
        )
        assert name == "GeForce RTX 4090"
        assert vendor == "NVIDIA"
