# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

毫米波雷达（mmWave）SAR 扫描控制框架，用于控制 TI 4-chip cascade EVM 雷达和 FMC4030 三轴运动控制器，实现自动化合成孔径雷达扫描成像。

## Commands

```bash
# 安装依赖
uv sync

# 运行脚本
uv run main.py

# CLI 工具：将原始雷达二进制数据重组为 numpy 数组
uv run repack <data_dir>

# CLI 工具：运行 RMA 成像算法
uv run rma <data_dir>

# 代码格式化（由 pre-commit 自动运行）
uv run ruff format .

# 代码检查
uv run ruff check .

# 清理 Jupyter notebook 输出
bash clear_ipynb.sh
```

## Architecture

### 层级结构

```
mmwave/                     核心包
├── schemas.py              Pydantic 数据模型（MMWConfig、BracketConfig 等）
├── config.py               三套预设雷达配置（default/short_range/very_short_range）
├── mmwave.py               雷达控制（MMWaveCmd 通过 SSH/CLI，MMWave 通过 mmwcas C扩展）
├── repack.py               原始二进制数据解析和重组（6D numpy 数组）
├── rma.py                  Range Migration Algorithm 成像算法
├── util.py                 配置加载、帧缓存、子进程工具
└── fmc4030/                FMC4030 三轴运动控制器子包
    ├── fmc4030lib.py       ctypes 底层绑定（加载原生 .so/.dll）
    ├── fmc4030.py          高级控制类（含参数验证和 min_delay）
    ├── bracket.py          Braket 扫描支架控制（X: 0-970mm，Y: 0-1970mm）
    └── util.py             min_delay 装饰器（确保调用间隔 >= 1ms）
```

### 关键数据流

1. **配置**：`config.py` 预设 → `schemas.MMWConfig` 验证 → TOML 文件存储
2. **采集**：Jupyter notebooks 控制扫描流程，`MMWaveCmd`/`MMWave` 控制雷达，`Braket` 控制运动
3. **数据**：原始 `.bin` + `.idx.bin` 文件 → `repack.py` 解析 → `(16_rx, 12_tx, rows, cols, adc_samples, 2_IQ)` 数组
4. **成像**：帧数据 → `rma.py` RMA 算法 → 聚焦图像

### mmwcas C 扩展

`mmwcas` 是外部 C 扩展模块（未包含在仓库中），通过 try/except 可选导入。类型存根见 `mmwave/mmwcas.pyi`。雷达 IP 地址默认为 `192.168.33.180`。

### FMC4030 平台兼容性

- Linux/Windows：加载原生 `.so`/`.dll`（位于 `mmwave/fmc4030/lib/`）
- macOS：使用 `MacTestLib` 模拟对象（所有调用为空操作），仅用于开发调试

### 已知硬件限制

FMC4030 控制器两次函数调用间隔小于 1ms 时第二次调用大概率无响应，通过 `fmc4030/util.py` 的 `@min_delay()` 装饰器全局缓解。
