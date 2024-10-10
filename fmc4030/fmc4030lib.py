from ctypes import Structure, c_float, c_int, c_uint, c_char, c_char_p, POINTER
from ctypes import CDLL
import platform
from pathlib import Path

MACHINE_MANUAL = 0x0001
MACHINE_AUTO = 0x0002

# @machine_status.axisStatus
MACHINE_POWER_ON = 0x0000
MACHINE_RUNNING = 0x0001
MACHINE_PAUSE = 0x0002
MACHINE_RESUME = 0x0004
MACHINE_STOP = 0x0008
MACHINE_LIMIT_N = 0x0010
MACHINE_LIMIT_P = 0x0020
MACHINE_HOME_DONE = 0x0040
MACHINE_HOME = 0x0080
MACHINE_AUTO_RUN = 0x0100
MACHINE_LIMIT_N_NONE = 0x0200
MACHINE_LIMIT_P_NONE = 0x0400
MACHINE_HOME_NONE = 0x0800
MACHINE_HOME_OVERTIME = 0x1000


class MachineStatus(Structure):
    _fields_ = [
        ("realPos", c_float * 3),
        ("realSpeed", c_float * 3),
        ("inputStatus", c_uint * 1),
        ("outputStatus", c_uint * 1),
        ("limitNStatus", c_uint * 1),
        ("limitPStatus", c_uint * 1),
        ("machineRunStatus", c_uint * 1),
        ("axisStatus", c_uint * 3),
        ("homeStatus", c_uint * 1),
        ("file", c_char * 600),
    ]


class DevicePara(Structure):
    _fields_ = [
        ("id", c_uint * 1),
        ("bound232", c_uint * 1),
        ("bound485", c_uint * 1),
        ("ip", c_char * 15),
        ("port", c_int * 1),
        ("div", c_int * 3),
        ("lead", c_int * 3),
        ("softLimitMax", c_int * 3),
        ("softLimitMin", c_int * 3),
        ("homeTime", c_int * 3),
    ]


class MachineVersion(Structure):
    _fields_ = [
        ("firmware", c_uint * 1),
        ("lib", c_uint * 1),
        ("serialnumber", c_uint * 1),
    ]


# 加载动态库
def loadlib() -> CDLL:
    lib_path = Path(__file__).parent
    match platform.system():
        case "Linux" | "Darwin":
            from ctypes import cdll

            fmc4030lib = cdll.LoadLibrary(lib_path / "lib/ubuntu/x64/libFMC4030-Lib.so")
        case "Windows":
            from ctypes import windll

            fmc4030lib = windll.LoadLibrary(lib_path / "lib/win/x64/FMC4030-Dll.dll")
        case _:
            raise ValueError(f"unknow system {platform.system()}")
    return fmc4030lib


def validate_code(rcode, func, arguments):
    if rcode == 0:
        return True

    raise ValueError(f"error code {rcode}")


flib = loadlib()


open_device = flib.FMC4030_Open_Device
open_device.argtypes = [c_int, c_char_p, c_int]
open_device.errcheck = validate_code

close_device = flib.FMC4030_Close_Device
close_device.argtypes = [c_int]
close_device.errcheck = validate_code

jog_single_axis = flib.FMC4030_Jog_Single_Axis
jog_single_axis.argtypes = [c_int, c_int, c_float, c_float, c_float, c_float, c_int]
jog_single_axis.errcheck = validate_code

check_axis_is_stop = flib.FMC4030_Check_Axis_Is_Stop
check_axis_is_stop.argtypes = [c_int, c_int]
check_axis_is_stop.errcheck = validate_code

home_single_axis = flib.FMC4030_Home_Single_Axis
home_single_axis.argtypes = [c_int, c_int, c_float, c_float, c_float, c_int]
home_single_axis.errcheck = validate_code

stop_single_axis = flib.FMC4030_Stop_Single_Axis
stop_single_axis.argtypes = [c_int, c_int, c_int]
stop_single_axis.errcheck = validate_code

get_axis_current_pos = flib.FMC4030_Get_Axis_Current_Pos
get_axis_current_pos.argtypes = [c_int, c_int, POINTER(c_float)]
get_axis_current_pos.errcheck = validate_code


get_axis_current_speed = flib.FMC4030_Get_Axis_Current_Speed
get_axis_current_speed.argtypes = [c_int, c_int, POINTER(c_float)]
get_axis_current_speed.errcheck = validate_code

set_output = flib.FMC4030_Set_Output
set_output.argtypes = [c_int, c_int, c_int]
set_output.errcheck = validate_code

get_input = flib.FMC4030_Get_Input
get_input.argtypes = [c_int, c_int, POINTER(c_int)]
get_input.errcheck = validate_code

write_data_to_485 = flib.FMC4030_Write_Data_To_485
write_data_to_485.argtypes = [c_int, c_char_p, c_int]
write_data_to_485.errcheck = validate_code

read_data_from_485 = flib.FMC4030_Read_Data_From_485
read_data_from_485.argtypes = [c_int, POINTER(c_char), POINTER(c_int)]
read_data_from_485.errcheck = validate_code

# set_fsc_speed = flib.FMC4030_Set_FSC_Speed
# set_fsc_speed.argtypes = [c_int, c_int, c_float]
# set_fsc_speed.errcheck=validate_code

line_2axis = flib.FMC4030_Line_2Axis
line_2axis.argtypes = [c_int, c_uint, c_float, c_float, c_float, c_float, c_float]
line_2axis.errcheck = validate_code

line_3axis = flib.FMC4030_Line_3Axis
line_3axis.argtypes = [
    c_int,
    c_uint,
    c_float,
    c_float,
    c_float,
    c_float,
    c_float,
    c_float,
]
line_3axis.errcheck = validate_code

arc_2axis = flib.FMC4030_Arc_2Axis
arc_2axis.argtypes = [
    c_int,
    c_uint,
    c_float,
    c_float,
    c_float,
    c_float,
    c_float,
    c_float,
    c_float,
    c_float,
    c_int,
]
arc_2axis.errcheck = validate_code

stop_run = flib.FMC4030_Stop_Run
stop_run.argtypes = [c_int]
stop_run.errcheck = validate_code

get_machine_status = flib.FMC4030_Get_Machine_Status
get_machine_status.argtypes = [c_int, POINTER(MachineStatus)]
get_machine_status.errcheck = validate_code

get_device_para = flib.FMC4030_Get_Device_Para
get_device_para.argtypes = [c_int, POINTER(DevicePara)]
get_device_para.errcheck = validate_code

set_device_para = flib.FMC4030_Set_Device_Para
set_device_para.argtypes = [c_int, POINTER(DevicePara)]
set_device_para.errcheck = validate_code
