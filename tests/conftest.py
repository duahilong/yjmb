"""
tests/conftest.py - 共享 fixtures
"""
import sys
import os
import pytest

# 确保项目根目录在 sys.path 中
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture
def sample_cpu_data():
    """CPU 模块的模拟采集结果"""
    return {
        "名称": "Intel(R) Core(TM) i7-13700K",
        "厂商": "GenuineIntel",
        "架构": "x64",
        "插槽": "LGA1700",
        "核心数": 16,
        "线程数": 24,
        "基础频率_MHz": 3400,
        "L2缓存_MB": 24,
        "L3缓存_MB": 30,
        "指令集": ["SSE", "SSE2", "AVX", "AVX2"],
        "虚拟化": True,
        "当前负载_百分比": 12.5,
    }


@pytest.fixture
def sample_storage_data():
    """存储模块的模拟采集结果"""
    return {
        "磁盘列表": [
            {
                "型号": "Samsung SSD 980 PRO 1TB",
                "类型": "SSD",
                "接口": "NVMe",
                "容量_GB": 931.5,
                "固件": "5B2QGXA7",
                "序列号": "S5GXNY0R123456",
                "分区": [
                    {"盘符": "C:", "标签": "系统", "文件系统": "NTFS",
                     "已用_GB": 200.5, "总计_GB": 930.6},
                ],
            },
            {
                "型号": "WDC WD20EZAZ-00GGJB0",
                "类型": "HDD",
                "接口": "SATA",
                "容量_GB": 1863.0,
                "固件": "80.00A80",
                "序列号": "WD-WCC123456789",
                "分区": [
                    {"盘符": "D:", "标签": "数据", "文件系统": "NTFS",
                     "已用_GB": 800.0, "总计_GB": 1862.9},
                ],
            },
        ]
    }


@pytest.fixture
def sample_collect_result(sample_cpu_data, sample_storage_data):
    """模拟的 CollectResult"""
    from core.manager import CollectResult
    return CollectResult(
        data={"cpu": sample_cpu_data, "storage": sample_storage_data},
        errors=[],
        warnings=[],
        elapsed_seconds=1.23,
    )


@pytest.fixture
def mini_pci_ids_file(tmp_path):
    """创建一个迷你 pci.ids 测试文件"""
    content = """\
# 测试用 pci.ids
10de  NVIDIA Corporation
\t1234  Test GPU Device
\t5678  Another GPU
8086  Intel Corporation
\t0046  Core Processor Integrated Graphics
"""
    filepath = tmp_path / "test_pci.ids"
    filepath.write_text(content, encoding="utf-8")
    return str(filepath)
