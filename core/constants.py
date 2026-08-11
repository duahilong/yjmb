"""
core/constants.py - 全局共享常量

避免 VERSION、排序权重、brief 字段等在多处重复定义。
"""

# 工具版本号：优先从包元数据读取，fallback 到硬编码值
try:
    from importlib.metadata import version as _pkg_version
    VERSION = _pkg_version("hwinfo")
except Exception:
    VERSION = "0.1.0"

# 模块显示排序权重
ORDER_MAP = {
    "os": 10,
    "motherboard": 20,
    "cpu": 30,
    "memory": 40,
    "gpu": 50,
    "storage": 60,
    "network": 70,
    "audio": 80,
    "monitor": 90,
}

# 所有可用的硬件类别（按 order 排序）
ALL_CATEGORIES = sorted(ORDER_MAP.keys(), key=lambda k: ORDER_MAP[k])

# 类别中文显示名（CLI/GUI 共用）
CATEGORY_LABELS = {
    "os": "操作系统",
    "motherboard": "主板",
    "cpu": "处理器",
    "memory": "内存",
    "gpu": "显卡",
    "storage": "存储",
    "network": "网络",
    "audio": "音频",
    "monitor": "显示器",
}

# brief 模式：顶层字段过滤
BRIEF_FIELDS_MAP = {
    "os": ["系统名称", "版本号", "系统架构"],
    "motherboard": ["厂商", "型号", "BIOS_版本"],
    "cpu": ["名称", "核心数", "线程数", "基础频率_MHz"],
    "memory": ["总容量_GB", "已用插槽", "通道模式"],
    "gpu": [],           # 列表型，由 ITEM_BRIEF_FIELDS_MAP 控制
    "storage": [],
    "network": [],
    "audio": [],
    "monitor": [],
}

# brief 模式：列表型数据中每个项的字段过滤
ITEM_BRIEF_FIELDS_MAP = {
    "memory": ["插槽", "厂商", "容量_GB", "类型", "频率_MHz", "CL", "电压_V"],
    "gpu": ["名称", "显存_MB", "驱动版本"],
    "storage": ["型号", "类型", "容量_GB"],
    "network": ["名称", "驱动版本"],
    "audio": ["名称", "驱动版本"],
    "monitor": ["型号", "分辨率", "刷新率_Hz"],
}
