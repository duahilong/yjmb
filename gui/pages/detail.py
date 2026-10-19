"""
gui/pages/detail.py - 类别详情页

两套模板：
- 标量型（操作系统 / 主板 / 处理器 / 内存）：主卡 + 指标卡 + 规格明细
- 列表型（显卡 / 存储 / 网络 / 音频 / 显示器）：概览卡 + 每台设备一张卡

字段全部来自采集结果的真实键名，不补造数据。
"""
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QApplication, QGridLayout, QHBoxLayout, QVBoxLayout, QWidget

from core.constants import CATEGORY_LABELS
from gui import theme
from gui import values as V
from gui.components import (
    BentoPage, CoreGrid, ElidedLabel, MeterBar, SlotRow, action_button,
    card, definition_grid, hline, label, mini_stat, pill, set_tag, state_card, vline,
)


def stat_row(pairs: list[tuple[str, str]]) -> QHBoxLayout:
    row = QHBoxLayout()
    row.setSpacing(theme.sp(16))
    for i, (key, value) in enumerate(pairs):
        row.addLayout(mini_stat(value, key), 1)
        if i < len(pairs) - 1:
            row.addWidget(vline())
    return row


def load_row(title: str, value_pct, accent: str) -> QVBoxLayout:
    box = QVBoxLayout()
    box.setSpacing(theme.sp(6))
    line = QHBoxLayout()
    line.addWidget(label(title, "miniLabel"))
    line.addStretch()
    line.addWidget(label(f"{V.percent(value_pct, 1)} %", "rowSub"))
    box.addLayout(line)
    box.addWidget(MeterBar(V.fraction(value_pct, 100), fill=accent))
    return box


