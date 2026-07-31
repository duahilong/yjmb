"""
utils/pci_ids.py - PCI ID 数据库解析与查询

解析 pci.ids 文件格式，提供 VEN/DEV ID 到品牌/设备名的翻译。
文件格式：
  - 无缩进行: 'XXXX  Vendor Name'
  - 一级Tab缩进: '\tXXXX  Device Name'
  - 二级Tab缩进: '\t\tXXXX XXXX  Subsystem Name'（忽略）
  - '#' 开头为注释，跳过
"""
import os
import re

# 项目根目录
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 默认 pci.ids 文件路径
_DEFAULT_PCI_IDS_PATH = os.path.join(_PROJECT_ROOT, "data", "pci.ids")


class PciIdsDatabase:
    """pci.ids 文件解析与查询"""

    def __init__(self, filepath: str = None):
        """
        加载 pci.ids 文件。
        默认路径: 程序目录下 data/pci.ids
        """
        self._vendors: dict[str, str] = {}       # {"10de": "NVIDIA Corporation"}
        self._devices: dict[str, str] = {}       # {"10de:2782": "GeForce RTX 4070 Ti"}
        self._loaded = False
        self._load(filepath or _DEFAULT_PCI_IDS_PATH)

    def _load(self, filepath: str) -> None:
        """解析 pci.ids 文件"""
        if not os.path.exists(filepath):
            return

        try:
            current_vendor = None

            with open(filepath, "r", encoding="utf-8", errors="replace") as f:
                for line in f:
                    # 跳过注释和空行
                    if not line or line.startswith("#") or line.strip() == "":
                        continue

                    # 判断缩进级别
                    if line.startswith("\t\t"):
                        # 二级缩进：子系统信息，忽略
                        continue
                    elif line.startswith("\t"):
                        # 一级缩进：设备信息
                        if current_vendor:
                            match = re.match(r"\t(\w{4})\s+(.+)", line)
                            if match:
                                device_id = match.group(1).lower()
                                device_name = match.group(2).strip()
                                key = f"{current_vendor}:{device_id}"
                                self._devices[key] = device_name
                    else:
                        # 无缩进：厂商信息
                        match = re.match(r"(\w{4})\s+(.+)", line)
                        if match:
                            current_vendor = match.group(1).lower()
                            vendor_name = match.group(2).strip()
                            self._vendors[current_vendor] = vendor_name

            self._loaded = True
        except Exception:
            pass

    @property
    def is_loaded(self) -> bool:
        """数据库是否成功加载"""
        return self._loaded

    def get_vendor(self, vendor_id: str) -> str | None:
        """查询厂商名。vendor_id 如 '10de'（小写，无0x前缀）"""
        return self._vendors.get(vendor_id.lower())

    def get_device(self, vendor_id: str, device_id: str) -> str | None:
        """查询设备名。返回如 'GeForce RTX 4070 Ti'"""
        key = f"{vendor_id.lower()}:{device_id.lower()}"
        return self._devices.get(key)

    def resolve_name(self, pnp_device_id: str) -> str | None:
        """
        从 PNPDeviceID 字符串中提取 VEN/DEV 并查询。
        输入: 'PCI\\VEN_10DE&DEV_2782&SUBSYS_...'
        输出: 'NVIDIA Corporation GeForce RTX 4070 Ti' 或 None
        """
        if not pnp_device_id:
            return None

        pnp_upper = pnp_device_id.upper()

        # 提取 VEN ID
        ven_match = re.search(r"VEN_([0-9A-F]{4})", pnp_upper)
        if not ven_match:
            return None
        vendor_id = ven_match.group(1).lower()

        # 提取 DEV ID
        dev_match = re.search(r"DEV_([0-9A-F]{4})", pnp_upper)
        if not dev_match:
            # 只有厂商
            vendor_name = self.get_vendor(vendor_id)
            return vendor_name

        device_id = dev_match.group(1).lower()

        # 组合查询
        vendor_name = self.get_vendor(vendor_id)
        device_name = self.get_device(vendor_id, device_id)

        if vendor_name and device_name:
            return f"{vendor_name} {device_name}"
        elif device_name:
            return device_name
        elif vendor_name:
            return vendor_name
        else:
            return None


# 全局单例
_db_instance: PciIdsDatabase | None = None


def get_pci_db() -> PciIdsDatabase:
    """获取全局 PciIdsDatabase 单例"""
    global _db_instance
    if _db_instance is None:
        _db_instance = PciIdsDatabase()
    return _db_instance
