"""
tests/test_collectors.py - 采集模块测试（Mock WMI）

通过 Mock WMI 返回数据验证各模块的解析逻辑，不依赖真实硬件。
"""
import pytest
from unittest.mock import patch, MagicMock


# ============================================================
# 辅助：创建模拟 WMI 对象
# ============================================================

def make_wmi_obj(**kwargs):
    """创建一个属性可访问的模拟对象（模拟 WMI 返回的 COM 对象）"""
    obj = MagicMock()
    for k, v in kwargs.items():
        setattr(obj, k, v)
    return obj


# ============================================================
# CPU 模块
# ============================================================

class TestCPUCollector:
    @patch("collectors.cpu.get_wmi")
    @patch("collectors.cpu.winreg")
    @patch("collectors.cpu.CPUCollector._get_cpu_load", return_value=15.0)
    def test_basic_fields(self, mock_load, mock_winreg, mock_wmi):
        mock_c = MagicMock()
        mock_wmi.return_value = mock_c
        mock_c.query.return_value = [
            make_wmi_obj(
                Name="Intel(R) Core(TM) i9-14900K",
                Manufacturer="GenuineIntel",
                Architecture=9,
                SocketDesignation="LGA1700",
                NumberOfCores=24,
                NumberOfLogicalProcessors=32,
                MaxClockSpeed=3200,
                L2CacheSize=32768,
                L3CacheSize=36864,
            )
        ]
        mock_c.Win32_ComputerSystem.return_value = [
            make_wmi_obj(HypervisorPresent=True)
        ]
        # 注册表返回
        mock_winreg.OpenKey.return_value = MagicMock()
        mock_winreg.QueryValueEx.return_value = (
            "Intel64 Family 6 Model 183 Stepping 1", 4
        )
        mock_winreg.HKEY_LOCAL_MACHINE = 0x80000002

        from collectors.cpu import CPUCollector
        collector = CPUCollector()
        result = collector.collect()

        assert result["名称"] == "Intel(R) Core(TM) i9-14900K"
        assert result["核心数"] == 24
        assert result["线程数"] == 32
        assert result["架构"] == "x64"
        assert result["L2缓存_MB"] == 32
        assert result["L3缓存_MB"] == 36
        assert result["当前负载_百分比"] == 15.0

    @patch("collectors.cpu.get_wmi")
    def test_no_processor_raises(self, mock_wmi):
        mock_c = MagicMock()
        mock_wmi.return_value = mock_c
        mock_c.query.return_value = []

        from collectors.cpu import CPUCollector
        from core.base import CollectorError
        with pytest.raises(CollectorError):
            CPUCollector().collect()

    @patch("collectors.cpu.get_wmi")
    @patch("collectors.cpu.winreg")
    @patch("collectors.cpu.CPUCollector._get_cpu_load", return_value=15.0)
    def test_uses_projection_query(self, mock_load, mock_winreg, mock_wmi):
        """必须用投影查询，避免 SELECT * 触发慢速 LoadPercentage。"""
        mock_c = MagicMock()
        mock_wmi.return_value = mock_c
        mock_c.query.return_value = [make_wmi_obj(
            Name="Test CPU", Manufacturer="Test", Architecture=9,
            SocketDesignation="LGA1700", NumberOfCores=8,
            NumberOfLogicalProcessors=16, MaxClockSpeed=3000,
            L2CacheSize=2048, L3CacheSize=16384,
        )]
        mock_c.Win32_ComputerSystem.return_value = []
        mock_winreg.OpenKey.return_value = MagicMock()
        mock_winreg.QueryValueEx.return_value = ("AuthenticAMD Family 25", 4)

        from collectors.cpu import CPUCollector
        CPUCollector().collect()

        query = mock_c.query.call_args[0][0]
        assert "Win32_Processor" in query
        assert "LoadPercentage" not in query
        assert "NumberOfLogicalProcessors" in query
        mock_c.Win32_Processor.assert_not_called()

    def test_cpu_load_reuses_sample_after_first_call(self, monkeypatch):
        """进程内第二次采集不应再阻塞 0.1s。"""
        import collectors.cpu as cpu_mod

        monkeypatch.setattr(cpu_mod, "_CPU_LOAD_PRIMED", False)
        with patch("psutil.cpu_percent", side_effect=[0.0, 12.5, 20.0]) as mock_cpu:
            assert cpu_mod.CPUCollector()._get_cpu_load() == 12.5
            assert cpu_mod.CPUCollector()._get_cpu_load() == 20.0

        assert mock_cpu.call_args_list[1].kwargs["interval"] == 0.1
        assert mock_cpu.call_args_list[2].kwargs["interval"] is None


