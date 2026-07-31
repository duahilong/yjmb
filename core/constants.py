"""
core/constants.py - 全局共享常量

避免 VERSION、排序权重、brief 字段等在多处重复定义。
"""

# 工具版本号（唯一来源）
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
    "memory": ["插槽", "容量_GB", "类型", "频率_MHz"],
    "gpu": ["名称", "显存_MB", "驱动版本"],
    "storage": ["型号", "类型", "容量_GB"],
    "network": ["名称", "状态", "IPv4"],
    "audio": ["名称", "状态"],
    "monitor": ["型号", "分辨率", "刷新率_Hz"],
}
