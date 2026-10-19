"""
gui/pages/overview.py - 总览页（便当格）

一张本机主卡 + 9 张类别卡 + 一张采集状态卡，一屏看完本机配置。
数据从 CollectResult 读取，支持逐类渐进填充。
"""
from datetime import datetime

from PySide6.QtWidgets import QHBoxLayout, QVBoxLayout

from core.constants import CATEGORY_LABELS
from gui import theme
from gui import values as V
from gui.components import (
    BentoPage, CoreGrid, ElidedLabel, MeterBar, Skeleton, SlotRow,
    card, clear_layout, hline, label, mini_stat, pill, vline,
)

# 类别卡片顺序（4 列 × 3 行：主卡占 2 格）
ORDER = ["cpu", "memory", "gpu", "storage", "network", "monitor",
         "os", "motherboard", "audio"]


def stat_row(pairs: list[tuple[str, str]]) -> QHBoxLayout:
    """一行迷你指标，用竖线分隔"""
    row = QHBoxLayout()
    row.setSpacing(theme.sp(16))
    for i, (key, value) in enumerate(pairs):
        row.addLayout(mini_stat(value, key), 1)
        if i < len(pairs) - 1:
            row.addWidget(vline())
    return row


def load_row(title: str, value_pct, accent: str) -> QVBoxLayout:
    """标签 + 百分比 + 进度条"""
    box = QVBoxLayout()
    box.setSpacing(theme.sp(6))
    line = QHBoxLayout()
    line.setSpacing(theme.sp(8))
    line.addWidget(label(title, "miniLabel"))
    line.addStretch()
    line.addWidget(label(f"{V.percent(value_pct, 1)} %", "rowSub"))
    box.addLayout(line)
    box.addWidget(MeterBar(V.fraction(value_pct, 100), fill=accent))
    return box


