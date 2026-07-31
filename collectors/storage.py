"""
collectors/storage.py - 存储设备信息采集
"""
from core.base import BaseCollector, CollectorError
from core.registry import register_collector
from utils.wmi_helper import get_wmi
from utils.format_utils import bytes_to_gb


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

        # 获取分区→盘符映射（复用已查询的 drives，避免重复 WMI 调用）
        partition_map = self._build_partition_map(c, drives)

        for drive in drives:
            disk_info = self._parse_drive(drive, partition_map, warnings)
            disk_list.append(disk_info)

        result = {"磁盘列表": disk_list}
        if warnings:
            result["_警告"] = warnings
        return result

    def get_brief_fields(self) -> list[str]:
        return ["磁盘列表"]

    def _parse_drive(self, drive, partition_map: dict, warnings: list) -> dict:
        """解析单个磁盘"""
        model = (drive.Model or "").strip()
        interface_type = drive.InterfaceType or "未知"

        # 判断接口类型
        pnp_id = (drive.PNPDeviceID or "").upper()
        if "NVME" in pnp_id or "NVME" in model.upper():
            interface_display = "NVMe"
        elif interface_type == "IDE" or interface_type == "SATA":
            interface_display = "SATA"
        elif interface_type == "SCSI":
            interface_display = "NVMe" if "NVME" in pnp_id or "ssd" in model.lower() else "SATA"
        else:
            interface_display = interface_type

        # 判断 SSD/HDD（通过关键词和 PNP ID 推断）
        disk_type = self._get_disk_type(drive, model)

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

    def _build_partition_map(self, c, drives) -> dict:
        """构建物理磁盘→逻辑分区的映射"""
        result = {}  # {"\\\\.\\PHYSICALDRIVE0": [{"盘符": "C:", ...}]}

        try:
            # 获取所有逻辑磁盘
            logical_disks = c.Win32_LogicalDisk()
            disk_info_map = {}
            for ld in logical_disks:
                if ld.DeviceID and ld.DriveType in (2, 3):  # 可移动磁盘或本地磁盘
                    disk_info_map[ld.DeviceID] = {
                        "盘符": ld.DeviceID,
                        "标签": (ld.VolumeName or "").strip() or None,
                        "文件系统": ld.FileSystem or None,
                        "已用_GB": None,
                        "总计_GB": None,
                    }
                    if ld.Size:
                        disk_info_map[ld.DeviceID]["总计_GB"] = bytes_to_gb(int(ld.Size))
                    if ld.FreeSpace and ld.Size:
                        used = int(ld.Size) - int(ld.FreeSpace)
                        disk_info_map[ld.DeviceID]["已用_GB"] = bytes_to_gb(used)

            # 通过关联查询建立映射（复用已查询的 drives 对象）
            for disk in drives:
                physical_id = disk.DeviceID
                result[physical_id] = []

                # 查询该物理磁盘的分区
                try:
                    partitions = disk.associators(wmi_result_class="Win32_DiskPartition")
                    for part in partitions:
                        # 查询分区对应的逻辑磁盘
                        try:
                            logicals = part.associators(wmi_result_class="Win32_LogicalDisk")
                            for logical in logicals:
                                if logical.DeviceID in disk_info_map:
                                    result[physical_id].append(disk_info_map[logical.DeviceID])
                        except Exception:
                            pass
                except Exception:
                    pass
        except Exception:
            pass

        return result

    def _get_disk_type(self, drive, model: str) -> str:
        """推断磁盘类型 SSD/HDD（通过关键词和 PNP ID）"""
        model_lower = model.lower()

        # PNP ID 判断 NVMe（最可靠）
        pnp_id = (drive.PNPDeviceID or "").upper()
        if "NVME" in pnp_id:
            return "SSD"

        ssd_keywords = ["ssd", "nvme", "sn7", "sn8", "sn5", "p5", "p3", "p1",
                        "980", "970", "960", "990", "gx", "kingston", "crucial"]
        for kw in ssd_keywords:
            if kw in model_lower:
                return "SSD"

        hdd_patterns = [
            "barracuda", "blue", "black", "red", "purple", "gold",
            "ironwolf", "skyhawk", "surveillance",
            "toshiba", "seagate",
        ]
        for kw in hdd_patterns:
            if kw in model_lower:
                return "HDD"

        if model_lower.startswith("wd") or "western digital" in model_lower:
            return "HDD"
        if model_lower.startswith("st") and model_lower[2:3].isdigit():
            return "HDD"

        return "未知"
