"""
collectors/os_info.py - 操作系统信息采集
"""
import os

from core.base import BaseCollector, CollectorError
from core.registry import register_collector
from utils.wmi_helper import get_wmi, parse_wmi_datetime, parse_wmi_date_only


@register_collector
class OSCollector(BaseCollector):
    name = "os"
    label = "操作系统"
    order = 10

    def collect(self) -> dict:
        """采集操作系统信息"""
        try:
            c = get_wmi()
            os_list = c.Win32_OperatingSystem()
        except Exception as e:
            raise CollectorError(self.name, f"无法访问操作系统信息: {e}")

        if not os_list:
            raise CollectorError(self.name, "未获取到操作系统信息")

        op_sys = os_list[0]

        # 拼接版本号
        version = op_sys.Version or ""
        build = op_sys.BuildNumber or ""
        version_str = f"{version} ({build})" if build else version

        result = {
            "系统名称": (op_sys.Caption or "").strip(),
            "版本号": version_str,
            "系统架构": op_sys.OSArchitecture or None,
            "安装日期": parse_wmi_date_only(op_sys.InstallDate),
            "上次启动": parse_wmi_datetime(op_sys.LastBootUpTime),
            "系统目录": op_sys.WindowsDirectory or None,
            "用户名": os.environ.get("USERNAME"),
        }

        return result

    def get_brief_fields(self) -> list[str]:
        return ["系统名称", "版本号", "系统架构"]
