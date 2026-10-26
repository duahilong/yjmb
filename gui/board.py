"""
gui/board.py - 单屏硬件信息画板

把定稿原型（prototypes/legacy_rows）的版式搬进 Qt：

    纯白底 · 蓝色粗体分类名 · 每个字段独占一行 · 无卡片 / 圆角 / 分隔线
    按窗口宽度动态分栏（1–6 栏）
    二分字号 8–40px，找出能一屏放下且最大的字号

数据来自 CollectResult.data（中文键名，单位编码在键名里）。
这里自己格式化，口径与原型一致：

    基础频率    1,690 MHz      （不转 GHz）
    显存        11,264 MB      （不转 GB）
    整数        千分位
    缺失        —
    布尔        支持 / 不支持

画板不滚动；只有搜索结果的单栏视图在内容超高时才允许纵向滚动。
"""
from __future__ import annotations

import re
import socket
from dataclasses import dataclass, field
from functools import lru_cache

from PySide6.QtCore import QRectF, QSize, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QFont, QFontMetricsF, QPainter
from PySide6.QtWidgets import QSizePolicy, QWidget

from core.constants import CATEGORY_LABELS
from gui import theme


# ============================================================
# 类别
# ============================================================

# 与手写原版一致的顺序（与 core.constants.ALL_CATEGORIES 的排序不同）
CATEGORY_ORDER = (
    "os", "cpu", "motherboard", "memory", "gpu",
    "storage", "network", "audio", "monitor",
)

# 精简档：每类 / 每类设备保留的字段（原始 key）
BRIEF = {
    "os": frozenset({"系统名称", "版本号", "系统架构", "安装日期", "上次启动", "用户名"}),
    "motherboard": frozenset({"厂商", "型号", "芯片组", "BIOS_版本", "BIOS_日期", "UEFI", "TPM"}),
    "cpu": frozenset({"名称", "插槽", "核心数", "线程数", "基础频率_MHz",
                      "L2缓存_MB", "L3缓存_MB", "虚拟化", "当前负载_百分比"}),
    "memory": frozenset({"总容量_GB", "已使用_GB", "使用率_百分比",
                         "插槽总数", "已用插槽", "通道模式"}),
    "memoryStick": frozenset({"厂商", "型号", "容量_GB", "类型", "频率_MHz",
                              "CL", "电压_V", "序列号"}),
    "gpu": frozenset({"厂商", "显存_MB", "驱动版本", "驱动日期",
                      "当前分辨率", "刷新率_Hz", "负载_百分比"}),
    "gpuIntegrated": frozenset({"显存_MB", "驱动版本"}),
    "disk": frozenset({"容量_GB", "固件", "序列号"}),
    "partition": frozenset({"已用_GB", "总计_GB"}),
    "network": frozenset({"厂商", "MAC", "速率_Gbps", "状态", "IPv4",
                          "子网掩码", "网关", "驱动版本"}),
    "audio": frozenset({"厂商", "驱动版本", "状态"}),
    "monitor": frozenset({"厂商", "制造年份", "制造周", "分辨率", "刷新率_Hz"}),
}

# 键名里编码的单位；最后一段命中时才拆成「显示名 + 单位」
UNITS = frozenset({
    "MHz", "GHz", "GB", "MB", "TB", "KB", "Gbps", "Mbps",
    "Hz", "V", "W", "bit", "百分比", "秒",
})

_MONO_RE = re.compile(r"序列号|MAC|系统目录|固件")
_CJK_GAP = re.compile(r"(?<=[A-Za-z0-9])(?=[\u4e00-\u9fa5])")
_RAW_NUMBER_KEY = re.compile(r"年份|制造周|日期|版本")

# 绘制文本用的标志位（PySide6 的 Flag 组合转成 int 最稳）
_ALIGN_LT = int(Qt.AlignmentFlag.AlignLeft) | int(Qt.AlignmentFlag.AlignTop)
_ALIGN_RT = int(Qt.AlignmentFlag.AlignRight) | int(Qt.AlignmentFlag.AlignTop)
_WRAP_LT = _ALIGN_LT | int(Qt.TextFlag.TextWordWrap)
_ALIGN_CENTER = int(Qt.AlignmentFlag.AlignCenter)


# ============================================================
# 格式化
# ============================================================

def split_key(key: str) -> tuple[str, str | None]:
    """基础频率_MHz → ("基础频率", "MHz")"""
    index = key.rfind("_")
    if index > 0 and key[index + 1:] in UNITS:
        label = key[:index].replace("_", " ")
        return _CJK_GAP.sub(" ", label), key[index + 1:]
    return _CJK_GAP.sub(" ", key.replace("_", " ")), None


def is_mono(label: str) -> bool:
    return bool(_MONO_RE.search(label))


# 序列号 / MAC 这类长串没有空格，Qt 的 TextWordWrap 不会断行（会被裁掉）。
# 插零宽空格给出断点，等价于原型的 overflow-wrap: break-word，但优先在分隔符处断。
_SOFT_BREAK = re.compile(r"([_:/\\.-])")


