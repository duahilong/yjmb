"""
tests/test_pci_ids.py - PCI ID 数据库解析测试
"""
import pytest
from utils.pci_ids import PciIdsDatabase


class TestPciIdsDatabase:
    """使用迷你测试文件验证解析逻辑"""

    def test_load_success(self, mini_pci_ids_file):
        db = PciIdsDatabase(mini_pci_ids_file)
        assert db.is_loaded is True

    def test_load_nonexistent(self, tmp_path):
        db = PciIdsDatabase(str(tmp_path / "nonexistent.ids"))
        assert db.is_loaded is False

    def test_get_vendor(self, mini_pci_ids_file):
        db = PciIdsDatabase(mini_pci_ids_file)
        assert db.get_vendor("10de") == "NVIDIA Corporation"
        assert db.get_vendor("8086") == "Intel Corporation"

    def test_get_vendor_case_insensitive(self, mini_pci_ids_file):
        db = PciIdsDatabase(mini_pci_ids_file)
        assert db.get_vendor("10DE") == "NVIDIA Corporation"

    def test_get_vendor_unknown(self, mini_pci_ids_file):
        db = PciIdsDatabase(mini_pci_ids_file)
        assert db.get_vendor("ffff") is None

    def test_get_device(self, mini_pci_ids_file):
        db = PciIdsDatabase(mini_pci_ids_file)
        assert db.get_device("10de", "1234") == "Test GPU Device"
        assert db.get_device("8086", "0046") == "Core Processor Integrated Graphics"

    def test_get_device_unknown(self, mini_pci_ids_file):
        db = PciIdsDatabase(mini_pci_ids_file)
        assert db.get_device("10de", "ffff") is None

    def test_resolve_name_full(self, mini_pci_ids_file):
        db = PciIdsDatabase(mini_pci_ids_file)
        result = db.resolve_name("PCI\\VEN_10DE&DEV_1234&SUBSYS_00000000")
        assert result == "NVIDIA Corporation Test GPU Device"

    def test_resolve_name_vendor_only(self, mini_pci_ids_file):
        db = PciIdsDatabase(mini_pci_ids_file)
        # 只有 VEN 没有 DEV
        result = db.resolve_name("PCI\\VEN_8086&SUBSYS_00000000")
        assert result == "Intel Corporation"

    def test_resolve_name_empty(self, mini_pci_ids_file):
        db = PciIdsDatabase(mini_pci_ids_file)
        assert db.resolve_name("") is None
        assert db.resolve_name(None) is None

    def test_resolve_name_no_match(self, mini_pci_ids_file):
        db = PciIdsDatabase(mini_pci_ids_file)
        result = db.resolve_name("PCI\\VEN_FFFF&DEV_0001")
        assert result is None

    def test_comments_ignored(self, mini_pci_ids_file):
        """注释行不应被解析为厂商"""
        db = PciIdsDatabase(mini_pci_ids_file)
        # '#' 开头的行不应产生任何条目
        assert db.get_vendor("#") is None


class TestPciIdsRealDatabase:
    """测试真实 pci.ids 文件（如果存在）"""

    def test_real_db_loads(self):
        """真实数据库应能成功加载"""
        db = PciIdsDatabase()  # 使用默认路径
        if db.is_loaded:
            # NVIDIA 应该存在
            assert db.get_vendor("10de") is not None
            # Intel 应该存在
            assert db.get_vendor("8086") is not None