# ============================================================
# OS 模块
# ============================================================

class TestOSCollector:
    @patch("collectors.os_info.get_wmi")
    def test_projection_query(self, mock_wmi):
        """OS 信息应使用投影查询，字段解析保持不变。"""
        mock_c = MagicMock()
        mock_wmi.return_value = mock_c
        mock_c.query.return_value = [make_wmi_obj(
            Caption="Microsoft Windows 11 专业版",
            Version="10.0.26100",
            BuildNumber="26100",
            OSArchitecture="64 位",
            InstallDate="20250323183420.000000+480",
            LastBootUpTime="20261020205200.500000+480",
            WindowsDirectory="C:\\WINDOWS",
        )]

        from collectors.os_info import OSCollector
        result = OSCollector().collect()

        assert result["系统名称"] == "Microsoft Windows 11 专业版"
        assert result["版本号"] == "10.0.26100 (26100)"
        assert result["安装日期"] == "2025-03-23"
        assert result["上次启动"] == "2026-10-20 20:52:00"
        assert result["系统目录"] == "C:\\WINDOWS"

        query = mock_c.query.call_args[0][0]
        assert "Win32_OperatingSystem" in query
        assert "SELECT Caption" in query
        mock_c.Win32_OperatingSystem.assert_not_called()


# ============================================================
# Storage 模块
# ============================================================