class OverviewPage(BentoPage):
    """总览页"""

    def __init__(self, parent=None):
        super().__init__("总览", "", columns=4, row_min=theme.sp(180), parent=parent)
        self._bodies: dict[str, QVBoxLayout] = {}
        self._frames: dict[str, object] = {}
        self._build()
        self.finish()
        self.set_meta("等待采集…")

    # ------------------------------------------------------------ 构建

    def _build(self) -> None:
        identity = self._identity_card()
        self._frames["identity"] = identity
        self.add(identity, span=2)

        for cat in ORDER:
            frame, body = card(CATEGORY_LABELS[cat], theme.accent(cat),
                               theme.CATEGORY_ICONS[cat])
            self._frames[cat] = frame
            self._bodies[cat] = body
            self._placeholder(body)
            self.add(frame, span=1)

        collector = self._collector_card()
        self._frames["collector"] = collector
        self.add(collector, span=1)

    def _identity_card(self):
        frame, body = card("本机", theme.accent("overview"), "overview", hero=True)
        self._id_kicker = label("HARDWARE OVERVIEW", "kicker")
        self._id_model = ElidedLabel("—", "idModel")
        self._id_sub = ElidedLabel("", "idSub")
        self._id_stats = QHBoxLayout()
        body.addWidget(self._id_kicker)
        body.addSpacing(theme.sp(6))
        body.addWidget(self._id_model)
        body.addSpacing(theme.sp(4))
        body.addWidget(self._id_sub)
        body.addSpacing(theme.sp(14))
        body.addLayout(self._id_stats)
        return frame

    def _collector_card(self):
        frame, body = card("采集", theme.accent("cpu"), "activity", "等待")
        self._collector_body = body
        return frame

    def _placeholder(self, body: QVBoxLayout) -> None:
        clear_layout(body)
        body.addWidget(Skeleton([(1.0, 12), (0.72, 10), (0.46, 10)]))
        body.addWidget(label("等待采集…", "hintText"))

    # ------------------------------------------------------------ 渐进填充

    def set_pending(self, categories: list[str]) -> None:
        """采集开始：先把本次要采集的类别置为「采集中」"""
        for cat in ORDER:
            frame = self._frames.get(cat)
            if cat in categories:
                if frame is not None and frame.tag_label is not None:
                    frame.tag_label.setText("采集中")
            else:
                if frame is not None and frame.tag_label is not None:
                    frame.tag_label.setText("未采集")

    def update_category(self, name: str, data) -> None:
        """单个类别采集完成（data 为 None 表示失败）"""
        if name in self._bodies:
            self._render(name, data)

    def update_result(self, result) -> None:
        """采集结束：写入选中的全部数据"""
        for cat in ORDER:
            self._render(cat, result.data.get(cat))
        self._fill_identity(result)
        self._fill_collector(result)
        stamp = datetime.now().strftime("%H:%M")
        self.set_meta(f"采集于 {stamp} · 耗时 {result.elapsed_seconds:.2f}s · "
                      f"数据 {len(result.data)}/{len(ORDER)} 类")

    def _render(self, cat: str, data) -> None:
        body = self._bodies.get(cat)
        if body is None:
            return
        clear_layout(body)
        if data is None:
            self._failed(body, cat)
            tag = self._frames[cat].tag_label
            if tag is not None:
                tag.setText("失败")
            return
        filler = getattr(self, f"_fill_{cat}", None)
        if filler:
            filler(body, data)

    def _failed(self, body: QVBoxLayout, cat: str) -> None:
        body.addWidget(Skeleton([(0.5, 10)]))
        body.addWidget(label("未采集到数据", "stateBody"))
        body.addWidget(label("可能是硬件不支持或需要管理员权限", "hintText"))

    # ------------------------------------------------------------ 各卡片内容

    def _fill_identity(self, result) -> None:
        board = result.data.get("motherboard") or {}
        os_data = result.data.get("os") or {}
        cpu = result.data.get("cpu") or {}
        mem = result.data.get("memory") or {}
        disks = V.items(result.data.get("storage") or {}, "storage")

        model = V.get(board, "型号", "") or V.get(os_data, "系统名称", "本机")
        vendor = V.get(board, "厂商", "")
        self._id_model.setText(str(model))
        os_name = str(V.get(os_data, "系统名称", "")).replace("Microsoft ", "")
        self._id_sub.setText("  ·  ".join(x for x in [
            vendor,
            os_name,
            V.get(board, "芯片组", "") if board else "",
        ] if x and x != V.MISSING))

        total_gb = sum(float(d.get("容量_GB") or 0) for d in disks)
        clear_layout(self._id_stats)
        self._id_stats.addLayout(stat_row([
            ("处理器", f"{V.get(cpu, '核心数')} 核 / {V.get(cpu, '线程数')} 线程"),
            ("内存", V.gb(V.get(mem, "总容量_GB", None))),
            ("存储", V.gb(total_gb) if total_gb else V.MISSING),
        ]), 1)
        # 标题行右侧加一个类别数标签
        kind = self._frames["identity"].tag_label
        if kind is not None:
            kind.setText(f"{len(result.data)} 类")

    def _fill_collector(self, result) -> None:
        body = self._collector_body
        clear_layout(body)
        ok = len(result.data)
        total = ok + len(result.errors)
        body.addLayout(stat_row([
            ("类别", f"{ok}/{total or 9}"),
            ("耗时", f"{result.elapsed_seconds:.2f}s"),
            ("错误", str(len(result.errors))),
        ]))
        body.addSpacing(theme.sp(12))
        if result.errors:
            tag = self._frames["collector"].tag_label
            if tag is not None:
                tag.setText(f"{len(result.errors)} 失败")
            for err in result.errors[:2]:
                line = QHBoxLayout()
                line.setSpacing(theme.sp(8))
                line.addWidget(pill("失败", theme.P["err"]))
                line.addWidget(ElidedLabel(str(err.get("错误", "")), "rowSub"), 1)
                body.addLayout(line)
                body.addSpacing(theme.sp(6))
        elif result.warnings:
            tag = self._frames["collector"].tag_label
            if tag is not None:
                tag.setText("有提示")
            for warn in result.warnings[:2]:
                body.addWidget(ElidedLabel(str(warn), "rowSub"))
        else:
            tag = self._frames["collector"].tag_label
            if tag is not None:
                tag.setText("完成")
            body.addWidget(label("全部类别采集完成，无错误", "rowSub"))

    def _fill_cpu(self, body, data) -> None:
        body.addWidget(ElidedLabel(str(V.get(data, "名称")), "rowName"))
        body.addWidget(ElidedLabel("  ·  ".join(x for x in [
            str(V.get(data, "厂商")), str(V.get(data, "架构")), str(V.get(data, "插槽"))
        ] if x != V.MISSING), "rowSub"))
        body.addSpacing(theme.sp(10))
        body.addLayout(stat_row([
            ("核心", str(V.get(data, "核心数"))),
            ("线程", str(V.get(data, "线程数"))),
            ("基础频率", V.mhz(V.get(data, "基础频率_MHz", None))),
        ]))
        threads = int(data.get("线程数") or 0)
        if threads:
            body.addSpacing(theme.sp(10))
            grid = CoreGrid(min(threads, 36), theme.accent("cpu"), cols=12,
                            cell=theme.sp(12), gap=theme.sp(5))
            body.addWidget(grid)

    def _fill_memory(self, body, data) -> None:
        body.addLayout(stat_row([
            ("总容量", V.gb(V.get(data, "总容量_GB", None))),
            ("已使用", V.gb(V.get(data, "已使用_GB", None))),
            ("通道", str(V.get(data, "通道模式"))),
        ]))
        body.addSpacing(theme.sp(12))
        total = int(data.get("插槽总数") or 0)
        used = int(data.get("已用插槽") or 0)
        if total:
            slot_line = QHBoxLayout()
            slot_line.setSpacing(theme.sp(10))
            slot_line.addWidget(SlotRow(total, used))
            slot_line.addWidget(label(f"插槽 {used} / {total} 已用", "hintText"))
            slot_line.addStretch()
            body.addLayout(slot_line)
        sticks = V.items(data, "memory")
        if sticks:
            first = sticks[0]
            body.addSpacing(theme.sp(10))
            detail = "  ·  ".join(x for x in [
                str(V.get(first, "频率_MHz")) + " MHz",
                f"CL{V.get(first, 'CL')}",
                str(V.get(first, "类型")),
                V.gb(V.get(first, "容量_GB", None), 0) + " × " + str(len(sticks)),
            ] if x and x != V.MISSING and not x.startswith("—"))
            body.addWidget(ElidedLabel(detail, "rowSub"))
        body.addSpacing(theme.sp(10))
        body.addLayout(load_row("使用率", V.get(data, "使用率_百分比", 0), theme.accent("memory")))

    def _fill_gpu(self, body, data) -> None:
        gpus = V.items(data, "gpu")
        primary = V.pick_primary_gpu(gpus)
        if not primary:
            body.addWidget(label("未检测到显卡", "stateBody"))
            return
        body.addWidget(ElidedLabel(str(V.get(primary, "名称")), "rowName"))
        body.addWidget(ElidedLabel("  ·  ".join(x for x in [
            str(V.get(primary, "厂商")), str(V.get(primary, "类型"))
        ] if x != V.MISSING), "rowSub"))
        body.addSpacing(theme.sp(10))
        body.addLayout(stat_row([
            ("显存", V.mb_to_gb(V.get(primary, "显存_MB", None))),
            ("分辨率", str(V.get(primary, "当前分辨率"))),
            ("刷新率", f"{V.get(primary, '刷新率_Hz')} Hz"),
        ]))
        body.addSpacing(theme.sp(10))
        body.addLayout(load_row("负载", V.get(primary, "负载_百分比", 0), theme.accent("gpu")))
    def _fill_storage(self, body, data) -> None:
        disks = V.items(data, "storage")
        if not disks:
            body.addWidget(label("未检测到磁盘", "stateBody"))
            return
        total_gb = sum(float(d.get("容量_GB") or 0) for d in disks)
        body.addLayout(stat_row([
            ("磁盘", f"{len(disks)} 个"),
            ("总容量", V.gb(total_gb)),
        ]))
        body.addSpacing(theme.sp(12))
        for i, disk in enumerate(disks[:2]):
            used, total = V.disk_usage(disk)
            line = QHBoxLayout()
            line.setSpacing(theme.sp(8))
            line.addWidget(ElidedLabel(str(V.get(disk, "型号")), "rowName"), 1)
            line.addWidget(label(f"{V.gb(used)} / {V.gb(total)}", "hintText"))
            body.addLayout(line)
            body.addSpacing(theme.sp(6))
            body.addWidget(MeterBar(V.fraction(used, total), fill=theme.accent("storage")))
            if i < min(len(disks), 2) - 1:
                body.addSpacing(theme.sp(12))

    def _fill_network(self, body, data) -> None:
        adapters = V.items(data, "network")
        connected = [a for a in adapters if str(a.get("状态", "")) == "已连接"]
        shown = (connected or adapters)[:2]
        if not shown:
            body.addWidget(label("未检测到网卡", "stateBody"))
            return
        body.addLayout(stat_row([
            ("网卡", f"{len(adapters)} 个"),
            ("已连接", f"{len(connected)} 个"),
        ]))
        body.addSpacing(theme.sp(12))
        for i, adapter in enumerate(shown):
            line = QHBoxLayout()
            line.setSpacing(theme.sp(8))
            is_wifi = "无线" in str(V.get(adapter, "类型", ""))
            line.addWidget(pill("无线" if is_wifi else "有线", theme.accent("network")))
            line.addWidget(ElidedLabel(str(V.get(adapter, "名称")), "rowName"), 1)
            body.addLayout(line)
            body.addWidget(ElidedLabel("  ·  ".join(x for x in [
                str(V.get(adapter, "IPv4")),
                f"{V.get(adapter, '速率_Gbps')} Gbps",
                str(V.get(adapter, "状态")),
            ] if x != V.MISSING), "rowSub"))
            if i < len(shown) - 1:
                body.addSpacing(theme.sp(10))

    def _fill_monitor(self, body, data) -> None:
        monitors = V.items(data, "monitor")
        if not monitors:
            body.addWidget(label("未检测到显示器", "stateBody"))
            return
        for i, mon in enumerate(monitors[:2]):
            line = QHBoxLayout()
            line.setSpacing(theme.sp(8))
            line.addWidget(ElidedLabel(str(V.get(mon, "型号")), "rowName"), 1)
            line.addWidget(pill(str(V.get(mon, "状态")), theme.accent("monitor")))
            body.addLayout(line)
            body.addWidget(ElidedLabel("  ·  ".join(x for x in [
                str(V.get(mon, "分辨率")),
                f"{V.get(mon, '刷新率_Hz')} Hz",
                str(V.get(mon, "厂商")),
            ] if x != V.MISSING), "rowSub"))
            if i < len(monitors[:2]) - 1:
                body.addSpacing(theme.sp(12))

    def _fill_os(self, body, data) -> None:
        body.addLayout(stat_row([
            ("架构", str(V.get(data, "系统架构"))),
            ("用户", str(V.get(data, "用户名"))),
        ]))
        body.addSpacing(theme.sp(12))
        for key in ("版本号", "安装日期", "上次启动"):
            line = QHBoxLayout()
            line.setSpacing(theme.sp(8))
            line.addWidget(label(V.field_label(key), "miniLabel"))
            line.addStretch()
            line.addWidget(ElidedLabel(str(V.get(data, key)), "rowSub"), 1)
            body.addLayout(line)
            body.addSpacing(theme.sp(6))

    def _fill_motherboard(self, body, data) -> None:
        body.addWidget(ElidedLabel(str(V.get(data, "型号")), "rowName"))
        body.addWidget(ElidedLabel(str(V.get(data, "芯片组")), "rowSub"))
        body.addSpacing(theme.sp(12))
        body.addLayout(stat_row([
            ("BIOS", str(V.get(data, "BIOS_版本"))),
            ("UEFI", V.human(V.get(data, "UEFI", None))),
        ]))
        body.addSpacing(theme.sp(10))
        body.addWidget(ElidedLabel(f"TPM {V.get(data, 'TPM')}", "rowSub"))
        body.addWidget(ElidedLabel(f"BIOS {V.get(data, 'BIOS_日期')}", "hintText"))

    def _fill_audio(self, body, data) -> None:
        devices = V.items(data, "audio")
        if not devices:
            body.addWidget(label("未检测到音频设备", "stateBody"))
            return
        first = devices[0]
        body.addWidget(ElidedLabel(str(V.get(first, "名称")), "rowName"))
        body.addWidget(ElidedLabel("  ·  ".join(x for x in [
            str(V.get(first, "厂商")), str(V.get(first, "位置"))
        ] if x != V.MISSING), "rowSub"))
        body.addSpacing(theme.sp(12))
        body.addLayout(stat_row([
            ("设备", f"{len(devices)} 个"),
            ("驱动", str(V.get(first, "驱动版本"))),
        ]))
