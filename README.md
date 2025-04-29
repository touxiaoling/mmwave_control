# mmwave_control

This is an active millimeter-wave scanning framework code, which is still under development.

# project install
## linux or macos

```bash
#install uv for package manage
curl -LsSf https://astral.sh/uv/install.sh | sh
# sync package
uv sync 
```
## windows
```bash
#install uv use win-get
winget install --id=astral-sh.uv  -e
uv sync
```
# run
1. `start_frame.ipynb`文件是用于扫描物体生成原始数据的
2. `rma.ipynb` 一个简单的rma算法，用于从原始数据计算出平面图像
3. `phase_correct.ipynb` 是用于纠正毫米波雷达不同通道的相位差

# References and dependencies:

•	https://github.com/azinke/mmwave  
•	https://github.com/azinke/mmwave-repack

# tips
## 更换清华源
```bash
pip config set global.index-url https://mirrors.tuna.tsinghua.edu.cn/pypi/web/simple
```

## win下挂载ext4磁盘
### 通过wsl2
#！注意： 需要安装好wsl2，再通过这个方法挂载

首先进入powershell管理员
```shell
wmic diskdrive list brief #显示所有磁盘
wsl --mount \\.\PHYSICALDRIVE2 #注意 \\.\PHYSICALDRIVE2 应替换成实际对应磁盘的路径
```

然后进入wsl2
```shell
sudo fdisk -l #显示所有磁盘
sudo mount /dev/sdg1 /mnt/mmw #注意设备应该替换成实际设备
rsync -avP /mnt/mmw/need_dir /to_dir #拷贝文件
sudo umount /mnt/mmw #wsl2下取消挂载
```
然后再回到powershell管理员

```shell
wsl --unmount \\.\PHYSICALDRIVE2 #取消挂载磁盘
```

# fmc4030 control issue

1. `FMC4030_Get_Axis_Current_Pos`函数第一次调用会返回正确位置，然后接下来调用任何函数都会卡死（如FMC4030_Jog_Single_Axis），返回错误码-6。作为对比 `FMC4030_Get_Axis_Current_Speed`函数没有发现同样的问题。
2. `FMC4030_Get_Machine_Status`函数调用后返回代码664，该代码不在说明书的返回值列表里，但返回的状态信息正常。
3. 两个任意函数调用时间间隔小于1ms时，第二次函数调用大概率不会响应。

