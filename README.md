# HWInfo — Windows 硬件检测工具

类似于「鲁大师」硬件检测功能的轻量级工具，采集并展示 9 大类硬件信息（操作系统 / 主板 / CPU / 内存 / 显卡 / 存储 / 网络 / 音频 / 显示器），提供 CLI 命令行与 GUI 桌面应用两种形态。

## 功能

- **9 大类硬件采集**：并行采集，全量耗时约 1.3~2s，单模块失败不影响整体
- **NVIDIA 显卡增强**：通过 pynvml 补充负载 / 显存实时数据
- **离线 PCI ID 数据库**：内置 `data/pci.ids`，品牌翻译不依赖网络
- **CLI 模式**：美化终端输出（颜色 + Unicode 框线，自动降级）、JSON 输出、brief 简洁模式、`--debug` 调试
- **GUI 模式**（PySide6）：Apple 风单页版式 —— 顶栏一行工具条 + 一张自绘画板，9 类信息一屏放下、不滚动；每个字段独占一行，按窗口宽度自动分 1–6 栏，字号自适应（8–40px）；纯白底、蓝色分类名、无卡片圆角；后台线程逐类回填不卡界面，F5 刷新，Ctrl+E 导出 JSON
- **信息量可调**：`全部 / 精简` 两档（精简档每类只留关键字段，197 → 149 项）；`标签` 开关隐藏左侧字段名让值更大；`Ctrl+K` 搜索字段或设备
- **外观可调**：浅色单主题，紧凑 / 舒适 / 大 三档密度，只用系统字体，不打包字体文件
- **界面缩放**：`Ctrl+- / Ctrl+=` 缩放顶栏与控件（0.7~1.6 倍，画板字号始终按窗口尺寸自适应）
- **显示控制**：配置文件 `config.yaml` 或设置对话框控制各类别的采集与显示（全部关闭即不采集，不会退化为全量）

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
utils/           WMI 封装、pci.ids、注册表、PowerShell、格式化、日志
config/          默认配置
data/pci.ids     PCI ID 离线数据库
build/           PyInstaller 打包配置
tests/           单元测试
docs/            需求文档、设计文档、后端优化计划
prototypes/      GUI 视觉方案原型（不参与打包）
```