def soft_breaks(text: str) -> str:
    """在分隔符后插入零宽空格，让长串能换行"""
    return _SOFT_BREAK.sub(lambda m: m.group(1) + "\u200b", text)


def number(value) -> str:
    """整数带千分位，浮点保留原样（47.7 → "47.7"）"""
    if isinstance(value, bool):
        return "支持" if value else "不支持"
    if isinstance(value, int):
        return f"{value:,}"
    if isinstance(value, float):
        if value.is_integer():
            return f"{int(value):,}"
        return f"{value:g}"
    return str(value)


def status_kind(status) -> str:
    """状态文本 → 语气：ok / off / neutral"""
    text = "" if status is None else str(status)
    if re.search(r"断开|未连接|停用|禁用", text):
        return "off"
    if re.search(r"已连接|活动|正常|已检测|运行|已启用", text):
        return "ok"
    return "neutral"


def _plain(value) -> str:
    """搜索用纯文本"""
    if value is None:
        return ""
    if isinstance(value, bool):
        return "支持" if value else "不支持"
    if isinstance(value, (list, tuple)):
        return " ".join(_plain(v) for v in value)
    return str(value)


def format_value(key: str, value) -> tuple[str, str]:
    """返回 (显示文本, 语气)。语气用于上色：'' / null / ok / off / neutral"""
    if value is None or value == "":
        return "—", "null"
    if isinstance(value, bool):
        return ("支持", "") if value else ("不支持", "no")
    if isinstance(value, (list, tuple)):
        if not value:
            return "—", "null"
        return " · ".join(_plain(v) for v in value), ""

    unit = split_key(key)[1]
    if key == "状态":
        text = str(value)
        return text, status_kind(text)
    if unit == "百分比":
        return f"{number(value)}%", ""
    if unit == "秒":
        return f"{number(value)} 秒", ""
    if unit and isinstance(value, (int, float)) and not isinstance(value, bool):
        return f"{number(value)} {unit}", ""
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if _RAW_NUMBER_KEY.search(key):
            return str(value), ""
        return number(value), ""
    return str(value), ""


# ============================================================
# 模型
# ============================================================

@dataclass(slots=True)
class Row:
    label: str
    text: str
    tone: str = ""
    mono: bool = False
    search: str = ""


@dataclass(slots=True)
class Device:
    name: str
    meta: str = ""
    tone: str = ""
    part: bool = False


@dataclass(slots=True)
class Cat:
    key: str
    name: str
    meta: str = ""


@dataclass(slots=True)
class Unit:
    """一台设备（或一个无设备标题的类别块）"""
    ci: int
    di: int
    cat: Cat
    dev: Device | None
    rows: list[Row] = field(default_factory=list)


@dataclass(slots=True)
class Item:
    """分栏的最小单位：一个字段行"""
    ci: int
    di: int
    cat: Cat
    dev: Device | None
    row: Row


def make_row(key: str, value) -> Row:
    label, unit = split_key(key)
    text, tone = format_value(key, value)
    mono = is_mono(label)
    return Row(
        label=label,
        text=soft_breaks(text) if mono else text,
        tone=tone,
        mono=mono,
        search=f"{label} {unit or ''} {_plain(value)}".lower(),
    )


def row_nodes(obj: dict, kind: str, brief: bool,
              skip: tuple[str, ...] = ()) -> list[Row]:
    """把一个字典展开成字段行（跳过嵌套设备列表）"""
    allow = BRIEF[kind] if brief else None
    rows: list[Row] = []
    for key, value in obj.items():
        if key.startswith("_") or key in skip:
            continue
        if allow is not None and key not in allow:
            continue
        if isinstance(value, list) and value and isinstance(value[0], dict):
            continue
        rows.append(make_row(key, value))
    return rows


def _as_dict(data, key: str) -> dict:
    value = data.get(key) if isinstance(data, dict) else None
    return value if isinstance(value, dict) else {}


def _as_list(record: dict, key: str) -> list[dict]:
    value = record.get(key) if isinstance(record, dict) else None
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def _text(record: dict, key: str, default: str = "") -> str:
    value = record.get(key) if isinstance(record, dict) else None
    if value is None or value == "":
        return default
    return str(value)