class TestStorageCollector:
    @patch("collectors.storage.get_wmi")
    @patch("collectors.storage.StorageCollector._get_physical_disk_map",
           return_value={})
    def test_basic_fields(self, mock_physical, mock_wmi):
        mock_c = MagicMock()
        mock_wmi.return_value = mock_c

        drive = make_wmi_obj(
            Model="Samsung SSD 980 PRO 1TB",
            InterfaceType="SCSI",
            PNPDeviceID="PCI\\VEN_144D&DEV_A808&SUBSYS_0000144D",
            Size="1000204886016",
            FirmwareRevision="5B2QGXA7",
            SerialNumber="S5GXNY0R123456",
            DeviceID="\\\\.\\PHYSICALDRIVE0",
            Index=0,
        )
        mock_c.Win32_DiskDrive.return_value = [drive]
        mock_c.Win32_LogicalDisk.return_value = []

        from collectors.storage import StorageCollector
        collector = StorageCollector()
        result = collector.collect()

        disk = result["磁盘列表"][0]
        assert disk["型号"] == "Samsung SSD 980 PRO 1TB"
        assert disk["类型"] == "SSD"  # 980 关键词匹配
        assert disk["容量_GB"] == 931.5
        assert disk["固件"] == "5B2QGXA7"

    @patch("collectors.storage.get_wmi")
    @patch("collectors.storage.StorageCollector._get_physical_disk_map",
           return_value={})
    def test_nvme_detection(self, mock_physical, mock_wmi):
        mock_c = MagicMock()
        mock_wmi.return_value = mock_c

        drive = make_wmi_obj(
            Model="GXF-512 PRO",
            InterfaceType="SCSI",
            PNPDeviceID="PCI\\VEN_1E4B&DEV_1202&NVME",
            Size="512110190592",
            FirmwareRevision="SN08193",
            SerialNumber="0000_0000",
            DeviceID="\\\\.\\PHYSICALDRIVE1",
            Index=1,
        )
        mock_c.Win32_DiskDrive.return_value = [drive]
        mock_c.Win32_LogicalDisk.return_value = []

        from collectors.storage import StorageCollector
        result = StorageCollector().collect()
        disk = result["磁盘列表"][0]
        assert disk["接口"] == "NVMe"
        assert disk["类型"] == "SSD"

    @patch("collectors.storage.get_wmi")
    @patch("collectors.storage.StorageCollector._get_physical_disk_map",
           return_value={0: {"media_type": 4, "bus_type": 11}})
    def test_msft_physical_disk_overrides_keywords(self, mock_physical, mock_wmi):
        """MediaType/BusType 应优先于型号关键词（修 SATA SSD 被猜成 NVMe/HDD）。"""
        mock_c = MagicMock()
        mock_wmi.return_value = mock_c

        drive = make_wmi_obj(
            Model="Seagate FireCuda 530",  # 旧关键词会因 seagate 判 HDD
            InterfaceType="SCSI",
            PNPDeviceID="PCI\\VEN_1BB1&DEV_4018",
            Size="1000204886016",
            FirmwareRevision="SU6SM001",
            SerialNumber="000000000000",
            DeviceID="\\\\.\\PHYSICALDRIVE0",
            Index=0,
        )
        mock_c.Win32_DiskDrive.return_value = [drive]
        mock_c.Win32_LogicalDisk.return_value = []

        from collectors.storage import StorageCollector
        disk = StorageCollector().collect()["磁盘列表"][0]
        assert disk["类型"] == "SSD"
        assert disk["接口"] == "SATA"

    @patch("collectors.storage.get_wmi")
    @patch("collectors.storage.StorageCollector._get_physical_disk_map",
           return_value={})
    def test_scsi_ssd_is_not_misreported_as_nvme(self, mock_physical, mock_wmi):
        """SCSI + 型号含 SSD 只能是 SATA，不能推断成 NVMe。"""
        mock_c = MagicMock()
        mock_wmi.return_value = mock_c

        drive = make_wmi_obj(
            Model="WD Blue SA510 1TB",
            InterfaceType="SCSI",
            PNPDeviceID="PCI\\VEN_15B7&DEV_5041",
            Size="1000204886016",
            FirmwareRevision="1.0",
            SerialNumber="0000",
            DeviceID="\\\\.\\PHYSICALDRIVE0",
            Index=0,
        )
        mock_c.Win32_DiskDrive.return_value = [drive]
        mock_c.Win32_LogicalDisk.return_value = []

        from collectors.storage import StorageCollector
        disk = StorageCollector().collect()["磁盘列表"][0]
        assert disk["接口"] == "SATA"

    @patch("collectors.storage.get_wmi")
    @patch("collectors.storage.StorageCollector._get_physical_disk_map",
           return_value={})
    def test_no_drives_raises(self, mock_physical, mock_wmi):
        mock_c = MagicMock()
        mock_wmi.return_value = mock_c
        mock_c.Win32_DiskDrive.return_value = []

        from collectors.storage import StorageCollector
        from core.base import CollectorError
        with pytest.raises(CollectorError):
            StorageCollector().collect()


# ============================================================
# Memory 模块
# ============================================================

