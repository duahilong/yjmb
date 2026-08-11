"""
utils/registry.py - Windows 注册表工具
"""


def get_driver_version(pnp_device_id: str) -> str | None:
    """
    从注册表读取指定设备的驱动版本（极快，<10ms）。

    原理（适用于所有 PnP 设备，如网卡/音频/显卡）：
    1. HKLM\\SYSTEM\\CurrentControlSet\\Enum\\<PNPDeviceID> 下的 Driver 值
       指向 {ClassGUID}\\InstanceID
    2. HKLM\\SYSTEM\\CurrentControlSet\\Control\\Class\\<Driver路径> 下
       的 DriverVersion 即为驱动版本

    注：不使用 Win32_PnPSignedDriver（枚举所有驱动，耗时 3-5s，是性能瓶颈）。
    """
    if not pnp_device_id:
        return None
    import winreg
    try:
        # 步骤 1：读取设备的 Driver 值（格式：{ClassGUID}\\InstanceID）
        dev_key = winreg.OpenKey(
            winreg.HKEY_LOCAL_MACHINE,
            rf"SYSTEM\CurrentControlSet\Enum\{pnp_device_id}"
        )
        try:
            driver_path, _ = winreg.QueryValueEx(dev_key, "Driver")
        except FileNotFoundError:
            return None
        finally:
            winreg.CloseKey(dev_key)

        # 步骤 2：从 Class 注册表键读取 DriverVersion
        # driver_path 格式: "{4d36e96c-e325-11ce-bfc1-08002be10318}\0001"
        class_key = winreg.OpenKey(
            winreg.HKEY_LOCAL_MACHINE,
            rf"SYSTEM\CurrentControlSet\Control\Class\{driver_path}"
        )
        try:
            version, _ = winreg.QueryValueEx(class_key, "DriverVersion")
            return version.strip() if version else None
        except FileNotFoundError:
            return None
        finally:
            winreg.CloseKey(class_key)
    except Exception:
        return None