def build_model(data: dict | None, mode: str = "brief") -> list[Unit]:
    """把采集结果展开成「类别 → 设备 → 字段行」，返回扁平设备列表"""
    data = data if isinstance(data, dict) else {}
    brief = mode == "brief"
    groups: list[tuple[Cat, list[Unit]]] = []

    def new_group(key: str, meta: str = "") -> list[Unit]:
        units: list[Unit] = []
        groups.append((Cat(key, CATEGORY_LABELS.get(key, key), meta), units))
        return units

    def add_dev(units: list[Unit], dev: Device | None, rows: list[Row]) -> None:
        units.append(Unit(0, 0, groups[-1][0], dev, rows))

    # 操作系统
    record = _as_dict(data, "os")
    if record:
        units = new_group("os", "系统与账户")
        add_dev(units, None, row_nodes(record, "os", brief))

    # 处理器
    record = _as_dict(data, "cpu")
    if record:
        cores = record.get("核心数")
        threads = record.get("线程数")
        meta = (f"{cores} 核 / {threads} 线程"
                if cores is not None and threads is not None else "")
        units = new_group("cpu", meta)
        add_dev(units, None, row_nodes(record, "cpu", brief))

    # 主板
    record = _as_dict(data, "motherboard")
    if record:
        units = new_group("motherboard", "固件与安全")
        add_dev(units, None, row_nodes(record, "motherboard", brief))

    # 内存 + 内存条
    record = _as_dict(data, "memory")
    if record:
        total = record.get("总容量_GB")
        channel = record.get("通道模式")
        parts = []
        if total is not None:
            parts.append(f"{number(total)} GB")
        if channel:
            parts.append(str(channel))
        units = new_group("memory", " · ".join(parts))
        add_dev(units, None, row_nodes(record, "memory", brief, skip=("内存条",)))
        for index, stick in enumerate(_as_list(record, "内存条"), start=1):
            dev = Device(f"内存条 {index}", _text(stick, "插槽"))
            add_dev(units, dev, row_nodes(stick, "memoryStick", brief, skip=("插槽",)))

    # 显卡
    record = _as_dict(data, "gpu")
    if record:
        gpus = _as_list(record, "显卡列表")
        units = new_group("gpu", f"{len(gpus)} 个适配器")
        for gpu in gpus:
            kind = "gpuIntegrated" if _text(gpu, "类型") == "核显" else "gpu"
            dev = Device(_text(gpu, "名称", "显卡"), _text(gpu, "类型"))
            add_dev(units, dev, row_nodes(gpu, kind, brief, skip=("名称", "类型")))

    # 存储：磁盘 → 分区
    record = _as_dict(data, "storage")
    if record:
        disks = _as_list(record, "磁盘列表")
        part_count = sum(len(_as_list(disk, "分区")) for disk in disks)
        units = new_group("storage", f"{len(disks)} 块盘 · {part_count} 个分区")
        for index, disk in enumerate(disks, start=1):
            meta = " · ".join(x for x in (_text(disk, "类型"), _text(disk, "接口")) if x)
            dev = Device(_text(disk, "型号", f"磁盘 {index}"), meta)
            add_dev(units, dev, row_nodes(
                disk, "disk", brief, skip=("型号", "类型", "接口", "分区")))
            for part in _as_list(disk, "分区"):
                name = _text(part, "盘符") or "分区"
                label = _text(part, "标签")
                if label:
                    name = f"{name} {label}"
                sub = Device(name, _text(part, "文件系统"), part=True)
                add_dev(units, sub, row_nodes(
                    part, "partition", brief, skip=("盘符", "标签", "文件系统")))

    # 网络：已连接优先；精简档只列已连接的
    record = _as_dict(data, "network")
    if record:
        all_nics = _as_list(record, "网卡列表")
        connected = sum(1 for nic in all_nics if status_kind(nic.get("状态")) == "ok")
        nics = sorted(all_nics, key=lambda nic: 0 if status_kind(nic.get("状态")) == "ok" else 1)
        meta = (f"{connected} / {len(all_nics)} 已连接" if brief
                else f"{len(all_nics)} 个 · {connected} 已连接")
        units = new_group("network", meta)
        for nic in nics:
            if brief and status_kind(nic.get("状态")) != "ok":
                continue
            dev = Device(_text(nic, "名称", "网卡"), _text(nic, "类型"))
            add_dev(units, dev, row_nodes(nic, "network", brief, skip=("名称", "类型")))

    # 音频
    record = _as_dict(data, "audio")
    if record:
        devices = _as_list(record, "音频设备列表")
        units = new_group("audio", f"{len(devices)} 个设备")
        for device in devices:
            dev = Device(_text(device, "名称", "音频设备"), _text(device, "位置"))
            add_dev(units, dev, row_nodes(device, "audio", brief, skip=("名称", "位置")))

    # 显示器：活动优先
    record = _as_dict(data, "monitor")
    if record:
        all_monitors = _as_list(record, "显示器列表")
        active = sum(1 for mon in all_monitors if status_kind(mon.get("状态")) == "ok")
        monitors = sorted(
            all_monitors, key=lambda mon: 0 if status_kind(mon.get("状态")) == "ok" else 1)
        units = new_group("monitor", f"{len(all_monitors)} 台 · {active} 活动")
        for monitor in monitors:
            status = _text(monitor, "状态")
            dev = Device(_text(monitor, "型号", "显示器"), status,
                         tone=status_kind(status))
            add_dev(units, dev, row_nodes(monitor, "monitor", brief, skip=("型号", "状态")))

    # 扁平化并写回 ci / di
    units_out: list[Unit] = []
    for ci, (cat, units) in enumerate(groups):
        for unit in units:
            unit.ci = ci
            unit.di = len(units_out)
            units_out.append(unit)
    return units_out


