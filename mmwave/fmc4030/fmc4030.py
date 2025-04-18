import time
import atexit
from ctypes import c_float, c_int, byref, create_string_buffer
from threading import Lock

from pydantic import validate_call, BaseModel

from . import fmc4030lib as flib
from . import util


class AxisStaus(BaseModel):
    power_on: bool
    running: bool
    pause: bool
    resume: bool
    stop: bool
    limit_n: bool
    limit_p: bool
    home_done: bool
    home: bool
    auto_run: bool
    limit_n_none: bool
    limit_p_none: bool
    home_none: bool
    home_overtime: bool

    @classmethod
    def from_ctypes(cls, cins: int):
        return cls(
            power_on=bool(cins & 0x0000),
            running=bool(cins & 0x0001),
            pause=bool(cins & 0x0002),
            resume=bool(cins & 0x0004),
            stop=bool(cins & 0x0008),
            limit_n=bool(cins & 0x0010),
            limit_p=bool(cins & 0x0020),
            home_done=bool(cins & 0x0040),
            home=bool(cins & 0x0080),
            auto_run=bool(cins & 0x0100),
            limit_n_none=bool(cins & 0x0200),
            limit_p_none=bool(cins & 0x0400),
            home_none=bool(cins & 0x0800),
            home_overtime=bool(cins & 0x1000),
        )


class MachineStatus(BaseModel):
    real_pos: tuple[float, float, float]
    real_speed: tuple[float, float, float]
    input_status: int
    output_status: int
    limit_n_status: int
    limit_p_status: int
    machine_run_status: str
    axis_status: tuple[AxisStaus, AxisStaus, AxisStaus]
    home_status: int
    file: str

    @classmethod
    def from_ctypes(cls, cins: flib.MachineStatus):
        match cins.machineRunStatus:
            case flib.MACHINE_MANUAL:
                machine_run_status = "MANUAL"
            case flib.MACHINE_AUTO:
                machine_run_status = "AUTO"
            case _:
                machine_run_status = "UNKNOWN"

        axis_status = tuple(AxisStaus.from_ctypes(i) for i in cins.axisStatus)

        return cls(
            real_pos=cins.realPos,
            real_speed=cins.realSpeed,
            input_status=cins.inputStatus,
            output_status=cins.outputStatus,
            limit_n_status=cins.limitNStatus,
            limit_p_status=cins.limitPStatus,
            machine_run_status=machine_run_status,
            axis_status=axis_status,
            home_status=cins.homeStatus,
            file=cins.file.decode("utf-8"),
        )


class DevicePara(BaseModel):
    id: int
    bound232: int
    bound485: int
    ip: str
    port: int
    div: tuple[int, int, int]
    lead: tuple[int, int, int]
    soft_limit_max: tuple[int, int, int]
    soft_limit_min: tuple[int, int, int]
    home_time: tuple[int, int, int]

    @classmethod
    def from_ctypes(cls, cins: flib.DevicePara):
        return cls(
            id=cins.id,
            bound232=cins.bound232,
            bound485=cins.bound485,
            ip=cins.ip.decode("utf-8"),
            port=cins.port,
            div=cins.div,
            lead=cins.lead,
            soft_limit_max=cins.softLimitMax,
            soft_limit_min=cins.softLimitMin,
            home_time=cins.homeTime,
        )

    def to_ctypes(self) -> flib.DevicePara:
        return flib.DevicePara(
            id=self.id,
            bound232=self.bound232,
            bound485=self.bound485,
            ip=self.ip.encode("utf-8"),
            port=self.port,
            div=self.div,
            lead=self.lead,
            softLimitMax=self.soft_limit_max,
            softLimitMin=self.soft_limit_min,
            homeTime=self.home_time,
        )


class MachineVersion(BaseModel):
    firmware: int
    lib: int
    serial_number: int

    @classmethod
    def from_ctypes(cls, cins: flib.MachineVersion):
        return cls(
            firmware=cins.firmware,
            lib=cins.lib,
            serial_number=cins.serialNumber,
        )


