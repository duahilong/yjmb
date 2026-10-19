"""两份 GUI 原型共用的模拟数据（取自项目真机采集结果）。"""

HOST = "DESKTOP-7F3A"
MODEL = "Z790MPOWER (MS-7E01)"
VENDOR = "MSI"
OS_NAME = "Windows 11 专业工作站版"
OS_VERSION = "10.0.26300"
OS_ARCH = "64 位"

CPU = "Genuine Intel(R) 0000"
CPU_CORES = 24
CPU_THREADS = 24
CPU_FREQ = "1.69 GHz"

RAM_TOTAL = "48 GB"
RAM_DETAIL = "DDR5 · 7200 · CL36"
RAM_SLOTS = "2 / 4 插槽 · 双通道"

GPU = "NVIDIA GeForce RTX 2080 Ti"
GPU_VRAM = "11 GB"
GPU_DRIVER = "32.0.16.1088"
IGPU = "Intel UHD Graphics"
IGPU_DRIVER = "32.0.101.7092"

DISK_1 = "Samsung SSD 980 PRO 1TB"
DISK_1_SIZE = "931.5 GB"
DISK_1_IF = "NVMe"
DISK_1_FW = "5B2QGXA7"
DISK_2 = "GXF-512 PRO"
DISK_2_SIZE = "476.9 GB"
DISK_2_IF = "SATA"
DISK_2_FW = "—"
DISK_TOTAL = "1.4 TB"

WIFI = "Intel(R) Wi-Fi 6E AX211 160MHz"
WIFI_DRIVER = "23.140.0.3"
LAN = "Realtek Gaming 2.5GbE Family Controller"
LAN_DRIVER = "10.75.324.2025"

AUDIO = "Realtek High Definition Audio"
AUDIO_DRIVER = "6.0.8988.1"

MONITOR_1 = "G322U"
MONITOR_1_SPEC = "3840×2160 · 120 Hz"
MONITOR_2 = "PHL 275M1RZ"
MONITOR_2_SPEC = "1920×1080 · 60 Hz"

COLLECTED_AT = "14:32:08"
ELAPSED = "1.73s"

# 类别, 设备/型号, 关键规格, 驱动/备注
SPEC_ROWS = [
    ("操作系统", OS_NAME, f"{OS_VERSION} · {OS_ARCH}", "系统正常"),
    ("主板", "MSI Z790MPOWER (MS-7E01)", "BIOS P.60 · UEFI", "Z790 芯片组"),
    ("处理器", CPU, f"{CPU_CORES} 核 / {CPU_THREADS} 线程 · {CPU_FREQ}", "LGA1700 · x64"),
    ("内存", "Golden Empire DDR5", f"{RAM_TOTAL} · 7200 MHz · CL36", RAM_SLOTS),
    ("显卡", GPU, f"{GPU_VRAM} · 独显", f"驱动 {GPU_DRIVER}"),
    ("显卡", IGPU, "2048 MB · 核显", f"驱动 {IGPU_DRIVER}"),
    ("存储", DISK_1, f"{DISK_1_SIZE} · {DISK_1_IF}", f"固件 {DISK_1_FW}"),
    ("存储", DISK_2, f"{DISK_2_SIZE} · {DISK_2_IF}", f"固件 {DISK_2_FW}"),
    ("网络", WIFI, "无线 · Wi-Fi 6E", f"驱动 {WIFI_DRIVER}"),
    ("网络", LAN, "以太网 · 2.5 Gbps", f"驱动 {LAN_DRIVER}"),
    ("音频", AUDIO, "板载", f"驱动 {AUDIO_DRIVER}"),
    ("显示器", MONITOR_1, MONITOR_1_SPEC, "2023 年"),
    ("显示器", MONITOR_2, MONITOR_2_SPEC, "2021 年"),
]

DEVICE_ROWS = [
    ("处理器", CPU, "正常", "24C / 24T"),
    ("内存", "Golden Empire DDR5 · 2 条", "正常", "7200 MHz"),
    ("显卡", GPU, "正常", GPU_DRIVER),
    ("存储", DISK_1, "正常", DISK_1_FW),
    ("网络", WIFI, "已连接", WIFI_DRIVER),
    ("音频", AUDIO, "正常", AUDIO_DRIVER),
    ("显示器", MONITOR_1, "活动", "3840×2160"),
]
