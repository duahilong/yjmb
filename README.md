# HWInfo — Windows 硬件检测工具

类似于「鲁大师」硬件检测功能的轻量级工具，采集并展示 9 大类硬件信息（操作系统 / 主板 / CPU / 内存 / 显卡 / 存储 / 网络 / 音频 / 显示器），提供 CLI 命令行与 GUI 桌面应用两种形态。

## 功能

- **9 大类硬件采集**：并行采集，全量耗时约 1.3~2s，单模块失败不影响整体
- **NVIDIA 显卡增强**：通过 pynvml 补充负载 / 显存实时数据
- **离线 PCI ID 数据库**：内置 `data/pci.ids`，品牌翻译不依赖网络
- **CLI 模式**：美化终端输出（颜色 + Unicode 框线，自动降级）、JSON 输出、brief 简洁模式、`--debug` 调试
- **GUI 模式**（PySide6）：左侧导航 + 总览 / 详情 / 设置页，后台线程采集不卡界面，F5 刷新，导出 JSON
- **界面缩放**：左下角 `− / +` 按钮或快捷键 `Ctrl+- / Ctrl+= / Ctrl+0` 整体缩放界面与字体（0.7~1.6 倍），重启恢复默认
- **显示控制**：配置文件 `config.yaml` 或 GUI 设置页控制各类别的采集与显示

## 环境要求

| 项目 | 要求 |
|------|------|
| Python | ≥ 3.10 |
| 操作系统 | Windows 10 / 11 (64-bit)，WMI 服务正常 |
| 权限 | 非必需；管理员可获取更完整的磁盘健康信息 |

## 安装

```bash
pip install -r requirements.txt
# 或
pip install -e .
```

## 使用方法

### GUI（推荐）

```bash
python main.py
```

### CLI

```bash
# 采集并显示全部硬件信息
python main.py all

# 只看指定类别
python main.py cpu gpu memory

# 隐藏某些类别
python main.py all --hide audio,os

# JSON 格式输出
python main.py all --json

# 简洁模式（每类只显示关键字段）
python main.py all --brief

# 版本 / 调试
python main.py --version
python main.py all --debug
```

## 配置

程序同目录下的 `config.yaml`（无则使用 `config/default.yaml`）：

```yaml
display:
  os: true
  motherboard: true
  cpu: true
  memory: true
  gpu: true
  storage: true
  network: true
  audio: true
  monitor: true
```

## 打包为 EXE

```bash
build\build.bat
# 产物: dist\HWInfo.exe（单文件，双击运行 GUI）
```

## 测试

```bash
python -m pytest
# 单元测试：采集解析、GPU 分类、CLI 类别解析、格式化输出、pci.ids、配置、调度、界面缩放
```

## 目录结构

```
main.py          入口（无参数 → GUI，有参数 → CLI）
cli/             CLI 解析与执行
gui/             GUI 桌面应用（主窗口/页面/组件）
core/            核心调度（CollectorManager、注册表、常量）
collectors/      9 个采集模块
formatters/      输出格式化（terminal / json）
utils/           WMI 封装、pci.ids、PowerShell、格式化工具
config/          默认配置
data/pci.ids     PCI ID 离线数据库
build/           PyInstaller 打包配置
tests/           单元测试
docs/            需求文档与设计文档
```