class FMC4030:
    def __init__(
        self,
        ip: str = "192.168.0.30",
        port=8088,
        id=0,
    ):
        self.ip = ip
        self.port = port
        self.id = id

        self.connected = False

        self._next_time = 0
        self._next_time_lock = Lock()

        self._dp = flib.DevicePara()
        self._ms = flib.MachineStatus()
        self._mv = flib.MachineVersion()
        self._pos = flib.c_float(0)
        self._speed = flib.c_float(0)

    def open_device(self):
        ip = self.ip.encode("utf-8")
        flib.open_device(self.id, ip, self.port)
        atexit.register(self.close_device)
        self.connected = True

    @util.min_delay()
    def close_device(self) -> bool:
        if self.connected:
            flib.close_device(self.id)
            self.connected = False

    def __enter__(self):
        if not self.connected:
            self.open_device()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.connected:
            self.close_device()
        else:
            raise ValueError("device already closed")

    @util.min_delay()
    def _jog_single_axis(self, axis: int, pos: float, speed: float, acc: float, dec: float, mode: int):
        flib.jog_single_axis(self.id, axis, pos, speed, acc, dec, mode)

    @validate_call
    def jog_single_axis_relative(self, axis: int, pos: float, speed: float, acc: float, dec: float):
        """执行控制器单轴相对运动，可多次启动不同轴，启动同一轴时若前次运动未完成，则此次指令不响应
        pos:运行的距离，区别正负，单位 mm
        speed:运行的速度，只能为正数，单位 mm/s
        acc:运行的加速度，只能为正数，单位 mm/s²
        dec:运行的减速度，只能为正数，单位 mm/s²
        """
        self._jog_single_axis(axis, pos, speed, acc, dec, flib.RELATIVE_MOTION)

    @validate_call
    def jog_single_axis_absolute(self, axis: int, pos: float, speed: float, acc: float, dec: float):
        """执行控制器单轴绝对运动，可多次启动不同轴，启动同一轴时若前次运动未完成，则此次指令不响应
        pos:运行的距离，区别正负，单位 mm
        speed:运行的速度，只能为正数，单位 mm/s
        acc:运行的加速度，只能为正数，单位 mm/s²
        dec:运行的减速度，只能为正数，单位 mm/s²
        """
        self._jog_single_axis(axis, pos, speed, acc, dec, flib.ABSOLUTE_MOTION)

    @validate_call
    @util.min_delay()
    def check_axis_is_stop(self, axis: int):
        """检查某轴是否为停止状态，用于判断某轴的运行状态
        返回值：ture 为停止状态
        """
        res = flib.check_axis_is_stop(self.id, axis)
        if res != 0 and res != 1:
            raise ValueError(f"axis stop check error,return code {res}")
        return bool(res)

    @validate_call
    def wait_axis_stop(self, axis: int, wait_time=0.01):
        while not self.check_axis_is_stop(axis):
            time.sleep(wait_time)

    @validate_call
    @util.min_delay()
    def home_single_axis(self, axis: int, speed: float, acc_dec: float, fall_step: float, dir: int) -> bool:
        """
        Speed:回零速度，正数，单位 mm/s
        AccDec:回零加减速度，正数，单位 mm/s²
        FallStep:回零脱落距离，正数，单位 mm。此参数为回零完成后远离限位开关的距离。
        eDir:回零方向，1：正限位回零，2：负限位回零
        """
        flib.home_single_axis(self.id, axis, speed, acc_dec, fall_step, dir)
        time.sleep(0.005)

    @validate_call
    @util.min_delay()
    def stop_single_axis(self, axis: int, force=False):
        """停止某轴运行，此函只能用于启动单轴运行后停止，不能用于插补运动时的停止
        force：立即停止
        """
        mode = 2 if force else 1
        flib.stop_single_axis(self.id, axis, mode)

    @validate_call
    @util.min_delay()
    def get_axis_current_pos(self, axis: int):
        """获取某轴当前实际位置，此位置为控制卡内部计数产生，若电机发生堵转或卡滞，则此位置不准确"""
        pos = self._pos
        flib.get_axis_current_pos(self.id, axis, byref(pos))
        return pos.value

    @validate_call
    @util.min_delay()
    def get_axis_current_speed(self, axis: int):
        """获取某轴当前运行速度"""
        speed = self._speed
        flib.get_axis_current_speed(self.id, axis, byref(speed))
        return speed.value

    @validate_call
    @util.min_delay()
    def set_output(self, io: int, status: int):
        """设置控制器输出口状态，此输出口为开漏输出，可接大功率继电器等设备。
        io：0、1、2、3 分别对应 OUT0、OUT1、OUT2、OUT3
        status：设置给输出口的状态，0：输出高电平，1：输出低电平
        """
        flib.set_output(self.id, io, status)

    @validate_call
    @util.min_delay()
    def get_input(self, io: int):
        """获取输入口状态
        id：分配给控制器的 id 号
        io：0、1、2、3 分别对应 IN0、IN1、IN2、IN3
        """
        status = c_int(0)
        flib.get_input(self.id, io, byref(status))
        return status.value

    @validate_call
    @util.min_delay()
    def write_data_to_485(self, data: str):
        data = data.encode("utf-8")
        length = len(data)
        flib.write_data_to_485(self.id, data, length)

    @validate_call
    @util.min_delay()
    def read_data_from_485(self):
        data = create_string_buffer(100)
        length = c_int(0)
        flib.read_data_from_485(self.id, data, length)
        return data.value.decode("utf-8")

    # @validate_call
    # def set_fsc_speed(self, slave_id: int, speed: int):
    #     flib.set_fsc_speed(self.id, slave_id, speed)

    @validate_call
    @util.min_delay()
    def line_2axis(self, axis: int, end_x: int, end_y: int, speed: float, acc: float, dec: float):
        """以当前点为起点的两轴直线插补，当前点由控制器内部计数进行控制
        axis：待控制的两个轴，由于本控制器具有三个轴，因此采用 32 位无符号数的低三位来表示选中的轴，0x03 表示 X、Y 轴，0x05 表示 X、Z 轴，0x06 表示 Y、Z 轴
        endX：直线插补终点的 X 坐标，此 X 非实际的 X 轴，为虚拟坐标系的 X，单位 mm
        endY：直线插补终点的 Y 坐标，此 Y 非实际的 Y 轴，为虚拟坐标系的Y，单位 mm
        speed：两轴直线插补合成速度，不代表各轴实际速度。单位 mm/s
        acc：两轴直线插补合成加速度，不是各轴实际加速度，单位 mm/s²
        dec：两轴直线插补合成减速度，不是各轴实际减速度，单位 mm/s²
        """
        flib.line_2axis(self.id, axis, end_x, end_y, speed, acc, dec)

    @validate_call
    @util.min_delay()
    def line_3axis(self, axis: int, end_x: float, end_y: float, end_z: float, speed: float, acc: float, dec: float):
        flib.line_3axis(self.id, axis, end_x, end_y, end_z, speed, acc, dec)

    @validate_call
    @util.min_delay()
    def arc_2axis(
        self,
        axis: int,
        end_x: float,
        end_y: float,
        center_x: float,
        center_y: float,
        radius: float,
        speed: float,
        acc: float,
        dec: float,
        dir: float,
    ):
        flib.arc_2axis(self.id, axis, end_x, end_y, center_x, center_y, radius, speed, acc, dec, dir)

    @validate_call
    @util.min_delay()
    def pause_run(self, axis: int):
        """暂停插补运动，包括直线插补与圆弧插补"""
        flib.pause_run(self.id, axis)

    @validate_call
    @util.min_delay()
    def resume_run(self, axis: int):
        """继续插补运动，包括直线插补与圆弧插补"""
        flib.resume_run(self.id, axis)

    @util.min_delay()
    def stop_run(self):
        """停止插补运动，包括直线插补与圆弧插补"""
        flib.stop_run(self.id)

    @util.min_delay()
    def get_machine_status(self):
        """取设备状态及运行参数，参数包含三轴位置，三轴速度，回零状态，输入状态，设备序列号等等"""
        ms = self._ms
        flib.get_machine_status(self.id, byref(ms))
        return MachineStatus.from_ctypes(ms)

    @util.min_delay()
    def get_device_para(self):
        """取设备设置参数及各轴设置参数，包含 ip，端口号，导程、细分等参数"""
        dp = self._dp
        flib.get_device_para(self.id, byref(dp))
        return DevicePara.from_ctypes(dp)

    @validate_call
    @util.min_delay()
    def set_device_para(self, para: DevicePara):
        """设置设备参数及各轴参数，请勿随意修改，避免造成设备运行错误致设备损坏"""
        para = para.to_ctypes()
        flib.set_device_para(self.id, byref(para))

    @validate_call
    @util.min_delay()
    def get_version_info(self):
        """获取设备版本信息，包含固件版本，库版本，序列号"""
        mv = self._mv
        flib.get_version_info(self.id, byref(mv))
        return MachineVersion.from_ctypes(mv)
