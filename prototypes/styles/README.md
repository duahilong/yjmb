# HWInfo GUI · 5 套风格原型

同一份 mock 数据、同样 1440×900，只换视觉语言。用于先定风格，再进入正式重写。

## 运行

```bash
# 单独打开某一套
python prototypes/styles/blueprint.py
python prototypes/styles/editorial.py
python prototypes/styles/bento.py
python prototypes/styles/glass.py
python prototypes/styles/printout.py

# 一次渲染全部 5 张 PNG 到 out/
python prototypes/styles/render_styles.py
```

> 渲染脚本用 `windows` 平台插件；`offscreen` 在 Windows 上取不到系统字体，中文会变方框。

## 五套风格

| 编号 | 文件 | 名称 | 一句话 |
|---|---|---|---|
| 01 | `blueprint.py` | 蓝图工程图 | 深蓝底 + 白色技术线稿 + 系统框图 + 尺寸线 + 图签 |
| 02 | `editorial.py` | 规格手册 | 冷白纸面 + Georgia 衬线大字号 + 朱红 + 三栏排版 |
| 03 | `bento.py` | 便当格 | 浅灰底 + 白色大圆角卡片 + 每类一色 |
| 04 | `glass.py` | 深色玻璃 | 夜黑渐变 + 柔光 + 磨砂面板 + 青紫渐变 |
| 05 | `printout.py` | 点阵打印 | 米白纸张 + 等宽字体 + 点线 + 印章 + 条形码 |

## 便当格关键页面（已选定方向）

| 编号 | 文件 | 页面 |
|---|---|---|
| 01 | `bento.py` | 总览 |
| 02 | `bento_detail.py` | 处理器详情（标量型模板） |
| 03 | `bento_detail_storage.py` | 存储详情（列表型模板） |
| 04 | `bento_settings.py` | 设置 |
| 05 | `bento_states.py` | 加载 / 空 / 失败 + 渐进采集 |

```bash
python prototypes/styles/render_pages.py      # 渲染整套页面到 out/
```

评审页：`gallery.html`（五套风格）、`gallery_pages.html`（便当格页面集）。

## 共用资源

- `prototypes/shared/mock_data.py`：模拟数据（真机采集结果）
- `prototypes/shared/ui.py`：字体、线性图标、圆环 / 进度条 / 插槽 / 条形码 / 印章 / 渐变文字等自绘组件

## 约束

- 只用 Windows 自带字体（Bahnschrift / Georgia / Cascadia Mono / 微软雅黑），不打包字体
- 纯 Qt Widgets + QSS + QPainter，不引入 WebView / QML
- 不接真实采集，不改动现有 `gui/`