def chip_row(values: list, accent: str, columns: int = 4) -> QWidget:
    """一组小胶囊（指令集等）"""
    box = QWidget()
    grid = QGridLayout(box)
    grid.setContentsMargins(0, 0, 0, 0)
    grid.setHorizontalSpacing(theme.sp(6))
    grid.setVerticalSpacing(theme.sp(6))
    for i, value in enumerate(values):
        grid.addWidget(pill(str(value), accent), i // columns, i % columns)
    grid.setColumnStretch(columns, 1)
    return box


class DetailPage(BentoPage):
    """通用类别详情页"""

    refresh_requested = Signal(str)

    def __init__(self, category: str, parent=None):
        label_text = CATEGORY_LABELS.get(category, category)
        super().__init__(label_text, "", columns=4, row_min=theme.sp(170), parent=parent)
        self.category = category
        self._result = None
        self._build_actions()
        self.finish()
        self._show_state("empty", "正在等待采集结果…")

    def _build_actions(self) -> None:
        self.add_action(action_button("复制摘要", "export", kind="ghost",
                                     on_click=self._copy_summary))
        self.add_action(action_button("重新采集", "refresh", kind="primary",
                                     on_click=lambda: self.refresh_requested.emit(self.category)))

    # ------------------------------------------------------------ 数据入口

    def set_pending(self) -> None:
        self._show_state("loading", "正在读取该类别…")

    def update_result(self, result) -> None:
        self._result = result
        data = result.data.get(self.category)
        if data is None:
            error = next((e for e in result.errors
                          if e.get("模块") == self.category), None)
            if error:
                self._show_state("error", str(error.get("错误", "未知错误")))
            else:
                self._show_state("empty", "该类别已关闭，或采集器未返回数据。")
            self.set_meta("")
            return
        self._render(data)
        elapsed = result.timings.get(self.category)
        self.set_meta(f"采集耗时 {elapsed:.2f}s" if elapsed else "")

    def update_category(self, name: str, data) -> None:
        if name != self.category:
            return
        if data is None:
            self._show_state("error", "该类别采集失败，可尝试重新采集。")
        else:
            self._render(data)

    # ------------------------------------------------------------ 状态页

    def _show_state(self, kind: str, text: str) -> None:
        self.grid.reset()
        accent = theme.accent(self.category)
        if kind == "error":
            frame = state_card(
                "warning", theme.P["err"], "采集失败", text, status="错误",
                buttons=[action_button("重新采集", "refresh", kind="primary",
                                       on_click=lambda: self.refresh_requested.emit(self.category))],
            )
        elif kind == "loading":
            frame = state_card("refresh", accent, "正在采集", text, status="采集中")
        else:
            frame = state_card(
                "box", accent, "该类别未采集", text, status="未采集",
                buttons=[action_button("重新采集", "refresh", kind="ghost",
                                       on_click=lambda: self.refresh_requested.emit(self.category))],
            )
        self.grid.add_card(frame, span=4)
        self.grid.finish()

    # ------------------------------------------------------------ 渲染

    def _render(self, data) -> None:
        self.grid.reset()
        builder = getattr(self, f"_cards_{self.category}", None)
        cards = builder(data) if builder else [(self._spec_card(data), 4)]
        for widget, span in cards:
            self.grid.add_card(widget, span)
        self.grid.finish()

    def _spec_card(self, data: dict, title: str = "规格明细",
                   columns: int = 2) -> QWidget:
        accent = theme.accent(self.category)
        rows = V.flat_rows(data)
        frame, body = card(title, accent, "info", f"{len(rows)} 项")
        body.addWidget(definition_grid(rows, columns=columns))
        return frame

    # ------------------------------------------------------------ 标量型

    def _cards_cpu(self, data: dict) -> list[tuple[QWidget, int]]:
        accent = theme.accent("cpu")
        hero, body = card("处理器", accent, "cpu", tag=str(V.get(data, "架构")), hero=True)
        body.addWidget(ElidedLabel(str(V.get(data, "名称")), "idModel"))
        body.addWidget(ElidedLabel("  ·  ".join(x for x in [
            str(V.get(data, "厂商")), str(V.get(data, "插槽"))
        ] if x != V.MISSING), "idSub"))
        body.addSpacing(theme.sp(18))
        body.addLayout(stat_row([
            ("核心", str(V.get(data, "核心数"))),
            ("线程", str(V.get(data, "线程数"))),
            ("基础频率", V.mhz(V.get(data, "基础频率_MHz", None))),
            ("当前负载", f"{V.percent(V.get(data, '当前负载_百分比'), 1)} %"),
        ]))

        threads = int(data.get("线程数") or 0)
        core_card, core_body = card(
            "核心与频率", accent, "chip",
            tag=f"{V.get(data, '核心数')} 核 / {threads} 线程")
        core_body.addWidget(CoreGrid(threads, accent, cols=12,
                                     cell=theme.sp(18), gap=theme.sp(9)))
        core_body.addSpacing(theme.sp(12))
        core_body.addWidget(label("每格代表一个逻辑线程", "hintText"))
        core_body.addSpacing(theme.sp(10))
        core_body.addLayout(load_row("当前负载", V.get(data, "当前负载_百分比", 0), accent))

        virt = V.human(V.get(data, "虚拟化", None))
        feat_card, feat_body = card("缓存与特性", accent, "layers", tag=f"虚拟化 {virt}")
        feat_body.addLayout(stat_row([
            ("L2 缓存", f"{V.human(V.get(data, 'L2缓存_MB', None))} MB"),
            ("L3 缓存", f"{V.human(V.get(data, 'L3缓存_MB', None))} MB"),
            ("指令集", f"{len(data.get('指令集') or [])} 项"),
        ]))
        feat_body.addSpacing(theme.sp(12))
        instructions = data.get("指令集") or []
        if instructions:
            feat_body.addWidget(chip_row(instructions, accent, columns=4))
        else:
            feat_body.addWidget(label("采集器未返回指令集", "hintText"))

        return [
            (hero, 2), (core_card, 2),
            (feat_card, 2), (self._spec_card(data), 2),
        ]

    def _cards_motherboard(self, data: dict) -> list[tuple[QWidget, int]]:
        accent = theme.accent("motherboard")
        hero, body = card("主板", accent, "motherboard", tag=str(V.get(data, "厂商")), hero=True)
        body.addWidget(ElidedLabel(str(V.get(data, "型号")), "idModel"))
        body.addWidget(ElidedLabel(str(V.get(data, "芯片组")), "idSub"))
        body.addSpacing(theme.sp(18))
        body.addLayout(stat_row([
            ("BIOS 版本", str(V.get(data, "BIOS_版本"))),
            ("BIOS 日期", str(V.get(data, "BIOS_日期"))),
            ("UEFI", V.human(V.get(data, "UEFI", None))),
        ]))
        body.addSpacing(theme.sp(10))
        body.addWidget(ElidedLabel(f"TPM  {V.get(data, 'TPM')}", "rowSub"))
        body.addWidget(ElidedLabel(f"BIOS 厂商  {V.get(data, 'BIOS_厂商')}", "hintText"))
        return [(hero, 2), (self._spec_card(data, columns=1), 2)]

    def _cards_os(self, data: dict) -> list[tuple[QWidget, int]]:
        accent = theme.accent("os")
        name = str(V.get(data, "系统名称")).replace("Microsoft ", "")
        hero, body = card("操作系统", accent, "os", tag=str(V.get(data, "系统架构")), hero=True)
        body.addWidget(ElidedLabel(name, "idModel"))
        body.addWidget(ElidedLabel(f"版本 {V.get(data, '版本号')}", "idSub"))
        body.addSpacing(theme.sp(18))
        body.addLayout(stat_row([
            ("用户", str(V.get(data, "用户名"))),
            ("安装日期", str(V.get(data, "安装日期"))),
            ("上次启动", str(V.get(data, "上次启动"))),
        ]))
        return [(hero, 2), (self._spec_card(data, columns=1), 2)]

    def _cards_memory(self, data: dict) -> list[tuple[QWidget, int]]:
        accent = theme.accent("memory")
        total = int(data.get("插槽总数") or 0)
        used = int(data.get("已用插槽") or 0)

        metrics, body = card("内存概览", accent, "memory",
                             tag=str(V.get(data, "通道模式")))
        body.addLayout(stat_row([
            ("总容量", V.gb(V.get(data, "总容量_GB", None))),
            ("已使用", V.gb(V.get(data, "已使用_GB", None))),
            ("使用率", f"{V.percent(V.get(data, '使用率_百分比'), 1)} %"),
            ("插槽", f"{used} / {total}"),
        ]))
        body.addSpacing(theme.sp(14))
        if total:
            slot_line = QHBoxLayout()
            slot_line.setSpacing(theme.sp(12))
            slot_line.addWidget(SlotRow(total, used))
            slot_line.addWidget(label(
                f"已用 {used} 条，空闲 {max(0, total - used)} 条", "hintText"))
            slot_line.addStretch()
            body.addLayout(slot_line)
        body.addSpacing(theme.sp(12))
        body.addLayout(load_row("使用率", V.get(data, "使用率_百分比", 0), accent))

        cards: list[tuple[QWidget, int]] = [(metrics, 4)]
        sticks = V.items(data, "memory")
        for stick in sticks:
            title = str(V.get(stick, "插槽"))
            frame, sbody = card(title, accent, "memory", tag=str(V.get(stick, "类型")))
            sbody.addWidget(ElidedLabel(str(V.get(stick, "型号")), "rowName"))
            sbody.addWidget(ElidedLabel(str(V.get(stick, "厂商")), "rowSub"))
            sbody.addSpacing(theme.sp(10))
            rows = V.flat_rows(stick, skip=("插槽", "型号", "厂商", "类型"))
            sbody.addWidget(definition_grid(rows, columns=2))
            cards.append((frame, 2 if len(sticks) > 1 else 4))
        return cards

    # ------------------------------------------------------------ 列表型

    def _cards_gpu(self, data: dict) -> list[tuple[QWidget, int]]:
        accent = theme.accent("gpu")
        gpus = V.items(data, "gpu")
        if not gpus:
            return [(self._empty_card("未检测到显卡"), 4)]
        span = 2 if len(gpus) > 1 else 4
        cards = []
        for gpu in gpus:
            frame, body = card(str(V.get(gpu, "类型", "显卡")), accent, "gpu",
                               tag=str(V.get(gpu, "状态")))
            body.addWidget(ElidedLabel(str(V.get(gpu, "名称")), "rowName"))
            body.addWidget(ElidedLabel(str(V.get(gpu, "厂商")), "rowSub"))
            body.addSpacing(theme.sp(10))
            rows = V.flat_rows(gpu, skip=("名称", "厂商", "类型", "状态", "负载_百分比"))
            body.addWidget(definition_grid(rows, columns=2))
            load = gpu.get("负载_百分比")
            if load is not None:
                body.addSpacing(theme.sp(10))
                body.addLayout(load_row("负载", load, accent))
            cards.append((frame, span))
        return cards

    def _cards_storage(self, data: dict) -> list[tuple[QWidget, int]]:
        accent = theme.accent("storage")
        disks = V.items(data, "storage")
        if not disks:
            return [(self._empty_card("未检测到磁盘"), 4)]

        total_gb = sum(float(d.get("容量_GB") or 0) for d in disks)
        used_gb = sum(V.disk_usage(d)[0] for d in disks)
        partitions = sum(len(d.get("分区") or []) for d in disks)

        summary, body = card("存储概览", accent, "storage", tag=f"{len(disks)} 块磁盘")
        body.addLayout(stat_row([
            ("总容量", V.gb(total_gb)),
            ("已使用", V.gb(used_gb)),
            ("使用率", f"{V.percent(V.fraction(used_gb, total_gb) * 100, 1)} %"),
            ("分区", f"{partitions} 个"),
        ]))
        body.addSpacing(theme.sp(12))
        body.addWidget(MeterBar(V.fraction(used_gb, total_gb), fill=accent))

        cards: list[tuple[QWidget, int]] = [(summary, 4)]
        span = 2 if len(disks) > 1 else 4
        for disk in disks:
            used, total = V.disk_usage(disk)
            frame, dbody = card(str(V.get(disk, "类型", "磁盘")), accent, "storage",
                                tag=V.gb(float(disk.get("容量_GB") or 0)))
            dbody.addWidget(ElidedLabel(str(V.get(disk, "型号")), "rowName"))
            dbody.addWidget(ElidedLabel("  ·  ".join(x for x in [
                str(V.get(disk, "接口")), str(V.get(disk, "固件"))
            ] if x != V.MISSING), "rowSub"))
            dbody.addSpacing(theme.sp(10))
            dbody.addWidget(MeterBar(V.fraction(used, total), fill=accent))

            parts = disk.get("分区") or []
            if len(parts) != 1:
                # 只有一个分区时，下面的分区行已经给出同样数字，避免重复
                dbody.addSpacing(theme.sp(4))
                dbody.addWidget(label(f"已用 {V.gb(used)} / {V.gb(total)}", "hintText"))

            if parts:
                dbody.addSpacing(theme.sp(12))
                dbody.addWidget(hline())
                dbody.addSpacing(theme.sp(10))
                for part in parts[:6]:
                    line = QHBoxLayout()
                    line.setSpacing(theme.sp(8))
                    letter = str(V.get(part, "盘符"))
                    label_text = part.get("标签")
                    if label_text in (None, "", V.MISSING):
                        name = letter
                    else:
                        name = f"{letter}  {label_text}"
                    line.addWidget(ElidedLabel(name.strip() or "分区", "rowName"), 1)
                    line.addWidget(pill(str(V.get(part, "文件系统")), accent))
                    dbody.addLayout(line)
                    p_used = float(part.get("已用_GB") or 0)
                    p_total = float(part.get("总计_GB") or 0)
                    dbody.addSpacing(theme.sp(4))
                    dbody.addWidget(MeterBar(V.fraction(p_used, p_total), fill=accent, height=6))
                    dbody.addSpacing(theme.sp(4))
                    dbody.addWidget(label(
                        f"{V.gb(p_used)} / {V.gb(p_total)}", "hintText"))
                    dbody.addSpacing(theme.sp(10))
            else:
                dbody.addSpacing(theme.sp(10))
                dbody.addWidget(label("该磁盘没有可用分区信息", "hintText"))
            cards.append((frame, span))
        return cards

    def _cards_network(self, data: dict) -> list[tuple[QWidget, int]]:
        accent = theme.accent("network")
        adapters = V.items(data, "network")
        if not adapters:
            return [(self._empty_card("未检测到网卡"), 4)]

        connected = [a for a in adapters if str(a.get("状态", "")) == "已连接"]
        wifi = [a for a in adapters if "无线" in str(a.get("类型", ""))]
        summary, body = card("网络概览", accent, "network", tag=f"{len(adapters)} 个适配器")
        body.addLayout(stat_row([
            ("适配器", f"{len(adapters)} 个"),
            ("已连接", f"{len(connected)} 个"),
            ("无线", f"{len(wifi)} 个"),
        ]))
        if connected:
            body.addSpacing(theme.sp(10))
            body.addWidget(ElidedLabel(
                f"当前连接：{V.get(connected[0], '名称')}", "rowSub"))

        cards: list[tuple[QWidget, int]] = [(summary, 4)]
        span = 2 if len(adapters) > 1 else 4
        # 已连接的排前面
        ordered = connected + [a for a in adapters if a not in connected]
        for adapter in ordered:
            status = str(V.get(adapter, "状态"))
            frame, abody = card(str(V.get(adapter, "类型", "网卡")), accent, "network",
                                tag=status)
            abody.addWidget(ElidedLabel(str(V.get(adapter, "名称")), "rowName"))
            abody.addWidget(ElidedLabel(str(V.get(adapter, "厂商")), "rowSub"))
            abody.addSpacing(theme.sp(10))
            rows = V.flat_rows(adapter, skip=("名称", "厂商", "类型", "状态"))
            abody.addWidget(definition_grid(rows, columns=2))
            cards.append((frame, span))
        return cards

    def _cards_audio(self, data: dict) -> list[tuple[QWidget, int]]:
        accent = theme.accent("audio")
        devices = V.items(data, "audio")
        if not devices:
            return [(self._empty_card("未检测到音频设备"), 4)]
        span = 2 if len(devices) > 1 else 4
        cards = []
        for device in devices:
            frame, body = card(str(V.get(device, "位置", "音频设备")), accent, "audio",
                               tag=str(V.get(device, "状态")))
            body.addWidget(ElidedLabel(str(V.get(device, "名称")), "rowName"))
            body.addWidget(ElidedLabel(str(V.get(device, "厂商")), "rowSub"))
            body.addSpacing(theme.sp(10))
            rows = V.flat_rows(device, skip=("名称", "厂商", "位置", "状态"))
            body.addWidget(definition_grid(rows, columns=2))
            cards.append((frame, span))
        return cards

    def _cards_monitor(self, data: dict) -> list[tuple[QWidget, int]]:
        accent = theme.accent("monitor")
        monitors = V.items(data, "monitor")
        if not monitors:
            return [(self._empty_card("未检测到显示器"), 4)]
        span = 2 if len(monitors) > 1 else 4
        cards = []
        for index, monitor in enumerate(monitors, 1):
            status = str(V.get(monitor, "状态"))
            has_status = bool(status) and status != V.MISSING
            frame, body = card(f"显示器 {index}", accent, "monitor",
                               tag=status if has_status else None)
            if has_status and status != "活动":
                # 未连接的显示器用中性色，避免读起来像「活动」
                set_tag(frame, status, theme.P["muted"])
            body.addWidget(ElidedLabel(str(V.get(monitor, "型号")), "rowName"))
            body.addWidget(ElidedLabel(str(V.get(monitor, "厂商")), "rowSub"))
            body.addSpacing(theme.sp(10))
            rows = V.flat_rows(monitor, skip=("型号", "厂商", "状态"))
            body.addWidget(definition_grid(rows, columns=2))
            cards.append((frame, span))
        return cards

    # ------------------------------------------------------------ 辅助

    def _empty_card(self, text: str) -> QWidget:
        return state_card("box", theme.accent(self.category), "无数据", text, status="未采集")

    def _copy_summary(self) -> None:
        text = self._summary_text()
        if text:
            QApplication.clipboard().setText(text)

    def _summary_text(self) -> str:
        if self._result is None or self.category not in self._result.data:
            return ""
        data = self._result.data[self.category]
        title = CATEGORY_LABELS.get(self.category, self.category)
        lines = [f"HWInfo · {title}"]
        if isinstance(data, dict):
            for key, value in data.items():
                if key.startswith("_") or isinstance(value, (list, dict)):
                    continue
                lines.append(f"{V.field_label(key)}: {V.field_value(key, value)}")
            for item in V.items(data, self.category):
                lines.append("")
                for key, value in item.items():
                    if isinstance(value, (list, dict)):
                        continue
                    lines.append(f"  {V.field_label(key)}: {V.field_value(key, value)}")
        return "\n".join(lines)
