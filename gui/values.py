"""
gui/values.py - 采集数据的读取与显示格式化

采集结果统一用中文键名，单位编码在键名里（如 基础频率_MHz）。
这里集中做「键名 → 显示名」「数值 → 带单位文本」的转换，
页面只调用这些函数，不自己拼格式，避免总览页与详情页口径不一致。
"""

# 列表型数据所在的键名（memory 是「标量 + 列表」混合结构）
LIST_FIELD = {
    "memory": "内存条",
    "gpu": "显卡列表",
    "storage": "磁盘列表",
    "network": "网卡列表",
    "audio": "音频设备列表",
    "monitor": "显示器列表",
}

# 列表型类别（用于详情页选择模板）
LIST_CATEGORIES = set(LIST_FIELD) - {"memory"}

# 键名 → 显示名
_KEY_LABEL = {
    "基础频率_MHz": "基础频率",
    "频率_MHz": "频率",
    "L2缓存_MB": "L2 缓存",
    "L3缓存_MB": "L3 缓存",
    "总容量_GB": "总容量",
    "已使用_GB": "已使用",
    "使用率_百分比": "使用率",
    "插槽总数": "插槽总数",
    "已用插槽": "已用插槽",
    "通道模式": "通道模式",
    "当前负载_百分比": "当前负载",
    "负载_百分比": "负载",
    "显存_MB": "显存",
    "显存使用_MB": "显存使用",
    "速率_Gbps": "速率",
    "刷新率_Hz": "刷新率",
    "容量_GB": "容量",
    "已用_GB": "已用",
    "总计_GB": "总计",
    "电压_V": "电压",
    "位宽_bit": "位宽",
    "BIOS_厂商": "BIOS 厂商",
    "BIOS_版本": "BIOS 版本",
    "BIOS_日期": "BIOS 日期",
    "制造年份": "制造年份",
    "制造周": "制造周",
    "系统名称": "系统",
    "版本号": "版本",
    "系统架构": "架构",
    "安装日期": "安装日期",
    "上次启动": "上次启动",
    "系统目录": "系统目录",
    "用户名": "用户",
}

MISSING = "—"


def field_label(key: str) -> str:
    """字段显示名（去掉单位后缀，单位改由数值承担）"""
    return _KEY_LABEL.get(key, key.replace("_", " "))


# ---------------------------------------------------------------- 格式化

def human(value) -> str:
    """通用值格式化：None → —，布尔 → 支持/不支持，浮点去尾零"""
    if value is None or value == "":
        return MISSING
    if isinstance(value, bool):
        return "支持" if value else "不支持"
    if isinstance(value, float):
        text = f"{value:.1f}".rstrip("0").rstrip(".")
        return text or "0"
    if isinstance(value, (list, tuple)):
        return ", ".join(human(v) for v in value) if value else MISSING
    return str(value)


def mhz(value) -> str:
    """MHz → GHz（≥1000 时）"""
    if value is None:
        return MISSING
    try:
        number = float(value)
    except (TypeError, ValueError):
        return human(value)
    return f"{number / 1000:.2f} GHz" if number >= 1000 else f"{number:.0f} MHz"


def gb(value, digits: int = 1) -> str:
    """GB 数值加单位"""
    if value is None:
        return MISSING
    try:
        number = float(value)
    except (TypeError, ValueError):
        return human(value)
    return f"{number:.{digits}f} GB"


def mb_to_gb(value, digits: int = 1) -> str:
    """MB → GB 文本"""
    if value is None:
        return MISSING
    try:
        return f"{float(value) / 1024:.{digits}f} GB"
    except (TypeError, ValueError):
        return human(value)


def percent(value, digits: int = 0) -> str:
    """百分比文本（不带 % 号，交给调用方决定）"""
    if value is None:
        return MISSING
    try:
        return f"{float(value):.{digits}f}"
    except (TypeError, ValueError):
        return human(value)