class TestMemoryCollector:
    @patch("psutil.virtual_memory")
    @patch("collectors.memory.get_wmi")
    def test_basic_fields(self, mock_wmi, mock_vmem):
        mock_c = MagicMock()
        mock_wmi.return_value = mock_c

        stick = make_wmi_obj(
            DeviceLocator="DIMM_A1",
            Manufacturer="Kingston",
            PartNumber="KF560C36BB-16",
            Capacity="17179869184",  # 16 GB
            SMBIOSMemoryType=34,  # DDR5
            Speed=6000,
            DataWidth=64,
            ConfiguredVoltage=1350,
            SerialNumber="ABC123",
        )
        mock_c.Win32_PhysicalMemory.return_value = [stick, stick]
        mock_c.Win32_PhysicalMemoryArray.return_value = [
            make_wmi_obj(MemoryDevices=4)
        ]

        mock_vmem.return_value = make_wmi_obj(
            total=34359738368, used=17179869184, percent=50.0
        )

        from collectors.memory import MemoryCollector
        result = MemoryCollector().collect()

        assert result["已用插槽"] == 2
        assert result["插槽总数"] == 4
        assert result["通道模式"] == "双通道"
        assert len(result["内存条"]) == 2
        assert result["内存条"][0]["类型"] == "DDR5"
        assert result["内存条"][0]["频率_MHz"] == 6000
        assert result["内存条"][0]["电压_V"] == 1.35

    def test_parse_cl(self):
        """CL 值从型号字符串解析（含各种厂商格式）"""
        from collectors.memory import MemoryCollector
        collector = MemoryCollector()

        # "CL36-44-44 D5-7200" 等显式格式 → 解析出 CL
        assert collector._parse_cl("CL36-44-44 D5-7200") == 36
        assert collector._parse_cl("CL30-40-40 96") == 30
        assert collector._parse_cl("cl28-34-34") == 28
        # 不含显式 CL 的厂商型号 → None（不误报）
        assert collector._parse_cl("F5-7200J3646G24GX2-TZ5RK") is None
        assert collector._parse_cl("M378A1G43EB1") is None
        assert collector._parse_cl("") is None
        assert collector._parse_cl(None) is None


# ============================================================
# Audio 模块
# ============================================================

class TestAudioCollector:
    @patch("collectors.audio.get_wmi")
    def test_location_detection(self, mock_wmi):
        mock_c = MagicMock()
        mock_wmi.return_value = mock_c

        devices = [
            make_wmi_obj(
                Name="Realtek High Definition Audio",
                Manufacturer="Realtek",
                PNPDeviceID="HDAUDIO\\FUNC_01&VEN_10EC",
                Status="OK",
            ),
            make_wmi_obj(
                Name="NVIDIA High Definition Audio",
                Manufacturer="NVIDIA",
                PNPDeviceID="HDAUDIO\\FUNC_01&VEN_10DE",
                Status="OK",
            ),
            make_wmi_obj(
                Name="USB Audio Device",
                Manufacturer="(Generic USB Audio)",
                PNPDeviceID="USB\\VID_046D&PID_0A66",
                Status="OK",
            ),
        ]
        mock_c.Win32_SoundDevice.return_value = devices

        from collectors.audio import AudioCollector
        result = AudioCollector().collect()
        audio_list = result["音频设备列表"]

        assert audio_list[0]["位置"] == "板载"
        assert audio_list[1]["位置"] == "GPU 附带 (HDMI/DP)"
        assert audio_list[2]["位置"] == "USB 外接"

    @patch("collectors.audio.get_wmi")
    def test_status_mapping(self, mock_wmi):
        mock_c = MagicMock()
        mock_wmi.return_value = mock_c
        mock_c.Win32_SoundDevice.return_value = [
            make_wmi_obj(Name="Test", Manufacturer="Test",
                         PNPDeviceID="PCI\\VEN_0000", Status="OK")
        ]

        from collectors.audio import AudioCollector
        result = AudioCollector().collect()
        assert result["音频设备列表"][0]["状态"] == "正常"


# ============================================================
# Network 模块
# ============================================================