def count_fields(units: list[Unit]) -> int:
    """字段数 = 行数 + 设备标题数"""
    return sum(len(unit.rows) + (1 if unit.dev else 0) for unit in units)


def build_items(units: list[Unit]) -> list[Item]:
    items: list[Item] = []
    for unit in units:
        for row in unit.rows:
            items.append(Item(unit.ci, unit.di, unit.cat, unit.dev, row))
    return items


def filter_units(units: list[Unit], query: str) -> list[Unit]:
    """按关键词过滤；分类或设备命中时保留其全部字段"""
    q = query.strip().lower()
    if not q:
        return units
    compact = re.sub(r"[\s,]", "", q)

    def match(text: str) -> bool:
        low = text.lower()
        if q in low:
            return True
        return bool(compact) and compact in re.sub(r"[\s,]", "", low)

    by_cat: dict[int, list[Unit]] = {}
    for unit in units:
        by_cat.setdefault(unit.ci, []).append(unit)

    out: list[Unit] = []
    for _ci, cat_units in by_cat.items():
        first = cat_units[0]
        cat_hit = match(f"{first.cat.name} {first.cat.meta}")
        kept: list[Unit] = []
        for unit in cat_units:
            dev_hit = cat_hit or (
                unit.dev is not None
                and match(f"{unit.dev.name} {unit.dev.meta}")
            )
            rows = unit.rows if dev_hit else [r for r in unit.rows if match(r.search)]
            if rows:
                kept.append(Unit(unit.ci, unit.di, unit.cat, unit.dev, rows))
        if kept:
            cat = Cat(first.cat.key, first.cat.name, f"{len(kept)} 个匹配")
            for unit in kept:
                unit.cat = cat
            out.extend(kept)
    return out


# ============================================================
# 度量 / 分栏
# ============================================================

PAD_X = 26
PAD_TOP = 10
PAD_BOTTOM = 14
GAP_EM = 2.2
LABEL_EM = 5.2
TARGET_WIDTH_LABELS = 260
TARGET_WIDTH_PLAIN = 205
MIN_FONT = 8
MAX_FONT = 40
SEARCH_FONT = 13
SEARCH_MAX_WIDTH = 1180


@lru_cache(maxsize=256)
def _font(px: int, weight: int, mono: bool) -> QFont:
    font = QFont("Cascadia Mono" if mono else "Microsoft YaHei UI")
    font.setPixelSize(max(6, int(px)))
    font.setWeight(QFont.Weight(int(weight)))
    font.setStyleStrategy(QFont.StyleStrategy.PreferAntialias)
    return font


class Metrics:
    """某一字号下各类文本的字体与行高"""

    def __init__(self, px: int):
        px = max(MIN_FONT, int(px))
        self.px = px
        self.cat_px = max(px + 1, round(px * 1.16))
        self.cat_cont_px = max(px, round(px * 1.04))
        self.dev_px = max(px - 1, round(px * 0.98))
        self.dev_cont_px = max(7, round(px * 0.84))
        self.label_px = max(7, round(px * 0.92))
        self.mono_px = max(7, round(px * 0.94))
        self.meta_small_px = max(7, round(px * 0.78))
        self.meta_dev_px = max(7, round(px * 0.82))

        self.cat_font = _font(self.cat_px, 700, False)
        self.cat_cont_font = _font(self.cat_cont_px, 700, False)
        self.dev_font = _font(self.dev_px, 600, False)
        self.dev_cont_font = _font(self.dev_cont_px, 400, False)
        self.label_font = _font(self.label_px, 400, False)
        self.value_font = _font(px, 400, False)
        self.mono_font = _font(self.mono_px, 400, True)
        self.meta_small_font = _font(self.meta_small_px, 400, False)
        self.meta_dev_font = _font(self.meta_dev_px, 400, False)

        self.cat_h = (0.82 + 1.34 + 0.06) * self.cat_px
        self.cat_cont_h = (0.42 + 1.34 + 0.06) * self.cat_cont_px
        self.dev_h = (0.50 + 1.36 + 0.04) * self.dev_px
        self.dev_cont_h = (0.20 + 1.36 + 0.04) * self.dev_cont_px
        self.row_pad = 0.07 * px
        self.row_line = 1.58 * px
        self.mono_line = 1.58 * self.mono_px

    def row_height(self, row: Row, value_width: float) -> float:
        font = self.mono_font if row.mono else self.value_font
        lines = wrapped_lines(row.text, font, value_width)
        return self.row_pad + lines * (self.mono_line if row.mono else self.row_line)

    def dev_height(self, dev: Device, col_width: float) -> float:
        """设备标题允许换行：名称过长时占两行（与原型 overflow-wrap 一致）"""
        name = f"↳ {dev.name}" if dev.part else dev.name
        indent = 0.85 * self.dev_px if dev.part else 0.0
        meta_width = 0.0
        if dev.meta:
            meta_width = QFontMetricsF(self.meta_dev_font).horizontalAdvance(dev.meta)
        gap = 0.45 * self.dev_px
        name_width = max(20.0, col_width - indent - gap
                         - min(meta_width, col_width * 0.55))
        lines = wrapped_lines(name, self.dev_font, name_width)
        return (0.54 + 1.36 * lines) * self.dev_px