# 键名 → 数值格式化
_KEY_VALUE = {
    "基础频率_MHz": mhz,
    "频率_MHz": lambda v: f"{human(v)} MHz",
    "L2缓存_MB": lambda v: f"{human(v)} MB",
    "L3缓存_MB": lambda v: f"{human(v)} MB",
    "总容量_GB": gb,
    "已使用_GB": gb,
    "使用率_百分比": lambda v: f"{percent(v, 1)} %",
    "当前负载_百分比": lambda v: f"{percent(v, 1)} %",
    "负载_百分比": lambda v: f"{percent(v, 0)} %",
    "显存_MB": mb_to_gb,
    "显存使用_MB": mb_to_gb,
    "速率_Gbps": lambda v: f"{human(v)} Gbps",
    "刷新率_Hz": lambda v: f"{human(v)} Hz",
    "容量_GB": gb,
    "已用_GB": gb,
    "总计_GB": gb,
    "电压_V": lambda v: f"{human(v)} V",
    "位宽_bit": lambda v: f"{human(v)} bit",
}


def field_value(key: str, value) -> str:
    """字段值格式化（含单位）；缺值统一显示为 —，不带单位后缀"""
    if value is None or value == "":
        return MISSING
    formatter = _KEY_VALUE.get(key)
    return formatter(value) if formatter else human(value)


# ---------------------------------------------------------------- 数据访问

def get(data, key: str, default=MISSING):
    """安全取值，None 也视为缺失"""
    if not isinstance(data, dict):
        return default
    value = data.get(key)
    return default if value is None else value


def items(data, category: str) -> list[dict]:
    """取类别下的设备列表（raw list 或 嵌套在命名键下）"""
    if isinstance(data, list):
        return [x for x in data if isinstance(x, dict)]
    if not isinstance(data, dict):
        return []
    field = LIST_FIELD.get(category)
    if field and isinstance(data.get(field), list):
        return [x for x in data[field] if isinstance(x, dict)]
    # 兜底：找出第一个 dict 列表
    for value in data.values():
        if isinstance(value, list) and all(isinstance(x, dict) for x in value):
            return value
    return []


def list_field(category: str) -> str | None:
    return LIST_FIELD.get(category)


def flat_rows(data: dict, skip: tuple[str, ...] = (),
              hide_missing: bool = True) -> list[tuple[str, str]]:
    """提取标量字段为 (显示名, 显示值) 列表，按原顺序

    hide_missing=True 时略过 None/空串（设备卡里避免出现一排「—」）。
    """
    rows = []
    for key, value in data.items():
        if key.startswith("_") or key in skip:
            continue
        if isinstance(value, (list, dict)):
            continue
        if hide_missing and (value is None or value == ""):
            continue
        rows.append((field_label(key), field_value(key, value)))
    return rows


def warnings(data) -> list[str]:
    """采集器写入的 _警告 字段"""
    if not isinstance(data, dict):
        return []
    out = []
    for key, value in data.items():
        if key.startswith("_警告") or key == "_警告":
            out.append(human(value))
    return out


# ---------------------------------------------------------------- 组合计算

def disk_usage(disk: dict) -> tuple[float, float]:
    """磁盘 (已用 GB, 总计 GB)：优先按分区求和，否则用容量"""
    partitions = disk.get("分区") if isinstance(disk, dict) else None
    used = total = 0.0
    if isinstance(partitions, list):
        for part in partitions:
            if not isinstance(part, dict):
                continue
            used += float(part.get("已用_GB") or 0)
            total += float(part.get("总计_GB") or 0)
    if total <= 0:
        total = float(disk.get("容量_GB") or 0) if isinstance(disk, dict) else 0.0
    if used <= 0:
        used = 0.0
    return used, total


def fraction(used, total) -> float:
    """安全占比，0 到 1"""
    try:
        total = float(total)
        if total <= 0:
            return 0.0
        return max(0.0, min(1.0, float(used) / total))
    except (TypeError, ValueError):
        return 0.0


def pick_primary_gpu(gpus: list[dict]) -> dict | None:
    """优先独立显卡，其次显存最大的"""
    if not gpus:
        return None
    dedicated = [g for g in gpus if str(g.get("类型", "")).strip() in ("独显", "独立")]
    pool = dedicated or gpus
    return max(pool, key=lambda g: float(g.get("显存_MB") or 0))
