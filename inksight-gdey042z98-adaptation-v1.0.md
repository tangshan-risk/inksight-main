# InkSight GDEY042Z98 4.2 寸三色墨水屏适配方案

> 版本: v1.0 | 日期: 2026-06-27 | 目标硬件: ESP32-C3 + GDEY042Z98 (4.2" 400×300 三色屏)

---

## 目录

1. [环境依赖检查与安装指南](#1-环境依赖检查与安装指南)
2. [项目结构改造要点](#2-项目结构改造要点)
3. [编译参数配置说明](#3-编译参数配置说明)
4. [烧录工具选择与操作步骤](#4-烧录工具选择与操作步骤)
5. [常见问题排查与解决方案](#5-常见问题排查与解决方案)
6. [附录](#6-附录)

---

## 1. 环境依赖检查与安装指南

### 1.1 系统环境要求

| 项目 | 最低要求 | 推荐版本 |
|---|---|---|
| 操作系统 | macOS 12+ | macOS 14+ (当前环境满足) |
| Python | 3.8+ | 3.10+ |
| Node.js | 18+ | 20+ (仅后端/WebApp 开发需要，固件编译不需要) |
| USB 接口 | USB-C / USB-A | 需能正常识别串口设备 |
| 磁盘空间 | 2GB (PlatformIO 工具链) | 5GB+ |

### 1.2 Trae IDE 安装 PlatformIO 插件

Trae IDE 基于 VS Code 内核，可直接安装 VS Code 扩展。

**步骤**:

1. 打开 Trae IDE
2. 点击左侧边栏扩展图标 (或 `Cmd+Shift+X`)
3. 搜索 **PlatformIO IDE**
4. 点击 **Install** 安装
5. 安装完成后，左侧边栏出现 PlatformIO 外星人头像图标
6. 底部状态栏出现 Build / Upload / Serial Monitor 等快捷按钮

**首次安装注意事项**:

- 安装过程需下载 PlatformIO Core、Python 虚拟环境及 ESP32 工具链，耗时约 3-5 分钟
- 安装完成后需重启 Trae IDE
- 检查安装成功：终端执行 `pio --version` 应输出版本号

### 1.3 Python 环境检查

```bash
# 检查 Python 版本 (macOS 自带)
python3 --version
# 预期输出: Python 3.x.x (>=3.8)

# 检查 pip
pip3 --version
```

PlatformIO 安装时会自动创建隔离的 Python 虚拟环境，**不需要手动安装任何 Python 包**。

### 1.4 USB 串口驱动

ESP32-C3 开发板通常使用 CH340 或 CP2102 USB 转串口芯片。

```bash
# 检查串口设备是否被识别
ls /dev/cu.usb* /dev/cu.wch* 2>/dev/null

# 如果无输出，需安装驱动:
# CH340: https://www.wch.cn/downloads/CH34XSER_MAC_ZIP.html
# CP2102: https://www.silabs.com/developers/usb-to-uart-bridge-vcp-drivers
```

### 1.5 依赖项汇总

| 依赖项 | 来源 | 说明 |
|---|---|---|
| PlatformIO Core | 自动安装 (插件附带) | 编译/烧录/监控 |
| ESP32 Arduino Framework | 自动下载 (首次编译时) | `espressif32` 平台 |
| GxEPD2@^1.5.0 | 自动下载 (lib_deps) | EPD 驱动库，含 GDEY042Z98 |
| Adafruit GFX Library@^1.11.0 | 自动下载 (lib_deps) | 图形基础库 |
| WebSockets@^2.6.1 | 自动下载 (lib_deps) | AI 语音 WebSocket |

**所有依赖项均由 PlatformIO 自动管理，无需手动安装。**

---

## 2. 项目结构改造要点

### 2.1 改造范围总览

只需修改 **2 个文件**，新增约 **200 行代码**，零文件新增，零文件删除。

| 文件 | 操作 | 改动量 | 说明 |
|---|---|---|---|
| `firmware/platformio.ini` | 末尾追加 | +30 行 | 新增 2 个编译环境 |
| `firmware/src/epd_driver.cpp` | 条件编译块追加 | +170 行 | 新增 GDEY042Z98 驱动分支 |

**无需修改的文件**:

| 文件 | 原因 |
|---|---|
| `firmware/src/config.h` | 引脚映射 (CS=7/DC=1/RST=2/BUSY=10) 与 ink_test 完全一致；`EPD_BPP`/`COLOR_BUF_LEN` 通过宏注入 |
| `firmware/src/display.h/cpp` | 仅操作 `imgBuf[]` 帧缓冲区，不直接操作 EPD 硬件；`smartDisplay()` 已处理 `useColorBuf` 路径 |
| `firmware/src/main.cpp` | `smartDisplay()` 中 `#if EPD_BPP >= 2` 分支已实现 `epdDisplay2bpp(colorBuf)` 调用 |
| `firmware/src/network.cpp` | `fetchBMP()` 已根据 `EPD_BPP >= 2` 自动请求 `colors=4` 并处理 2bpp 数据 |
| 后端代码 | `pipeline.generate_and_render()` 已支持 `colors=4` 三色渲染 |

### 2.2 改造一：platformio.ini 新增编译环境

在 `firmware/platformio.ini` 文件末尾追加以下内容：

```ini
# ── GDEY042Z98 4.2" 三色屏 (黑/白/红) GxEPD2 硬件SPI驱动 ──────────────────
[env:epd_42_gdey042z98_3c_c3_promini]
extends = common
board = esp32-c3-devkitm-1
build_flags =
    -DBOARD_PROFILE_ESP32_C3
    -DARDUINO_USB_MODE=1
    -DARDUINO_USB_CDC_ON_BOOT=1
    -DEPD_WIDTH=400
    -DEPD_HEIGHT=300
    -DEPD_PANEL_42_GDEY042Z98
    -DEPD_BPP=2
    -DALLOW_INSECURE_FALLBACK=0

[env:epd_42_gdey042z98_3c_c3_std]
extends = common
board = esp32-c3-devkitm-1
upload_speed = 460800
board_build.flash_mode = dio
board_build.f_flash = 40000000L
build_flags =
    -DBOARD_PROFILE_ESP32_C3
    -DARDUINO_USB_MODE=0
    -DARDUINO_USB_CDC_ON_BOOT=0
    -DEPD_WIDTH=400
    -DEPD_HEIGHT=300
    -DEPD_PANEL_42_GDEY042Z98
    -DEPD_BPP=2
    -DALLOW_INSECURE_FALLBACK=0
```

**编译环境说明**:

| 环境名 | 目标板 | USB 模式 | 适用场景 |
|---|---|---|---|
| `epd_42_gdey042z98_3c_c3_promini` | ESP32-C3 ProMini | USB CDC (模拟串口) | 推荐，多数 ESP32-C3 开发板 |
| `epd_42_gdey042z98_3c_c3_std` | ESP32-C3 标准板 | UART 串口 | 使用外部 USB-TTL 适配器的板子 |

**宏定义说明**:

| 宏 | 值 | 作用 |
|---|---|---|
| `BOARD_PROFILE_ESP32_C3` | — | 选择 ESP32-C3 引脚映射 (CS=7/DC=1/RST=2/BUSY=10) |
| `ARDUINO_USB_MODE` | 1 或 0 | 1=USB CDC 模式, 0=UART 模式 |
| `ARDUINO_USB_CDC_ON_BOOT` | 1 或 0 | 启动时是否启用 USB CDC，需与 USB_MODE 匹配 |
| `EPD_WIDTH` / `EPD_HEIGHT` | 400 / 300 | 屏幕分辨率 |
| `EPD_PANEL_42_GDEY042Z98` | — | 驱动分支选择标识 (条件编译) |
| `EPD_BPP` | 2 | 启用 2bpp 多色缓冲区，激活 `colorBuf` / `useColorBuf` 逻辑 |
| `ALLOW_INSECURE_FALLBACK` | 0 | 禁用不安全的 HTTP 回退 |

### 2.3 改造二：epd_driver.cpp 新增 GDEY042Z98 驱动分支

在 `firmware/src/epd_driver.cpp` 中，现有代码结构为：

```
#if defined(EPD_PANEL_42_SSD1683_BW) || ...
    // 分支1: 软件 SPI bit-bang 驱动 (SSD1683/DKE RY683/GDEM042F52)
#elif defined(EPD_PANEL_42_WFT)
    // 分支2: WFT042 旧版面板驱动
#else
    // 分支3: GxEPD2 硬件 SPI 驱动 (其他面板)
    // ← 在此分支内部，#else 之前插入 GDEY042Z98 条件块
#endif
```

需要在分支3 (GxEPD2 硬件 SPI 区域，约 L783 `#else` 之后) 的面板类型选择 `#if defined(...)` 链中，在 `#else` (报错分支，约 L848) 之前插入：

```cpp
#elif defined(EPD_PANEL_42_GDEY042Z98)
  #include <GxEPD2_3C.h>
  #include <gdey3c/GxEPD2_420c_GDEY042Z98.h>
  GxEPD2_3C<GxEPD2_420c_GDEY042Z98, GxEPD2_420c_GDEY042Z98::HEIGHT> _gdey_display(
      GxEPD2_420c_GDEY042Z98(PIN_EPD_CS, PIN_EPD_DC, PIN_EPD_RST, PIN_EPD_BUSY));
```

并在该分支3的函数实现区域，添加 GDEY042Z98 的特化实现。以下是完整的代码插入方案：

#### 2.3.1 全局对象声明区 (约 L793-L850 面板选择链)

在 `#elif defined(EPD_PANEL_75)` 之后、`#else` (error) 之前，插入：

```cpp
#elif defined(EPD_PANEL_42_GDEY042Z98)
  #include <GxEPD2_3C.h>
  #include <gdey3c/GxEPD2_420c_GDEY042Z98.h>
  GxEPD2_3C<GxEPD2_420c_GDEY042Z98, GxEPD2_420c_GDEY042Z98::HEIGHT> _gdey_display(
      GxEPD2_420c_GDEY042Z98(PIN_EPD_CS, PIN_EPD_DC, PIN_EPD_RST, PIN_EPD_BUSY));
```

#### 2.3.2 DISPLAY_ROTATION 常量

在现有 DISPLAY_ROTATION 定义 (约 L856-L861) 的条件链中追加：

```cpp
#elif defined(EPD_PANEL_42_GDEY042Z98)
    1;  // 横屏模式，与 ink_test 一致
```

#### 2.3.3 各函数实现

以下函数需要在 GxEPD2 分支的函数体内部添加 GDEY042Z98 的条件分支。

**gpioInit()** — 无需额外代码，GxEPD2 分支已有通用实现 (`SPI.begin(...)`)。

**epdInit()** — 添加 GDEY042Z98 条件：

```cpp
void epdInit() {
    if (!_initialized) {
#if defined(EPD_PANEL_42_GDEY042Z98)
        _gdey_display.epd2.selectSPI(SPI, SPISettings(EPD_GXEPD2_SPI_HZ, MSBFIRST, SPI_MODE0));
        _gdey_display.init(0);
        _gdey_display.setRotation(DISPLAY_ROTATION);
#else
        display.epd2.selectSPI(SPI, SPISettings(EPD_GXEPD2_SPI_HZ, MSBFIRST, SPI_MODE0));
        display.init(0);
        display.setRotation(DISPLAY_ROTATION);
#endif
        _initialized = true;
    }
}
```

**epdInitFast()** — 无需修改，GxEPD2 内部管理 LUT 切换。

**epdDisplay()** — 添加 GDEY042Z98 条件：

```cpp
void epdDisplay(const uint8_t *image) {
    epdInit();
#if defined(EPD_PANEL_42_GDEY042Z98)
    _gdey_display.setFullWindow();
    _gdey_display.writeImage(image, 0, 0, W, H);
    _gdey_display.refresh(false);
    _gdey_display.powerOff();
#elif defined(EPD_PANEL_29)
    // ... 现有代码 ...
#else
    // ... 现有代码 ...
#endif
}
```

**epdDisplayFast()** — 添加 GDEY042Z98 条件：

```cpp
void epdDisplayFast(const uint8_t *image) {
#if defined(EPD_PANEL_42_GDEY042Z98)
    epdInit();
    _gdey_display.setFullWindow();
    _gdey_display.writeImage(image, 0, 0, W, H);
    _gdey_display.refresh(true);
    _gdey_display.powerOff();
#else
    // ... 现有代码 ...
#endif
}
```

**epdDisplay2bpp()** — 这是三色屏的核心函数，需新增完整实现：

```cpp
void epdDisplay2bpp(const uint8_t *image2bpp) {
#if defined(EPD_PANEL_42_GDEY042Z98)
    epdInit();
    _gdey_display.setFullWindow();

    int total = (W / 8) * H;
    uint8_t *blackBuf = (uint8_t *)malloc(total);
    uint8_t *redBuf   = (uint8_t *)malloc(total);
    if (!blackBuf || !redBuf) {
        Serial.println("[EPD] 2bpp buffer alloc failed");
        free(blackBuf); free(redBuf);
        return;
    }
    memset(blackBuf, 0xFF, total);  // 默认白色
    memset(redBuf,   0x00, total);  // 默认无红色

    // 2bpp → 双平面拆分
    // 后端颜色映射: 0=黑, 1=白, 2=黄(映射为红), 3=红
    // GxEPD2_3C 约定: blackBuf 白=1/黑=0, redBuf 红=1/无红=0
    for (int y = 0; y < H; y++) {
        for (int x = 0; x < W; x++) {
            int pixelIdx = y * W + x;
            int byteIdx = pixelIdx / 4;
            int shift = (6 - (pixelIdx % 4) * 2);
            uint8_t color = (image2bpp[byteIdx] >> shift) & 0x03;

            int bufIdx = y * (W / 8) + (x / 8);
            int bitPos = x % 8;
            switch (color) {
                case 0:  // 黑
                    blackBuf[bufIdx] &= ~(0x80 >> bitPos);
                    redBuf[bufIdx]   |=  (0x80 >> bitPos);
                    break;
                case 1:  // 白
                    blackBuf[bufIdx] |=  (0x80 >> bitPos);
                    redBuf[bufIdx]   &= ~(0x80 >> bitPos);
                    break;
                case 2:  // 黄 → 映射为红 (三色屏物理限制)
                case 3:  // 红
                    blackBuf[bufIdx] |=  (0x80 >> bitPos);
                    redBuf[bufIdx]   |=  (0x80 >> bitPos);
                    break;
            }
        }
    }

    _gdey_display.writeImage(blackBuf, redBuf, 0, 0, W, H);
    _gdey_display.refresh(false);
    _gdey_display.powerOff();
    free(blackBuf);
    free(redBuf);
#else
    // 其他面板的 epdDisplay2bpp 由各分支自行实现
    // (现有代码中 BW 面板无此函数或 fallback 到 epdDisplay)
    epdDisplay(image2bpp);
#endif
}
```

> **注意**: `epdDisplay2bpp()` 函数在当前 `epd_driver.cpp` 中仅存在于 `#if defined(EPD_PANEL_42_SSD1683_BW)` 和 `#elif defined(EPD_PANEL_42_WFT)` 分支中，GxEPD2 分支（`#else` 部分）尚未定义此函数。需在 GxEPD2 分支中新增该函数定义。

**epdDisplayDeepClear()** — 添加 GDEY042Z98 条件：

```cpp
void epdDisplayDeepClear(const uint8_t *image) {
    epdInit();
#if defined(EPD_PANEL_42_GDEY042Z98)
    uint8_t *clearBuf = (uint8_t *)malloc(IMG_BUF_LEN);
    if (clearBuf) {
        for (int pass = 0; pass < 4; pass++) {
            memset(clearBuf, (pass % 2 == 0) ? 0x00 : 0xFF, IMG_BUF_LEN);
            _gdey_display.writeImage(clearBuf, 0, 0, W, H);
            _gdey_display.refresh(false);
        }
        free(clearBuf);
        _gdey_display.powerOff();
    }
    epdDisplay(image);
#else
    // ... 现有代码 ...
#endif
}
```

**epdPartialDisplayWithOld()** — 添加 GDEY042Z98 条件：

```cpp
void epdPartialDisplayWithOld(uint8_t *data, const uint8_t *oldData,
                               int xStart, int yStart, int xEnd, int yEnd) {
    epdInit();
#if defined(EPD_PANEL_42_GDEY042Z98)
    int w = xEnd - xStart;
    int h = yEnd - yStart;
    _gdey_display.setPartialWindow(xStart, yStart, w, h);
    if (oldData) {
        _gdey_display.epd2.writeImageAgain(oldData, xStart, yStart, w, h, false, false, true);
        _gdey_display.writeImage(data, xStart, yStart, w, h, false, false, true);
    } else {
        _gdey_display.writeImage(data, xStart, yStart, w, h, false, false, true);
        _gdey_display.epd2.writeImageAgain(data, xStart, yStart, w, h, false, false, true);
    }
    _gdey_display.refresh(xStart, yStart, w, h);
    _gdey_display.powerOff();
#else
    // ... 现有代码 ...
#endif
}
```

**epdSupportsPartialRefresh()** — 添加 GDEY042Z98 条件：

```cpp
bool epdSupportsPartialRefresh() {
#if defined(EPD_PANEL_42_GDEY042Z98)
    return true;  // GxEPD2_420c_GDEY042Z98 支持局部刷新
#else
    // ... 现有代码 ...
#endif
}
```

**epdSleep()** — 添加 GDEY042Z98 条件：

```cpp
void epdSleep() {
#if defined(EPD_PANEL_42_GDEY042Z98)
    _gdey_display.hibernate();
    _initialized = false;
#else
    display.hibernate();
    _initialized = false;
    // ... 现有代码 ...
#endif
}
```

### 2.4 引脚映射对照

| 功能引脚 | InkSight ESP32-C3 | ink_test ESP32-C3 | 一致性 |
|---|---|---|---|
| MOSI | GPIO 6 | GPIO 6 | 完全一致 |
| SCK | GPIO 4 | GPIO 4 | 完全一致 |
| CS | GPIO 7 | GPIO 7 | 完全一致 |
| DC | GPIO 1 | GPIO 1 | 完全一致 |
| RST | GPIO 2 | GPIO 2 | 完全一致 |
| BUSY | GPIO 10 | GPIO 10 | 完全一致 |

### 2.5 数据流路径

```
后端渲染 (Pillow, 400x300, colors=4)
    │
    ▼
HTTP GET /api/device/{mac}/render?format=2bpp&colors=4
    │
    ▼
2bpp packed 数据 (30000 bytes, 颜色: 0=黑 1=白 2=黄 3=红)
    │
    ▼
network.cpp: fetchBMP() → 写入 colorBuf[], 置 useColorBuf=true
    │
    ▼
main.cpp: smartDisplay() → 检测 useColorBuf → epdDisplay2bpp(colorBuf)
    │
    ▼
epd_driver.cpp: epdDisplay2bpp()
    │  2bpp → 双平面拆分 (blackBuf + redBuf)
    │  黄色(2) → 映射为红色 (三色屏物理限制)
    ▼
GxEPD2_3C.writeImage(blackBuf, redBuf, 0, 0, 400, 300)
    │
    ▼
GxEPD2_3C.refresh() → SPI 发送到 GDEY042Z98 控制器
    │
    ▼
墨水屏显示 (黑/白/红三色)
```

---

## 3. 编译参数配置说明

### 3.1 PlatformIO 编译命令

```bash
# 进入固件目录
cd /Users/tangshan/Downloads/inksight-main/firmware

# 编译 (ProMini USB CDC 版本)
pio run -e epd_42_gdey042z98_3c_c3_promini

# 编译 (标准 UART 版本)
pio run -e epd_42_gdey042z98_3c_c3_std

# 编译并烧录
pio run -e epd_42_gdey042z98_3c_c3_promini -t upload

# 编译并烧录 + 打开串口监视器
pio run -e epd_42_gdey042z98_3c_c3_promini -t upload -t monitor

# 仅清理编译产物
pio run -e epd_42_gdey042z98_3c_c3_promini -t clean
```

### 3.2 Trae IDE 图形化编译

1. 打开 `firmware/` 目录 (File → Open Folder → 选择 `firmware/`)
2. 点击底部状态栏的 **环境选择器** (齿轮图标旁的环境名)
3. 选择 `epd_42_gdey042z98_3c_c3_promini`
4. 点击 **✓ Build** 编译
5. 连接硬件后点击 **→ Upload** 烧录
6. 点击 **🔌 Serial Monitor** 查看串口日志

### 3.3 编译参数详解

| 参数 | 值 | 说明 |
|---|---|---|
| `platform` | `espressif32` | ESP32 开发平台 (自动选择最新稳定版) |
| `framework` | `arduino` | Arduino 框架 |
| `board` | `esp32-c3-devkitm-1` | ESP32-C3 开发板 |
| `board_build.partitions` | `min_spiffs.csv` | 最小 SPIFFS 分区表 (更多应用 Flash 空间) |
| `board_build.filesystem` | `littlefs` | 使用 LittleFS 文件系统 |
| `monitor_speed` | `115200` | 串口监视器波特率 |
| `upload_speed` | `460800` | 烧录速度 (仅 std 环境) |
| `board_build.flash_mode` | `dio` | Flash 访问模式 (仅 std 环境) |
| `board_build.f_flash` | `40000000L` | Flash 频率 40MHz (仅 std 环境) |

### 3.4 GxEPD2 SPI 速率

默认 `EPD_GXEPD2_SPI_HZ = 4000000` (4MHz)。GDEY042Z98 支持最高 20MHz，可通过编译宏调高：

```ini
build_flags =
    ...
    -DEPD_GXEPD2_SPI_HZ=10000000  # 提高到 10MHz，可加快图像传输
```

建议先使用默认 4MHz 确保稳定，验证通过后再逐步提高。

---

## 4. 烧录工具选择与操作步骤

### 4.1 方法一：PlatformIO 一键烧录 (推荐)

**前提条件**:
- ESP32-C3 开发板通过 USB 线连接到 Mac
- 串口驱动已安装 (见 1.4 节)
- 编译环境已选择 `epd_42_gdey042z98_3c_c3_promini`

**操作步骤**:

1. USB 线连接开发板到 Mac
2. 确认串口识别：

```bash
ls /dev/cu.usb* /dev/cu.wch* 2>/dev/null
# 预期输出示例: /dev/cu.usbmodem1401
```

3. 在 Trae IDE 中点击 **→ Upload** 按钮，或执行：

```bash
cd /Users/tangshan/Downloads/inksight-main/firmware
pio run -e epd_42_gdey042z98_3c_c3_promini -t upload
```

4. 烧录过程输出示例：

```
Looking for upload port...
Auto-detected: /dev/cu.usbmodem1401
Uploading .pio/build/epd_42_gdey042z98_3c_c3_promini/firmware.bin
esptool.py v4.7.0
Serial port /dev/cu.usbmodem1401
Connecting....
Chip is ESP32-C3 (revision v0.4)
Writing at 0x00078000... (100%)
Wrote 393216 bytes (253487 compressed) at 0x00010000 in 4.5 seconds
Hash of data verified.
Leaving...
Hard resetting via RTS pin...
```

5. 烧录成功后，打开串口监视器验证：

```bash
pio device monitor -b 115200
```

### 4.2 方法二：esptool 手动烧录

当 PlatformIO Upload 失败时使用此方法。

**安装 esptool**:

```bash
pip3 install esptool
```

**操作步骤**:

```bash
# 1. 查找固件文件
FIRMWARE=".pio/build/epd_42_gdey042z98_3c_c3_promini/firmware.bin"
PORT="/dev/cu.usbmodem1401"  # 替换为实际串口

# 2. 擦除芯片 (首次烧录或更换面板时执行)
esptool.py --chip esp32c3 --port $PORT erase_flash

# 3. 烧录固件
esptool.py --chip esp32c3 --port $PORT \
  -b 460800 \
  --before default_reset \
  --after hard_reset \
  write_flash 0x0 $FIRMWARE
```

### 4.3 方法三：合并固件 OTA 烧录

PlatformIO 配置了 `post:merge_firmware.py` 脚本，编译后自动生成合并固件（含 bootloader + partition table + application），适用于 OTA 分发。

合并固件位置：
```
.pio/build/epd_42_gdey042z98_3c_c3_promini/firmware-merged.bin
```

烧录命令：
```bash
esptool.py --chip esp32c3 --port $PORT \
  -b 460800 write_flash 0x0 firmware-merged.bin
```

### 4.4 首次烧录后验证清单

烧录成功后，按开发板 RST 键重启，通过串口监视器观察：

| 检查项 | 预期输出 | 说明 |
|---|---|---|
| 固件版本 | `[INKSIGHT] Firmware v1.2.0` | 确认固件已更新 |
| 板型识别 | `[INKSIGHT] Board: ESP32-C3` | 确认板型正确 |
| 面板识别 | `[INKSIGHT] Panel: GDEY042Z98 400x300 3C` | 确认新面板被识别 |
| EPD 初始化 | `[EPD] GDEY042Z98 detected` | 驱动初始化成功 |
| WiFi 连接 | `[WIFI] Connecting to XXX...` | 进入配网流程 |
| 墨水屏刷新 | 屏幕显示 InkSight 默认界面 | 视觉确认 |

---

## 5. 常见问题排查与解决方案

### 5.1 编译阶段

| 问题 | 原因 | 解决方案 |
|---|---|---|
| `GxEPD2_420c_GDEY042Z98.h: No such file` | GxEPD2 版本过旧，不包含 GDEY042Z98 驱动 | 确认 `lib_deps` 中 `GxEPD2@^1.5.0`，执行 `pio pkg update -e epd_42_gdey042z98_3c_c3_promini` |
| `'GxEPD2_3C' does not name a type` | 未包含 `GxEPD2_3C.h` 头文件 | 检查 `#include <GxEPD2_3C.h>` 是否在 `EPD_PANEL_42_GDEY042Z98` 条件块内 |
| `undefined reference to epdDisplay2bpp` | GxEPD2 分支未定义此函数 | 按本方案 2.3 节添加函数定义 |
| `EPD_PANEL_42_GDEY042Z98` 未定义 | 编译环境选择错误 | 确认选择了 `epd_42_gdey042z98_3c_c3_promini` 环境 |
| 内存不足 | ESP32-C3 SRAM 有限 | 检查 `malloc` 返回值，使用 PSRAM 或减小缓冲区 |
| `python3: command not found` | Python 未安装 | `brew install python3` 或安装 Xcode Command Line Tools |

### 5.2 烧录阶段

| 问题 | 原因 | 解决方案 |
|---|---|---|
| 找不到串口设备 | USB 驱动未安装或 USB 线仅供电 | 安装 CH340/CP2102 驱动；换用支持数据传输的 USB 线 |
| `A fatal error occurred: Failed to connect to ESP32` | 开发板未进入下载模式 | 按住 BOOT 键 → 按 RST 键 → 松开 BOOT 键 |
| 烧录超时 | 串口被其他程序占用 | 关闭串口监视器、Arduino IDE 等程序后重试 |
| `Permission denied: /dev/cu.usbmodemXXX` | 串口设备权限不足 | `sudo chmod 666 /dev/cu.usbmodemXXX` |
| 烧录成功但无输出 | USB CDC 模式配置不匹配 | 尝试切换 promini/std 环境；检查 `ARDUINO_USB_CDC_ON_BOOT` 宏 |

### 5.3 运行阶段

| 问题 | 原因 | 解决方案 |
|---|---|---|
| 屏幕全白/全黑，无内容 | EPD 初始化失败或图像数据为空 | 检查串口日志 `[EPD]` 开头的输出；确认 BUSY 引脚连接正常 |
| 颜色显示不正确 | 2bpp 颜色映射逻辑有误 | 检查 `epdDisplay2bpp()` 中 switch-case 分支 |
| 红色偏淡或有残影 | 三色屏红色刷新需要更长时间 | 使用全刷新 (`refresh(false)`) 而非快速刷新 |
| 局部刷新后花屏 | 旧数据未正确传递 | 检查 `epdPartialDisplayWithOld()` 的 `oldData` 参数 |
| 快速刷新闪烁严重 | GDEY042Z98 三色屏快速刷新效果受限 | 调整 `FULL_REFRESH_INTERVAL` 减小 (如改为 5) |
| WiFi 连接失败 | 未配置 WiFi 凭证 | 长按配置按钮 (2秒) 进入 Captive Portal 配网 |
| 后端图像获取失败 | 服务器地址未配置或后端未启动 | 通过 Captive Portal 设置服务器地址；启动后端服务 |
| 黄色显示为红色 | GDEY042Z98 是三色屏 (黑/白/红)，无黄色粒子 | 这是物理限制，无法通过软件解决 |
| 休眠后无法唤醒 | `hibernate()` 后 EPD 需重新初始化 | `epdSleep()` 已置 `_initialized = false`，下次显示会自动 `epdInit()` |
| 内存溢出重启 | `malloc` 黑/红缓冲区后内存不足 | ESP32-C3 有 400KB SRAM，30KB×2=60KB 缓冲区应足够；检查是否有其他大内存分配 |

### 5.4 串口调试命令

在串口监视器中可观察的关键日志标签：

```
[INKSIGHT]  — 系统启动/配置
[EPD]       — EPD 驱动操作
[WIFI]      — WiFi 连接状态
[NET]       — 网络请求
[OTA]       — 固件更新
[HEAP]      — 内存使用
```

开启详细调试：在 `config.h` 中设置 `#define DEBUG_MODE 1`，刷新间隔将缩短为 1 分钟。

---

## 6. 附录

### 6.1 硬件接线图

```
ESP32-C3          GDEY042Z98 模块
─────────         ──────────────
GPIO 6 (MOSI) ──→ DIN  (SPI 数据)
GPIO 4 (SCK)  ──→ CLK  (SPI 时钟)
GPIO 7 (CS)   ──→ CS   (片选, 低有效)
GPIO 1 (DC)   ──→ DC   (数据/命令)
GPIO 2 (RST)  ──→ RST  (复位, 低有效)
GPIO 10(BUSY) ←── BUSY (忙信号)
3.3V          ──→ VCC
GND           ──→ GND
```

### 6.2 支持的面板完整列表 (改造后)

| 编译环境宏 | 面板型号 | 尺寸 | 分辨率 | 色彩 | SPI 方式 |
|---|---|---|---|---|---|
| `EPD_PANEL_42_SSD1683_BW` | 微雪 v2 SSD1683 | 4.2" | 400x300 | BW | 软件 bit-bang |
| `EPD_PANEL_42_GXEPD2_GYE042A87` | 中景园 GYE042A87 | 4.2" | 400x300 | BW | GxEPD2 硬件 |
| `EPD_PANEL_42_GDEM042F52` | 大连佳显 GDEM042F52 | 4.2" | 400x300 | BWRY | 软件 bit-bang |
| `EPD_PANEL_42_DKE_RY683` | 广义顺 RY683 | 4.2" | 400x300 | BWRY | 软件 bit-bang |
| `EPD_PANEL_42_WFT` | Waveshare WFT0420CZ15 | 4.2" | 400x300 | BW/BWR | 软件 SPI |
| `EPD_PANEL_42_GXEPD2_T81` | GDEY042T81 | 4.2" | 400x300 | BW | GxEPD2 硬件 |
| **`EPD_PANEL_42_GDEY042Z98`** | **GDEY042Z98 (本次新增)** | **4.2"** | **400x300** | **BWR** | **GxEPD2 硬件** |
| `EPD_PANEL_29` | GDEY029T94 | 2.9" | 296x128 | BW | GxEPD2 硬件 |
| `EPD_PANEL_583` / `EPD_PANEL_583_UC8179` | GDEQ0583T31 | 5.83" | 648x480 | BW | GxEPD2 硬件 |
| `EPD_PANEL_75` | GxEPD2_750_T7 | 7.5" | 800x480 | BW | GxEPD2 硬件 |

### 6.3 关键代码路径索引

| 功能 | 文件 | 关键函数/变量 |
|---|---|---|
| 引脚配置 | `firmware/src/config.h` | `PIN_EPD_*` 宏定义 |
| 帧缓冲区分配 | `firmware/src/main.cpp` | `imgBuf[]`, `colorBuf[]`, `useColorBuf` |
| 智能刷新调度 | `firmware/src/display.cpp` | `smartDisplay()` |
| EPD 底层驱动 | `firmware/src/epd_driver.cpp` | `epdInit()`, `epdDisplay()`, `epdDisplay2bpp()` |
| 图像获取 | `firmware/src/network.cpp` | `fetchBMP()` |
| 后端渲染管道 | `backend/core/pipeline.py` | `generate_and_render()` |
| 后端三色渲染 | `backend/core/json_renderer.py` | 4 色调色板配置 |
| WebApp 预览 | `webapp/components/config/eink-preview-panel.tsx` | 墨水屏预览面板 |

### 6.4 测试验证指标

| 指标 | 目标值 | 测量方法 |
|---|---|---|
| 编译零错误 | 0 error, 0 warning | `pio run` 输出 |
| 全刷新耗时 | ≤4s | 串口计时 |
| 快速刷新耗时 | ≤2s | 串口计时 |
| 局部刷新耗时 | ≤1s | 串口计时 |
| 休眠电流 | ≤10μA | 万用表串联 |
| 三色显示正确 | 黑/白/红准确 | 目视对比 |
| 2bpp 数据完整性 | 颜色映射无错 | 对比后端渲染图 |
| 残影消除 | 10 次全刷新后无可见残影 | 连续 50 次刷新测试 |
| WiFi 配网 | Captive Portal 正常 | 手机/电脑连接测试 |
| OTA 更新 | 固件更新成功 | WebApp 触发 |