class TestNetworkCollector:
    @patch("collectors.network.NetworkCollector._get_wifi_info", return_value=None)
    @patch("collectors.network.get_wmi")
    def test_basic_adapter(self, mock_wmi, mock_wifi):
        mock_c = MagicMock()
        mock_wmi.return_value = mock_c

        adapter = make_wmi_obj(
            Name="Realtek Gaming 2.5GbE",
            AdapterType="Ethernet 802.3",
            Manufacturer="Realtek",
            MACAddress="D8:43:AE:8B:1A:01",
            Speed="2500000000",
            NetConnectionStatus=2,
            NetConnectionID="以太网",
            PNPDeviceID="PCI\\VEN_10EC&DEV_8125",
            Index=1,
        )
        mock_c.Win32_NetworkAdapter.return_value = [adapter]
        mock_c.query.return_value = [
            make_wmi_obj(
                Index=1,
                IPAddress=["192.168.1.100", "fe80::1"],
                IPSubnet=["255.255.255.0"],
                DefaultIPGateway=["192.168.1.1"],
            )
        ]

        from collectors.network import NetworkCollector
        result = NetworkCollector().collect()
        nic = result["网卡列表"][0]

        assert nic["名称"] == "Realtek Gaming 2.5GbE"
        assert nic["类型"] == "以太网"
        assert nic["速率_Gbps"] == 2.5
        assert nic["状态"] == "已连接"
        assert nic["IPv4"] == "192.168.1.100"
        assert nic["网关"] == "192.168.1.1"

        # 网卡配置必须用投影查询，避免 SELECT * 的额外开销
        config_query = mock_c.query.call_args[0][0]
        assert "Win32_NetworkAdapterConfiguration" in config_query
        assert "SELECT Index" in config_query
        mock_c.Win32_NetworkAdapterConfiguration.assert_not_called()

    @patch("collectors.network.NetworkCollector._get_wifi_info", return_value=None)
    @patch("collectors.network.get_wmi")
    def test_speed_overflow_filtered(self, mock_wmi, mock_wifi):
        """int64 最大值应被过滤"""
        mock_c = MagicMock()
        mock_wmi.return_value = mock_c

        adapter = make_wmi_obj(
            Name="Intel Wi-Fi 6E",
            AdapterType="Wireless",
            Manufacturer="Intel",
            MACAddress="AA:BB:CC:DD:EE:FF",
            Speed="9223372036854775807",  # int64 max
            NetConnectionStatus=7,
            NetConnectionID="WLAN",
            PNPDeviceID="PCI\\VEN_8086",
            Index=2,
        )
        mock_c.Win32_NetworkAdapter.return_value = [adapter]
        mock_c.query.return_value = []

        from collectors.network import NetworkCollector
        result = NetworkCollector().collect()
        nic = result["网卡列表"][0]
        assert nic["速率_Gbps"] is None  # 溢出值被过滤

    def test_signal_percent_to_dbm(self):
        """Windows 信号质量 0~100 对应 -100 ~ -50 dBm。"""
        from collectors.network import NetworkCollector

        assert NetworkCollector._signal_percent_to_dbm(0) == -100
        assert NetworkCollector._signal_percent_to_dbm(50) == -75
        assert NetworkCollector._signal_percent_to_dbm(80) == -60
        assert NetworkCollector._signal_percent_to_dbm(100) == -50
        # 越界值应被夹紧，不能出现正 dBm
        assert NetworkCollector._signal_percent_to_dbm(120) == -50
        assert NetworkCollector._signal_percent_to_dbm(-5) == -100

    @patch("utils.powershell.run_command")
    def test_wifi_info_signal_parsing(self, mock_run):
        """netsh 解析出的信号百分比应按正确公式转成 dBm。"""
        mock_run.return_value = (
            "    SSID                   : TestWiFi\n"
            "    Signal                 : 80%\n"
        )
        from collectors.network import NetworkCollector
        info = NetworkCollector()._get_wifi_info()
        assert info["SSID"] == "TestWiFi"
        assert info["信号_dBm"] == -60