def wrapped_lines(text: str, font: QFont, width: float) -> int:
    """用 Qt 自己的换行规则量行数（与 drawText(TextWordWrap) 一致）"""
    if width <= 1 or not text:
        return 1
    metrics = QFontMetricsF(font)
    rect = metrics.boundingRect(
        QRectF(0, 0, width, 1e6),
        int(Qt.TextFlag.TextWordWrap) | int(Qt.AlignmentFlag.AlignLeft),
        text,
    )
    spacing = metrics.lineSpacing() or metrics.height() or 1.0
    return max(1, int(round(rect.height() / spacing)))


@dataclass(slots=True)
class Op:
    kind: str            # cat / dev / row
    ci: int
    payload: object
    cont: bool
    y: float
    h: float


@dataclass(slots=True)
class Column:
    x: float
    w: float
    ops: list[Op]
    height: float


@dataclass(slots=True)
class Layout:
    px: int
    cols: int
    columns: list[Column]
    total: float
    avail: float
    fits: bool
    col_width: float
    metrics: Metrics
    label_width: float
    value_width: float
    gap: float


def _partition(cost: list[list[float]], n: int, count: int) -> list[list[int]]:
    """把连续字段切成 count 段，先压低最高一栏，再压低平方和"""
    count = max(1, min(count, n))
    inf = float("inf")
    dp_max = [[inf] * (n + 1) for _ in range(count + 1)]
    dp_sq = [[inf] * (n + 1) for _ in range(count + 1)]
    cut = [[0] * (n + 1) for _ in range(count + 1)]
    dp_max[0][0] = 0.0
    dp_sq[0][0] = 0.0

    for c in range(1, count + 1):
        prev_max = dp_max[c - 1]
        prev_sq = dp_sq[c - 1]
        cur_max = dp_max[c]
        cur_sq = dp_sq[c]
        cur_cut = cut[c]
        for j in range(1, n + 1):
            best_max = inf
            best_sq = inf
            best_i = 0
            for i in range(c - 1, j):
                base_max = prev_max[i]
                if base_max == inf:
                    continue
                segment = cost[i][j]
                cand_max = base_max if base_max > segment else segment
                if cand_max > best_max:
                    continue
                cand_sq = prev_sq[i] + segment * segment
                if cand_max < best_max - 1e-6 or (
                        abs(cand_max - best_max) <= 1e-6 and cand_sq < best_sq):
                    best_max = cand_max
                    best_sq = cand_sq
                    best_i = i
            cur_max[j] = best_max
            cur_sq[j] = best_sq
            cur_cut[j] = best_i

    groups: list[list[int]] = []
    j = n
    for c in range(count, 0, -1):
        i = cut[c][j]
        groups.insert(0, list(range(i, j)))
        j = i
    return groups


