import atexit
from ctypes import c_float, c_int, byref, create_string_buffer

from pydantic import validate_call, BaseModel

from . import fmc4030lib as flib
from . import util


class MachineStatus(BaseModel):
    real_pos: tuple[float, float, float]
    real_speed: tuple[float, float, float]
    input_status: int
    output_status: int
    limit_n_status: int
    limit_p_status: int
    machine_run_status: int
    axis_status: tuple[int, int, int]
    home_status: int
    file: str


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


class MachineVersion(BaseModel):
    firmware: int
    lib: int
    serial_number: int


def machine_status_turn(cins: flib.MachineStatus):
    return MachineStatus(
        real_pos=cins.realPos,
        real_speed=cins.realSpeed,
        input_status=cins.inputStatus,
        output_status=cins.outputStatus,
        limit_n_status=cins.limitNStatus,
        limit_p_status=cins.limitPStatus,
        machine_run_status=cins.machineRunStatus,
        axis_status=cins.axisStatus,
        home_status=cins.homeStatus,
        file=cins.file.decode("utf-8"),
    )


def device_para_turn(cins: flib.DevicePara):
    return DevicePara(
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


def device_para_return(pins: DevicePara):
    return flib.DevicePara(
        id=pins.id,
        bound232=pins.bound232,
        bound485=pins.bound485,
        ip=pins.ip.encode("utf-8"),
        port=pins.port,
        div=pins.div,
        lead=pins.lead,
        softLimitMax=pins.soft_limit_max,
        softLimitMin=pins.soft_limit_min,
        homeTime=pins.home_time,
    )


def machine_version_turn(cins: flib.MachineVersion):
    return MachineVersion(
        firmware=cins.firmware,
        lib=cins.lib,
        serial_number=cins.serialNumber,
    )


delay_decorator = util.DelayDecorator(0.001)


class FMC4030:
    def __init__(
        self,
        ip: str = "192.168.0.30",
        port=8088,
        id=0,
        speed: float = 200,
        acc: float = 200,
        dec: float = None,
        home_speed: float = 50,
    ):
        self.ip = ip
        self.port = port
        self.id = id

        self.speed = speed
        self.acc = acc
        self.dec = dec or acc
        self.fall_step = 5
        self.home_speed = home_speed

    def open_device(self):
        ip = self.ip.encode("utf-8")
        flib.open_device(self.id, ip, self.port)
        atexit.register(self.close_device)

    @delay_decorator
    def close_device(self) -> bool:
        flib.close_device(self.id)

    @delay_decorator
    def _jog_single_axis(self, axis: int, pos: float, speed: float, acc: float, dec: float, mode: int):
        flib.jog_single_axis(self.id, axis, pos, speed, acc, dec, mode)

    @validate_call
    def jog_single_axis_relative(
        self,
        axis: int,
        pos: float,
        speed: float = None,
        acc: float = None,
        dec: float = None,
    ):
        """执行控制器单轴相对运动，可多次启动不同轴，启动同一轴时若前次运动未完成，则此次指令不响应
        pos:运行的距离，区别正负，单位 mm
        speed:运行的速度，只能为正数，单位 mm/s
        acc:运行的加速度，只能为正数，单位 mm/s²
        dec:运行的减速度，只能为正数，单位 mm/s²
        """
        speed = speed or self.speed
        dec = dec or acc or self.dec
        acc = acc or self.acc

        self._jog_single_axis(axis, pos, speed, acc, dec, flib.RELATIVE_MOTION)

    @validate_call
    def jog_single_axis_absolute(self, axis: int, pos: float, speed: float = None, acc: float = None, dec: float = None):
        """执行控制器单轴绝对运动，可多次启动不同轴，启动同一轴时若前次运动未完成，则此次指令不响应
        pos:运行的距离，区别正负，单位 mm
        speed:运行的速度，只能为正数，单位 mm/s
        acc:运行的加速度，只能为正数，单位 mm/s²
        dec:运行的减速度，只能为正数，单位 mm/s²
        """
        speed = speed or self.speed
        dec = dec or acc or self.dec
        acc = acc or self.acc

        self._jog_single_axis(axis, pos, speed, acc, dec, flib.ABSOLUTE_MOTION)

    @validate_call
    @delay_decorator
    def check_axis_is_stop(self, axis: int):
        """检查某轴是否为停止状态，用于判断某轴的运行状态
        返回值：ture 为停止状态
        """
        res = flib.check_axis_is_stop(self.id, axis)
        if res != 0 and res != 1:
            raise ValueError(f"axis stop check error,return code {res}")
        return bool(res)

    @validate_call
    def wait_axis_stop(self, axis: int):
        while not self.check_axis_is_stop(axis):
            pass

    @validate_call
    @delay_decorator
    def home_single_axis(
        self, axis: int, speed: float = None, acc_dec: float = None, fall_step: float = None, dir: int = 1
    ) -> bool:
        """
        Speed:回零速度，正数，单位 mm/s
        AccDec:回零加减速度，正数，单位 mm/s²
        FallStep:回零脱落距离，正数，单位 mm。此参数为回零完成后远离限位开关的距离。
        eDir:回零方向，1：正限位回零，2：负限位回零
        """
        speed = speed or self.home_speed
        acc_dec = acc_dec or self.acc
        fall_step = fall_step or self.fall_step
        flib.home_single_axis(self.id, axis, speed, acc_dec, fall_step, dir)

    @validate_call
    @delay_decorator
    def stop_single_axis(self, axis: int, force=False):
        """停止某轴运行，此函只能用于启动单轴运行后停止，不能用于插补运动时的停止
        force：立即停止
        """
        mode = 2 if force else 1
        flib.stop_single_axis(self.id, axis, mode)

    @validate_call
    @delay_decorator
    def get_axis_current_pos(self, axis: int):
        """获取某轴当前实际位置，此位置为控制卡内部计数产生，若电机发生堵转或卡滞，则此位置不准确"""
        pos = c_float(0)
        flib.get_axis_current_pos(self.id, axis, byref(pos))
        return pos.value

    @validate_call
    @delay_decorator
    def get_axis_current_speed(self, axis: int):
        """获取某轴当前运行速度"""
        speed = c_float(0)
        flib.get_axis_current_speed(self.id, axis, byref(speed))
        return speed.value

    @validate_call
    @delay_decorator
    def set_output(self, io: int, status: int):
        """设置控制器输出口状态，此输出口为开漏输出，可接大功率继电器等设备。
        io：0、1、2、3 分别对应 OUT0、OUT1、OUT2、OUT3
        status：设置给输出口的状态，0：输出高电平，1：输出低电平
        """
        flib.set_output(self.id, io, status)

    @validate_call
    @delay_decorator
    def get_input(self, io: int):
        """获取输入口状态
        id：分配给控制器的 id 号
        io：0、1、2、3 分别对应 IN0、IN1、IN2、IN3
        """
        status = c_int(0)
        flib.get_input(self.id, io, byref(status))
        return status.value

    @validate_call
    @delay_decorator
    def write_data_to_485(self, data: str):
        data = data.encode("utf-8")
        length = len(data)
        flib.write_data_to_485(self.id, data, length)

    @validate_call
    @delay_decorator
    def read_data_from_485(self):
        data = create_string_buffer(100)
        length = c_int(0)
        flib.read_data_from_485(self.id, data, length)
        return data.value.decode("utf-8")

    # @validate_call
    # def set_fsc_speed(self, slave_id: int, speed: int):
    #     flib.set_fsc_speed(self.id, slave_id, speed)

    @validate_call
    @delay_decorator
    def line_2axis(self, axis: int, end_x: int, end_y: int, speed: float = None, acc: float = None, dec: float = None):
        """以当前点为起点的两轴直线插补，当前点由控制器内部计数进行控制
        axis：待控制的两个轴，由于本控制器具有三个轴，因此采用 32 位无符号数的低三位来表示选中的轴，0x03 表示 X、Y 轴，0x05 表示 X、Z 轴，0x06 表示 Y、Z 轴
        endX：直线插补终点的 X 坐标，此 X 非实际的 X 轴，为虚拟坐标系的 X，单位 mm
        endY：直线插补终点的 Y 坐标，此 Y 非实际的 Y 轴，为虚拟坐标系的Y，单位 mm
        speed：两轴直线插补合成速度，不代表各轴实际速度。单位 mm/s
        acc：两轴直线插补合成加速度，不是各轴实际加速度，单位 mm/s²
        dec：两轴直线插补合成减速度，不是各轴实际减速度，单位 mm/s²
        """
        speed = speed or self.speed
        dec = dec or acc or self.dec
        acc = acc or self.acc
        flib.line_2axis(self.id, axis, end_x, end_y, speed, acc, dec)

    @validate_call
    @delay_decorator
    def line_3axis(self, axis: int, end_x: float, end_y: float, end_z: float, speed: float, acc: float, dec: float):
        flib.line_3axis(self.id, axis, end_x, end_y, end_z, speed, acc, dec)

    @validate_call
    @delay_decorator
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
        flib.arc_2axis(
            self.id,
            axis,
            end_x,
            end_y,
            center_x,
            center_y,
            radius,
            speed,
            acc,
            dec,
            dir,
        )

    @delay_decorator
    def stop_run(self):
        """停止插补运动，包括直线插补与圆弧插补"""
        flib.stop_run(self.id)

    @delay_decorator
    def get_machine_status(self):
        """取设备状态及运行参数，参数包含三轴位置，三轴速度，回零状态，输入状态，设备序列号等等"""
        ms = flib.MachineStatus()
        flib.get_machine_status(self.id, byref(ms))
        return machine_status_turn(ms)

    @delay_decorator
    def get_device_para(self):
        """取设备设置参数及各轴设置参数，包含 ip，端口号，导程、细分等参数"""
        dp = flib.DevicePara()
        flib.get_device_para(self.id, byref(dp))
        return device_para_turn(dp)

    @validate_call
    @delay_decorator
    def set_device_para(self, para: DevicePara):
        """设置设备参数及各轴参数，请勿随意修改，避免造成设备运行错误致设备损坏"""
        para = device_para_return(para)
        flib.set_device_para(self.id, byref(para))
