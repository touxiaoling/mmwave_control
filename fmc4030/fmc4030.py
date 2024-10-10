from ctypes import c_float, c_int, byref, create_string_buffer
from pydantic import validate_call, BaseModel
from . import fmc4030lib as flib


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


class FMC4030:
    def __init__(
        self,
        ip: str = "192.168.0.30",
        port=8088,
        id=0,
        speed: float = 200,
        acc: float = 200,
        dec: float = None,
    ):
        self.ip = ip
        self.port = port
        self.id = id

        self.speed = speed
        self.acc = acc
        self.dec = dec or acc

    def open_device(self):
        ip = self.ip.encode("utf-8")
        flib.open_device(self.id, ip, self.port)

    def close_device(self) -> bool:
        flib.close_device(self.id)

    @validate_call
    def jog_single_axis(
        self, axis: int, pos: float, speed: float, acc: float, dec: float, mode: int
    ):
        """
        pos:运行的距离，区别正负，单位 mm
        speed:运行的速度，只能为正数，单位 mm/s
        acc:运行的加速度，只能为正数，单位 mm/s²
        dec:运行的减速度，只能为正数，单位 mm/s²
        mode:运行模式。1：相对运动，2：绝对运动
        """
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
        speed = speed or self.speed
        acc = acc or self.acc
        dec = dec or self.dec

        self.jog_single_axis(axis, pos, speed, acc, dec, flib.RELATIVE_MOTION)

    @validate_call
    def jog_single_axis_absolute(
        self,
        axis: int,
        pos: float,
        speed: float = None,
        acc: float = None,
        dec: float = None,
    ):
        speed = speed or self.speed
        acc = acc or self.acc
        dec = dec or self.dec

        self.jog_single_axis(axis, pos, speed, acc, dec, flib.ABSOLUTE_MOTION)

    @validate_call
    def check_axis_is_stop(self, axis: int):
        flib.check_axis_is_stop(self.id, axis)

    @validate_call
    def home_single_axis(
        self, axis: int, speed: float, acc_dec: float, fall_step: float, dir: int
    ) -> bool:
        flib.home_single_axis(self.id, axis, speed, acc_dec, fall_step, dir)

    @validate_call
    def stop_single_axis(self, axis: int, mode: int):
        flib.stop_single_axis(self.id, axis, mode)

    @validate_call
    def get_axis_current_pos(self, axis: int):
        pos = c_float(0)
        flib.get_axis_current_pos(self.id, axis, byref(pos))
        return pos.value

    @validate_call
    def get_axis_current_speed(self, axis: int):
        speed = c_float(0)
        flib.get_axis_current_speed(self.id, axis, byref(speed))
        return speed.value

    @validate_call
    def set_output(self, io: int, status: int):
        flib.set_output(self.id, io, status)

    @validate_call
    def get_input(self, io: int):
        status = c_int(0)
        flib.get_input(self.id, io, byref(status))
        return status.value

    @validate_call
    def write_data_to_485(self, data: str):
        data = data.encode("utf-8")
        length = len(data)
        flib.write_data_to_485(self.id, data, length)

    @validate_call
    def read_data_from_485(self):
        data = create_string_buffer(100)
        length = c_int(0)
        flib.read_data_from_485(self.id, data, length)
        return data.value.decode("utf-8")

    @validate_call
    def set_fsc_speed(self, slave_id: int, speed: int):
        flib.set_fsc_speed(self.id, slave_id, speed)

    @validate_call
    def line_2axis(
        self, axis: int, end_x: int, end_y: int, speed: float, acc: float, dec: float
    ):
        flib.line_2axis(self.id, axis, end_x, end_y, speed, acc, dec)

    @validate_call
    def line_3axis(
        self,
        axis: int,
        end_x: float,
        end_y: float,
        end_z: float,
        speed: float,
        acc: float,
        dec: float,
    ):
        flib.line_3axis(self.id, axis, end_x, end_y, end_z, speed, acc, dec)

    @validate_call
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

    def stop_fun(self):
        flib.stop_run(self.id)

    def get_machine_status(self):
        ms = flib.MachineStatus()
        flib.get_machine_status(self.id, byref(ms))
        return machine_status_turn(ms)

    def get_device_para(self):
        dp = flib.DevicePara()
        flib.get_device_para(self.id, byref(dp))
        return device_para_turn(dp)

    @validate_call
    def set_device_para(self, para: DevicePara):
        para = device_para_return(para)
        flib.set_device_para(self.id, byref(para))
