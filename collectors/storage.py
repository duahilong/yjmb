"""
collectors/storage.py - 存储设备信息采集
"""
from core.base import BaseCollector, CollectorError
from core.registry import register_collector
from utils.logger import get_logger
from utils.wmi_helper import get_wmi, get_wmi_namespace
from utils.format_utils import bytes_to_gb

logger = get_logger(__name__)

# MSFT_PhysicalDisk.MediaType：0=未指定，3=HDD，4=SSD，5=SCM
_MEDIA_TYPE_MAP = {3: "HDD", 4: "SSD", 5: "SCM"}

# MSFT_PhysicalDisk.BusType（Storage Management API）
_BUS_TYPE_MAP = {
    3: "ATA",
    7: "USB",
    8: "RAID",
    10: "SAS",
    11: "SATA",
    14: "虚拟",
    15: "虚拟",
    16: "存储空间",
    17: "NVMe",
}


@register_collector
class StorageCollector(BaseCollector):
    name = "storage"
    label = "存储设备"
    order = 60

    def collect(self) -> dict:
        """采集存储设备信息"""
        try:
            c = get_wmi()
            drives = c.Win32_DiskDrive()
        except Exception as e:
            raise CollectorError(self.name, f"无法访问磁盘信息: {e}")

        if not drives:
            raise CollectorError(self.name, "未检测到磁盘")

        warnings = []
        disk_list = []

        # MSFT_PhysicalDisk 提供准确的 MediaType/BusType（Win8+，无需管理员）
        physical_map = self._get_physical_disk_map()

        # 用关联类一次性建立 物理磁盘→分区→盘符 映射，避免逐盘 associators()
        partition_map = self._build_partition_map(c, drives)

        for drive in drives:
            disk_info = self._parse_drive(drive, partition_map, physical_map, warnings)
            disk_list.append(disk_info)

        result = {"磁盘列表": disk_list}
        if warnings:
            result["_警告"] = warnings
        return result

    def get_brief_fields(self) -> list[str]:
        return ["磁盘列表"]

    def _get_physical_disk_map(self) -> dict[int, dict]:
        """读取 MSFT_PhysicalDisk，返回 {磁盘索引: {"media_type", "bus_type"}}。

        该命名空间在 Win8+ 可用且通常不要求管理员权限；
        查询失败（旧系统/精简系统）时返回空字典，由关键词兜底。
        """
        try:
            ns = get_wmi_namespace(r"root\Microsoft\Windows\Storage")
            rows = ns.query(
                "SELECT DeviceId, MediaType, BusType FROM MSFT_PhysicalDisk"
            )
        except Exception:
            logger.debug("无法读取 MSFT_PhysicalDisk，回退到关键词推断", exc_info=True)
            return {}

        result = {}
        for row in rows:
            try:
                index = int(row.DeviceId)
            except (TypeError, ValueError):
                continue
            result[index] = {
                "media_type": row.MediaType,
                "bus_type": row.BusType,
            }
        return result

    def _parse_drive(
        self,
        drive,
        partition_map: dict,
        physical_map: dict[int, dict],
        warnings: list,
    ) -> dict:
        """解析单个磁盘"""
        model = (drive.Model or "").strip()

        # Win32_DiskDrive.Index 与 MSFT_PhysicalDisk.DeviceId 对应
        try:
            index = int(drive.Index)
        except (TypeError, ValueError):
            index = None
        physical = physical_map.get(index) if index is not None else None

        interface_display = self._resolve_interface(drive, physical)
        disk_type = self._resolve_disk_type(drive, model, physical)

        # 容量
        size_gb = bytes_to_gb(int(drive.Size)) if drive.Size else None

        # 获取该磁盘的分区
        device_id = drive.DeviceID
        partitions = partition_map.get(device_id, [])

        return {
            "型号": model,
            "类型": disk_type,
            "接口": interface_display,
            "容量_GB": size_gb,
            "固件": (drive.FirmwareRevision or "").strip() or None,
            "序列号": (drive.SerialNumber or "").strip() or None,
            "分区": partitions,
        }

    @staticmethod
    def _resolve_interface(drive, physical: dict | None) -> str:
        """接口类型：MSFT_PhysicalDisk.BusType 优先，WMI/PNP 兜底。"""
        if physical:
            bus_name = _BUS_TYPE_MAP.get(physical.get("bus_type"))
            if bus_name:
                return bus_name

        pnp_id = (drive.PNPDeviceID or "").upper()
        interface_type = drive.InterfaceType or ""

        if "NVME" in pnp_id:
            return "NVMe"

        # Windows 常把 SATA/NVMe 都报成 SCSI；没有 BusType 时按 SATA 处理，
        # 不再用型号里的 "ssd" 猜 NVMe（SATA SSD 也会带 SSD 字样）。
        if interface_type.upper() in ("IDE", "SATA", "SCSI", "ATA"):
            return "SATA"

        if interface_type.upper() == "USB" or "USB" in pnp_id:
            return "USB"

        return interface_type or "未知"

    def _resolve_disk_type(
        self, drive, model: str, physical: dict | None
    ) -> str:
        """磁盘类型：MSFT_PhysicalDisk.MediaType 优先，关键词兜底。"""
        if physical:
            media_name = _MEDIA_TYPE_MAP.get(physical.get("media_type"))
            if media_name:
                return media_name
        return self._get_disk_type(drive, model)

    def _build_logical_disk_map(self, c) -> dict:
        """构建 盘符 → 分区展示信息 的映射。"""
        result = {}
        for ld in c.Win32_LogicalDisk():
            if not ld.DeviceID or ld.DriveType not in (2, 3):  # 可移动磁盘或本地磁盘
                continue

            info = {
                "盘符": ld.DeviceID,
                "标签": (ld.VolumeName or "").strip() or None,
                "文件系统": ld.FileSystem or None,
                "已用_GB": None,
                "总计_GB": None,
            }
            if ld.Size:
                info["总计_GB"] = bytes_to_gb(int(ld.Size))
            if ld.FreeSpace and ld.Size:
                used = int(ld.Size) - int(ld.FreeSpace)
                info["已用_GB"] = bytes_to_gb(used)
            result[ld.DeviceID] = info
        return result

    def _build_partition_map(self, c, drives) -> dict:
        """构建物理磁盘→逻辑分区的映射。

        优先用两条关联类查询（O(1) 次 WMI 调用），失败时回退到
        逐盘 associators()，保证旧系统/异常 WMI 环境下仍能拿到分区。
        """
        result = {disk.DeviceID: [] for disk in drives if disk.DeviceID}

        try:
            disk_info_map = self._build_logical_disk_map(c)
        except Exception:
            logger.debug("读取逻辑磁盘失败", exc_info=True)
            disk_info_map = {}

        try:
            # Win32_DiskDriveToDiskPartition: Antecedent=物理磁盘, Dependent=分区
            dp = c.query(
                "SELECT Antecedent, Dependent FROM Win32_DiskDriveToDiskPartition"
            )
            # Win32_LogicalDiskToPartition: Antecedent=分区, Dependent=逻辑磁盘
            lp = c.query(
                "SELECT Antecedent, Dependent FROM Win32_LogicalDiskToPartition"
            )

            part_to_disk = {
                row.Dependent.DeviceID: row.Antecedent.DeviceID for row in dp
            }
            part_to_logical = {
                row.Antecedent.DeviceID: row.Dependent.DeviceID for row in lp
            }

            for part_id, physical_id in part_to_disk.items():
                logical_id = part_to_logical.get(part_id)
                if logical_id in disk_info_map:
                    result.setdefault(physical_id, []).append(
                        disk_info_map[logical_id]
                    )
            return result
        except Exception:
            logger.debug("关联类查询分区映射失败，回退到 associators", exc_info=True)
            return self._build_partition_map_associators(drives, disk_info_map)

    def _build_partition_map_associators(self, drives, disk_info_map: dict) -> dict:
        """旧实现：逐盘 associators()，仅在关联类查询失败时使用。"""
        result = {disk.DeviceID: [] for disk in drives if disk.DeviceID}

        for disk in drives:
            physical_id = disk.DeviceID
            if not physical_id:
                continue
            try:
                partitions = disk.associators(wmi_result_class="Win32_DiskPartition")
                for part in partitions:
                    try:
                        logicals = part.associators(
                            wmi_result_class="Win32_LogicalDisk"
                        )
                        for logical in logicals:
                            if logical.DeviceID in disk_info_map:
                                result[physical_id].append(
                                    disk_info_map[logical.DeviceID]
                                )
                    except Exception:
                        logger.debug("读取分区对应的逻辑磁盘失败", exc_info=True)
            except Exception:
                logger.debug("读取物理磁盘分区失败", exc_info=True)

        return result

    def _get_disk_type(self, drive, model: str) -> str:
        """关键词兜底（MSFT_PhysicalDisk 不可用时）。

        只保留指向性较强的型号片段，宁可返回「未知」也不根据品牌
        武断判 HDD/SSD（同品牌既有 HDD 也有 SSD）。
        """
        model_lower = model.lower()

        # PNP ID 判断 NVMe（最可靠）
        pnp_id = (drive.PNPDeviceID or "").upper()
        if "NVME" in pnp_id:
            return "SSD"

        ssd_keywords = (
            "ssd", "nvme", "solid state",
            "sn5", "sn7", "sn8", "sn9",
            "970", "980", "990",
            "a400", "bx500", "mx500",
        )
        for kw in ssd_keywords:
            if kw in model_lower:
                return "SSD"

        # 仅保留明确指向机械盘的系列/型号前缀
        hdd_keywords = (
            "barracuda", "ironwolf", "skyhawk",
            "wd red", "wd purple", "wd gold",
            "dt01", "hdwd", "mq01", "mq02", "mq03",
        )
        for kw in hdd_keywords:
            if kw in model_lower:
                return "HDD"

        return "未知"
