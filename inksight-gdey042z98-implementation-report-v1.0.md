# InkSight GDEY042Z98 4.2 寸三色墨水屏改造实施报告

> 版本: v1.0 | 日期: 2026-06-27 | 状态: 编译验证通过

---

## 一、改造概述

本次改造在 InkSight 固件中新增了对 GDEY042Z98 (4.2" 400x300 三色屏，黑/白/红) 的驱动支持，基于 GxEPD2 库硬件 SPI 方式实现。

**改造范围**: 2 个文件修改，0 个文件新增，0 个文件删除  
**编译状态**: 通过 (0 error, 0 warning)  
**资源占用**: RAM 31.2% (102156/327680 bytes), Flash 55.9% (1098320/1966080 bytes)

---

## 二、关键变更点

### 2.1 文件变更清单

| 文件 | 变更类型 | 行数变化 | 说明 |
|---|---|---|---|
| `firmware/platformio.ini` | 追加 | +30 行 | 新增 2 个编译环境 |
| `firmware/src/epd_driver.cpp` | 修改 | +120 行 | 新增 GDEY042Z98 条件编译分支 |

### 2.2 platformio.ini 变更

新增 2 个编译环境：

- `epd_42_gdey042z98_3c_c3_promini` — ESP32-C3 ProMini USB CDC 模式
- `epd_42_gdey042z98_3c_c3_std` — ESP32-C3 标准 UART 模式

关键宏定义：`-DEPD_PANEL_42_GDEY042Z98 -DEPD_BPP=2`

### 2.3 epd_driver.cpp 变更

在 GxEPD2 硬件 SPI 分支 (`#else` 区域) 中新增 GDEY042Z98 条件编译，涉及以下修改点：

1. **全局对象声明** (L848-L852): 新增 `GxEPD2_3C<GxEPD2_420c_GDEY042Z98>` 实例 `_gdey_display`
2. **DISPLAY_ROTATION** (L864-L865): GDEY042Z98 使用 rotation=1 (横屏)
3. **epdInit()** (L875-L888): 使用 `_gdey_display` 替代 `display` 进行初始化
4. **epdDisplay()** (L894-L926): GDEY042Z98 使用 `setFullWindow()` + `writeImage()` + `refresh(false)`
5. **epdDisplayFast()** (L929-L964): GDEY042Z98 使用 `refresh(true)` 快速刷新
6. **epdDisplayDeepClear()** (L967-L994): GDEY042Z98 使用 4 次交替全屏刷新清残影
7. **epdPartialDisplayWithOld()** (L1009-L1058): GDEY042Z98 支持局部刷新
8. **epdDisplay2bpp()** (L1062-L1113): **核心新增函数**，将 2bpp 数据拆分为 blackBuf + redBuf 双平面，调用 `GxEPD2_3C.writeImage(blackBuf, redBuf)`
9. **epdSleep()** (L1116-L1125): GDEY042Z98 使用 `_gdey_display.hibernate()`

---

## 三、实施过程中遇到的问题及解决方案

### 问题1：头文件路径错误

**现象**: 首次编译报错 `gdey/GxEPD2_420c_GDEY042Z98.h: No such file or directory`

**原因**: GxEPD2@1.6.9 版本中，三色屏驱动文件位于 `gdey3c/` 子目录（而非方案中预估的 `gdey/`），这与单色屏的目录命名不同。

**解决方案**: 将 `#include <gdey/GxEPD2_420c_GDEY042Z98.h>` 修正为 `#include <gdey3c/GxEPD2_420c_GDEY042Z98.h>`

**影响范围**: 同时修正了适配方案文档 `inksight-gdey042z98-adaptation-v1.0.md` 中的对应描述。

### 问题2：PlatformIO CLI 未预装

**现象**: 首次执行 `pio run` 报 `command not found: pio`

**原因**: 本地开发环境未安装 PlatformIO Core CLI

**解决方案**: 通过 `pip3 install platformio` 安装，安装路径为 `/Users/tangshan/Library/Python/3.9/bin/pio`，需添加到 PATH

**注意**: 安装 Trae IDE 的 PlatformIO 插件后，插件会自动管理 Core，无需手动安装。命令行编译需设置 PATH：
```bash
export PATH="$PATH:/Users/tangshan/Library/Python/3.9/bin"
```

---

## 四、编译验证结果

### 4.1 新环境编译

| 项目 | 结果 |
|---|---|
| 编译环境 | `epd_42_gdey042z98_3c_c3_promini` |
| 编译结果 | SUCCESS |
| 编译耗时 | 36.58 秒 |
| RAM 占用 | 31.2% (102156 / 327680 bytes) |
| Flash 占用 | 55.9% (1098320 / 1966080 bytes) |
| 固件输出 | `firmware_merged.bin` (0x126990 bytes = 1.2MB) |
| 错误数 | 0 |
| 警告数 | 0 |

### 4.2 原有环境回归验证

| 项目 | 结果 |
|---|---|
| 编译环境 | `epd_42_wsv2_ssd1683_c3_promini` (默认环境) |
| 编译结果 | SUCCESS |
| 编译耗时 | 35.65 秒 |
| 结论 | 改造未破坏原有面板的编译 |

---

## 五、GxEPD2 依赖版本

| 库 | 版本 | 说明 |
|---|---|---|
| GxEPD2 | 1.6.9 | 自动下载，含 GDEY042Z98 三色屏驱动 |
| Adafruit GFX Library | 1.12.6 | 图形基础库 |
| Adafruit BusIO | 1.17.4 | I2C/SPI 通信 |
| WebSockets | 2.7.3 | AI 语音 WebSocket |
| ESP32 Arduino Framework | 3.20017.241212 | Espressif 官方框架 |

---

## 六、待设备验证项

以下项目需在实际 ESP32-C3 + GDEY042Z98 硬件上验证：

| 序号 | 验证项 | 验证方法 | 通过标准 |
|---|---|---|---|
| 1 | BW 全刷新 | 渲染纯黑/白位图 | 无残影、无花屏 |
| 2 | 三色全刷新 | 后端 colors=4 模式渲染 | 黑/白/红三色正确 |
| 3 | 2bpp 颜色映射 | 4色测试图 | 颜色 0=黑 1=白 2=黄→红 3=红 正确 |
| 4 | 快速刷新 | 连续 9 次快速刷新 | 内容正确，闪烁可接受 |
| 5 | 局部刷新 | 更新时段标签 | 仅目标区域更新 |
| 6 | 深度休眠/唤醒 | 休眠后定时唤醒 | 唤醒后显示正常 |
| 7 | WiFi 配网 | 长按按钮进入 Portal | 配网页可访问 |
| 8 | 完整数据流 | 后端渲染→设备显示 | 三色模式端到端正常 |

---

## 七、方案文档更新记录

| 文件 | 更新内容 |
|---|---|
| `inksight-gdey042z98-adaptation-v1.0.md` | 修正头文件路径 `gdey/` → `gdey3c/` |

---

## 八、产出文件索引

| 文件 | 路径 |
|---|---|
| 适配方案文档 | `/Users/tangshan/Downloads/inksight-main/inksight-gdey042z98-adaptation-v1.0.md` |
| 改造实施报告 | `/Users/tangshan/Downloads/inksight-main/inksight-gdey042z98-implementation-report-v1.0.md` |
| 编译配置 | `/Users/tangshan/Downloads/inksight-main/firmware/platformio.ini` |
| 驱动源码 | `/Users/tangshan/Downloads/inksight-main/firmware/src/epd_driver.cpp` |
| 固件产物 | `/Users/tangshan/Downloads/inksight-main/firmware/.pio/build/epd_42_gdey042z98_3c_c3_promini/firmware_merged.bin` |
