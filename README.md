# mmwave_control

毫米波雷达（mmWave）SAR 扫描控制框架，用于联动 TI 4-chip cascade EVM 雷达与 FMC4030 三轴运动控制器，实现自动化采集与成像流程。

> 项目仍在持续迭代中。

## 功能概览

- 雷达采集控制：支持通过 `MMWaveCmd` / `MMWave` 启停与采集。
- 运动控制：封装 FMC4030 控制接口，支持扫描路径执行。
- 数据重组：将原始雷达二进制数据重组为 numpy 数组。
- 成像处理：提供 RMA（Range Migration Algorithm）成像流程。

## 环境要求

- Python `3.13.x`（项目当前固定）
- 推荐使用 `uv` 进行依赖管理

## 安装

### Linux / macOS

```bash
# 安装 uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# 安装依赖
uv sync
```

### Windows

```powershell
# 安装 uv
winget install --id=astral-sh.uv -e

# 安装依赖
uv sync
```

## 快速开始

### 1) 采集与预处理（Notebook）

- `start_frame.ipynb`：基础扫描采集流程。
- `start_frame2.ipynb`：扩展版本采集流程。
- `start_frame_handshake.ipynb`：包含抖动扫描相关流程的采集版本。
- `phase_correct.ipynb`：通道相位校正。
- `rma.ipynb`：基于采集数据进行 RMA 成像演示。

### 2) 命令行工具

```bash
# 运行主程序（若使用）
uv run main.py

# 将原始数据重组为 numpy 数组
uv run repack <data_dir>

# 对数据执行 RMA 成像
uv run rma <data_dir>
```

## 项目结构

```text
mmwave/
├── config.py               预设雷达配置
├── schemas.py              Pydantic 配置模型
├── mmwave.py               雷达控制核心
├── repack.py               原始数据重组
├── rma.py                  RMA 成像算法
├── util.py                 通用工具
└── fmc4030/
    ├── fmc4030lib.py       ctypes 底层绑定
    ├── fmc4030.py          高级控制接口
    ├── bracket.py          扫描支架控制
    └── util.py             调用间隔控制（min_delay）
```

## 平台说明

- Linux / Windows：使用 `mmwave/fmc4030/lib/` 下的原生动态库。
- macOS：使用 `MacTestLib` 模拟对象（仅用于本地开发调试，不控制真实硬件）。

## 常见问题（FMC4030）

1. `FMC4030_Get_Axis_Current_Pos` 首次调用正常，后续调用其他函数可能卡死并返回 `-6`；`FMC4030_Get_Axis_Current_Speed` 暂未观察到同类问题。
2. `FMC4030_Get_Machine_Status` 返回过 `664`，该返回码不在说明书列表中，但状态结构体内容可用。
3. 任意两次函数调用间隔小于 `1ms` 时，第二次调用大概率无响应。项目通过 `@min_delay()` 装饰器做了全局缓解。

## 实用命令

```bash
# 代码格式化
uv run ruff format .

# 代码检查
uv run ruff check .

# 清理 notebook 输出
bash clear_ipynb.sh
```

## 参考项目

- https://github.com/azinke/mmwave
- https://github.com/azinke/mmwave-repack