class BoardWidget(QWidget):
    """自绘画板：负责模型、分栏、字号自适应与绘制"""

    counts_changed = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._data: dict = {}
        self._mode = "brief"
        self._labels = True
        self._query = ""
        self._pending: list[str] = []

        self._units: list[Unit] = []
        self._units_all: list[Unit] = []
        self._items: list[Item] = []
        self._all_fields = 0
        self._mode_fields = 0
        self._visible_fields = 0
        self._searching = False

        self._layout: Layout | None = None
        self._dirty = True
        self._last_text = ""

        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.setInterval(90)
        self._timer.timeout.connect(self._sync_layout)

        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMinimumSize(1, 1)
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent, True)

    # ------------------------------------------------------------ 数据

    def set_data(self, data: dict | None) -> None:
        self._data = dict(data or {})
        self._rebuild()

    def set_result(self, result) -> None:
        self.set_data(getattr(result, "data", {}) or {})

    def update_category(self, name: str, data) -> None:
        if data is None:
            self._data.pop(name, None)
        elif isinstance(data, dict):
            self._data[name] = data
        self._rebuild()

    def set_pending(self, categories: list[str] | None) -> None:
        self._pending = list(categories or [])
        self.update()

    def set_mode(self, mode: str) -> None:
        mode = "all" if mode == "all" else "brief"
        if mode == self._mode:
            return
        self._mode = mode
        self._rebuild()

    def mode(self) -> str:
        return self._mode

    def set_labels(self, labels: bool) -> None:
        labels = bool(labels)
        if labels == self._labels:
            return
        self._labels = labels
        self._dirty = True
        self._schedule()

    def labels(self) -> bool:
        return self._labels

    def set_query(self, query: str) -> None:
        query = query or ""
        if query == self._query:
            return
        self._query = query
        self._rebuild()

    def query(self) -> str:
        return self._query

    # ------------------------------------------------------------ 模型

    def _rebuild(self) -> None:
        self._units = build_model(self._data, self._mode)
        self._units_all = (self._units if self._mode == "all"
                           else build_model(self._data, "all"))
        self._mode_fields = count_fields(self._units)
        self._all_fields = count_fields(self._units_all)

        self._searching = bool(self._query.strip())
        shown = (filter_units(self._units, self._query)
                 if self._searching else self._units)
        self._items = build_items(shown)
        self._visible_fields = count_fields(shown)

        self._dirty = True
        self._schedule()
        self._emit_counts()

    def _emit_counts(self) -> None:
        if self._searching:
            text = f"命中 {self._visible_fields} / {self._mode_fields} 项"
        elif self._mode == "brief":
            text = f"{self._visible_fields} / {self._all_fields} 项 · 精简"
        else:
            text = f"{self._mode_fields} 项"
        if text != self._last_text:
            self._last_text = text
            self.counts_changed.emit(text)

    def counts(self) -> tuple[int, int, int]:
        """(当前可见字段, 当前档位字段, 全部字段)"""
        return self._visible_fields, self._mode_fields, self._all_fields

    # ------------------------------------------------------------ 布局

    def _schedule(self) -> None:
        self._timer.start()

    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)
        self._dirty = True
        self._schedule()

    def _sync_layout(self) -> None:
        layout = self._compute_layout()
        self._layout = layout
        self._dirty = False
        want = 0
        if layout is not None:
            needed = int(layout.total + PAD_TOP + PAD_BOTTOM + 1)
            if needed > self.height() or self._searching:
                want = needed
        if want != self.minimumHeight():
            self.setMinimumHeight(want)
        self.update()

    def _ensure_layout(self) -> Layout | None:
        if self._dirty or self._layout is None:
            self._layout = self._compute_layout()
            self._dirty = False
        return self._layout

    def _column_width(self, font_px: int, cols: int) -> tuple[float, float]:
        inner = max(1.0, self.width() - 2 * PAD_X)
        gap = GAP_EM * font_px
        col_w = max(80.0, (inner - gap * (cols - 1)) / cols)
        return col_w, gap

    def _value_width(self, col_w: float, font_px: int) -> float:
        if not self._labels:
            return max(20.0, col_w)
        return max(20.0, col_w - LABEL_EM * font_px - 0.7 * font_px)

    def _measure(self, px: int, cols: int) -> tuple[Metrics, list[float], dict[int, float], list[list[float]], float, float]:
        """返回 (度量, 每行高度, 每个设备标题高度, 代价矩阵, 栏宽, 间隔)"""
        metrics = Metrics(px)
        col_w, gap = self._column_width(px, cols)
        value_w = self._value_width(col_w, px)
        row_heights = [metrics.row_height(item.row, value_w) for item in self._items]
        dev_heights: dict[int, float] = {}
        for item in self._items:
            if item.dev is not None and item.di not in dev_heights:
                dev_heights[item.di] = metrics.dev_height(item.dev, col_w)

        n = len(self._items)
        items = self._items
        cost = [[0.0] * (n + 1) for _ in range(n)]
        cat_h = metrics.cat_h
        cat_cont_h = metrics.cat_cont_h
        dev_cont_h = metrics.dev_cont_h

        for i in range(n):
            total = 0.0
            cat = -1
            dev = -1
            row = cost[i]
            for j in range(i + 1, n + 1):
                item = items[j - 1]
                if item.ci != cat:
                    cont = (j - 1 == i and i > 0 and items[i - 1].ci == item.ci)
                    total += cat_cont_h if cont else cat_h
                    cat = item.ci
                    dev = -1
                if item.dev is not None:
                    if item.di != dev:
                        cont = (j - 1 == i and i > 0
                                and items[i - 1].ci == item.ci
                                and items[i - 1].di == item.di)
                        total += dev_cont_h * 2.6 if cont else dev_heights[item.di]
                        dev = item.di
                else:
                    dev = -1
                total += row_heights[j - 1]
                row[j] = total
        return metrics, row_heights, dev_heights, cost, col_w, gap

    def _fit(self, px: int, cols: int) -> tuple[float, list[list[int]], Metrics, list[float], dict[int, float]]:
        metrics, row_heights, dev_heights, cost, _col_w, _gap = self._measure(px, cols)
        groups = _partition(cost, len(self._items), cols)
        total = max((cost[group[0]][group[-1] + 1] for group in groups if group), default=0.0)
        return total, groups, metrics, row_heights, dev_heights

    def _compute_layout(self) -> Layout | None:
        if not self._items:
            return None

        avail = max(1.0, self.height() - PAD_TOP - PAD_BOTTOM)
        inner = max(1.0, self.width() - 2 * PAD_X)

        if self._searching:
            px = SEARCH_FONT
            metrics = Metrics(px)
            col_w = min(inner, SEARCH_MAX_WIDTH)
            x = PAD_X + max(0.0, (inner - col_w) / 2)
            value_w = self._value_width(col_w, px)
            row_heights = [metrics.row_height(item.row, value_w) for item in self._items]
            dev_heights: dict[int, float] = {}
            for item in self._items:
                if item.dev is not None and item.di not in dev_heights:
                    dev_heights[item.di] = metrics.dev_height(item.dev, col_w)
            column = self._make_column(
                list(range(len(self._items))), row_heights, dev_heights,
                metrics, x, col_w)
            return Layout(px, 1, [column], column.height, avail,
                          column.height <= avail + 0.5, col_w, metrics,
                          LABEL_EM * px if self._labels else 0.0,
                          value_w, GAP_EM * px)

        target = TARGET_WIDTH_LABELS if self._labels else TARGET_WIDTH_PLAIN
        cols = max(1, min(6, round(inner / target)))

        total, groups, metrics, row_heights, dev_heights = self._fit(MIN_FONT, cols)
        while total > avail and cols < 6:
            cols += 1
            total, groups, metrics, row_heights, dev_heights = self._fit(MIN_FONT, cols)

        if total <= avail:
            low, high = MIN_FONT, MAX_FONT
            best = (total, groups, metrics, row_heights, dev_heights)
            while low <= high:
                mid = (low + high) // 2
                candidate = self._fit(mid, cols)
                if candidate[0] <= avail:
                    best = candidate
                    low = mid + 1
                else:
                    high = mid - 1
            total, groups, metrics, row_heights, dev_heights = best

        col_w, gap = self._column_width(metrics.px, cols)
        columns: list[Column] = []
        for index, group in enumerate(groups):
            x = PAD_X + index * (col_w + gap)
            columns.append(self._make_column(
                group, row_heights, dev_heights, metrics, x, col_w))
        total = max((column.height for column in columns), default=0.0)
        value_w = self._value_width(col_w, metrics.px)
        return Layout(
            metrics.px, cols, columns, total, avail, total <= avail + 0.5,
            col_w, metrics, LABEL_EM * metrics.px if self._labels else 0.0,
            value_w, gap,
        )

    def _make_column(self, indices: list[int], row_heights: list[float],
                     dev_heights: dict[int, float], metrics: Metrics,
                     x: float, col_w: float) -> Column:
        items = self._items
        ops: list[Op] = []
        y = 0.0
        cat = -1
        dev = -1
        for pos, index in enumerate(indices):
            item = items[index]
            if item.ci != cat:
                cont = pos == 0 and index > 0 and items[index - 1].ci == item.ci
                height = metrics.cat_cont_h if cont else metrics.cat_h
                ops.append(Op("cat", item.ci, item.cat, cont, y, height))
                y += height
                cat = item.ci
                dev = -1
            if item.dev is not None:
                if item.di != dev:
                    cont = (pos == 0 and index > 0
                            and items[index - 1].ci == item.ci
                            and items[index - 1].di == item.di)
                    height = metrics.dev_cont_h if cont else dev_heights[item.di]
                    ops.append(Op("dev", item.ci, item.dev, cont, y, height))
                    y += height
                    dev = item.di
            else:
                dev = -1
            height = row_heights[index]
            ops.append(Op("row", item.ci, item.row, False, y, height))
            y += height
        return Column(x, col_w, ops, y)

    # ------------------------------------------------------------ 绘制

    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(theme.P["bg"]))
        layout = self._ensure_layout()
        if layout is None:
            painter.setPen(QColor(theme.P["faint"]))
            painter.setFont(_font(13, 400, False))
            text = "正在采集…" if self._pending else "暂无数据"
            painter.drawText(self.rect(), _ALIGN_CENTER, text)
            return

        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        metrics = layout.metrics
        for column in layout.columns:
            for op in column.ops:
                top = PAD_TOP + op.y
                if op.kind == "cat":
                    self._paint_cat(painter, op, column, metrics, top)
                elif op.kind == "dev":
                    self._paint_dev(painter, op, column, metrics, top)
                else:
                    self._paint_row(painter, op, column, metrics, top, layout)

    def _paint_cat(self, painter: QPainter, op: Op, column: Column,
                   metrics: Metrics, top: float) -> None:
        cat: Cat = op.payload
        if op.cont:
            font = metrics.cat_cont_font
            pad = 0.42 * metrics.cat_cont_px
            painter.setFont(font)
            painter.setPen(QColor(theme.P["accent"]))
            painter.drawText(
                QRectF(column.x, top + pad, column.w, op.h - pad),
                _ALIGN_LT,
                cat.name,
            )
            painter.setFont(metrics.meta_small_font)
            painter.setPen(QColor(theme.P["faint"]))
            painter.drawText(
                QRectF(column.x, top + pad, column.w, op.h - pad),
                _ALIGN_RT,
                "续",
            )
            return

        pad = 0.82 * metrics.cat_px
        name_rect = QRectF(column.x, top + pad, column.w, op.h - pad)
        painter.setFont(metrics.cat_font)
        painter.setPen(QColor(theme.P["accent"]))
        fm = QFontMetricsF(metrics.cat_font)
        painter.drawText(
            name_rect,
            _ALIGN_LT,
            cat.name,
        )
        if cat.meta:
            meta_width = max(0.0, column.w - fm.horizontalAdvance(cat.name) - 8)
            if meta_width > 12:
                painter.setFont(metrics.meta_small_font)
                painter.setPen(QColor(theme.P["faint"]))
                meta_fm = QFontMetricsF(metrics.meta_small_font)
                text = meta_fm.elidedText(
                    cat.meta, Qt.TextElideMode.ElideRight, meta_width)
                painter.drawText(
                    name_rect,
                    _ALIGN_RT,
                    text,
                )

    def _paint_dev(self, painter: QPainter, op: Op, column: Column,
                   metrics: Metrics, top: float) -> None:
        dev: Device = op.payload
        if op.cont:
            font = metrics.dev_cont_font
            pad = 0.20 * metrics.dev_cont_px
            painter.setFont(font)
            painter.setPen(QColor(theme.P["muted"]))
            fm = QFontMetricsF(font)
            text = fm.elidedText(dev.name, Qt.TextElideMode.ElideRight,
                                 max(20.0, column.w - 24))
            painter.drawText(
                QRectF(column.x, top + pad, column.w - 24, op.h - pad),
                _ALIGN_LT,
                text,
            )
            painter.setFont(metrics.meta_small_font)
            painter.setPen(QColor(theme.P["faint"]))
            painter.drawText(
                QRectF(column.x, top + pad, column.w, op.h - pad),
                _ALIGN_RT,
                "续",
            )
            return

        pad = 0.50 * metrics.dev_px
        indent = 0.85 * metrics.dev_px if dev.part else 0.0
        name = f"↳ {dev.name}" if dev.part else dev.name
        painter.setFont(metrics.dev_font)
        painter.setPen(QColor(theme.P["ink"]))
        reserve = 0.0
        meta_text = ""
        if dev.meta:
            meta_fm = QFontMetricsF(metrics.meta_dev_font)
            natural = meta_fm.horizontalAdvance(dev.meta)
            reserve = min(natural, column.w * 0.55) + 0.45 * metrics.dev_px
            meta_text = meta_fm.elidedText(
                dev.meta, Qt.TextElideMode.ElideRight, max(0.0, column.w * 0.55))
        name_width = max(20.0, column.w - indent - reserve)
        painter.drawText(
            QRectF(column.x + indent, top + pad, name_width, op.h - pad),
            _WRAP_LT,
            name,
        )
        if meta_text:
            painter.setFont(metrics.meta_dev_font)
            painter.setPen(QColor(_tone_color(dev.tone, theme.P["faint"])))
            painter.drawText(
                QRectF(column.x, top + pad, column.w, op.h - pad),
                _ALIGN_RT,
                meta_text,
            )

    def _paint_row(self, painter: QPainter, op: Op, column: Column,
                   metrics: Metrics, top: float, layout: Layout) -> None:
        row: Row = op.payload
        pad = metrics.row_pad / 2
        if layout.label_width > 0:
            painter.setFont(metrics.label_font)
            painter.setPen(QColor(theme.P["muted"]))
            label_fm = QFontMetricsF(metrics.label_font)
            text = label_fm.elidedText(
                row.label, Qt.TextElideMode.ElideRight, layout.label_width)
            painter.drawText(
                QRectF(column.x, top + pad, layout.label_width, op.h - pad),
                _ALIGN_LT,
                text,
            )
            value_x = column.x + layout.label_width + 0.7 * metrics.px
        else:
            value_x = column.x

        painter.setFont(metrics.mono_font if row.mono else metrics.value_font)
        painter.setPen(QColor(_tone_color(row.tone, theme.P["text2"])))
        painter.drawText(
            QRectF(value_x, top + pad, layout.value_width, op.h - pad),
            _WRAP_LT,
            row.text,
        )

    # ------------------------------------------------------------ 供测试 / 截图使用

    def layout_metrics(self) -> dict:
        layout = self._ensure_layout()
        visible, mode_fields, all_fields = self.counts()
        if layout is None:
            return {
                "font": 0, "cols": 0, "total": 0.0, "avail": max(
                    0.0, self.height() - PAD_TOP - PAD_BOTTOM),
                "fits": False, "visible": visible, "mode": mode_fields,
                "all": all_fields, "searching": self._searching,
                "rows": len(self._items),
            }
        return {
            "font": layout.px,
            "cols": layout.cols,
            "total": round(layout.total, 1),
            "avail": round(layout.avail, 1),
            "fits": layout.fits,
            "visible": visible,
            "mode": mode_fields,
            "all": all_fields,
            "searching": self._searching,
            "rows": len(self._items),
            "col_heights": [round(column.height, 1) for column in layout.columns],
        }

    def sizeHint(self) -> QSize:  # noqa: N802
        return QSize(1280, 760)


def _tone_color(tone: str, default: str) -> str:
    return {
        "ok": theme.P["ok"],
        "off": theme.P["off"],
        "no": theme.P["faint"],
        "null": theme.P["faint"],
        "neutral": theme.P["muted"],
    }.get(tone, default)


def host_name() -> str:
    """主机名（取不到时给个占位）"""
    try:
        return socket.gethostname() or "本机"
    except OSError:
        return "本机"
