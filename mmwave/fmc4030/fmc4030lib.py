from ctypes import Structure, c_float, c_int, c_uint, c_ushort, c_char, c_char_p, POINTER
from ctypes import CDLL
import platform
from pathlib import Path
from typing import Any

# @machine_status.machineRunStatus
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

AXIS_X = 0
AXIS_Y = 1
AXIS_Z = 2

RELATIVE_MOTION = 1
ABSOLUTE_MOTION = 2

P_LIMIT = 1
N_LIMIT = 2


class MachineStatus(Structure):
    _fields_ = [
        ("realPos", c_float * 3),
        ("realSpeed", c_float * 3),
        ("inputStatus", c_uint),
        ("outputStatus", c_uint),
        ("limitNStatus", c_uint),
        ("limitPStatus", c_uint),
        ("machineRunStatus", c_uint),
        ("axisStatus", c_uint * 3),
        ("homeStatus", c_uint),
        ("file", c_char * 600),
    ]


class DevicePara(Structure):
    _fields_ = [
        ("id", c_uint),
        ("bound232", c_uint),
        ("bound485", c_uint),
        ("ip", c_char * 15),
        ("port", c_int),
        ("div", c_int * 3),
        ("lead", c_int * 3),
        ("softLimitMax", c_int * 3),
        ("softLimitMin", c_int * 3),
        ("homeTime", c_int * 3),
    ]


class MachineVersion(Structure):
    _fields_ = [
        ("firmware", c_uint),
        ("lib", c_uint),
        ("serialNumber", c_uint),
    ]


class MacTestFunc:
    def __init__(self):
        self.argtypes = c_int
        self.errcheck = None

    def __call__(self, *args: Any, **kwds: Any) -> Any:
        pass


class MacTestLib:
    def __init__(self):
        self.dynamic_methods = {}

    def __getattr__(self, name):
        if name not in self.dynamic_methods:
            # print(f"Creating method '{name}' dynamically")

            self.dynamic_methods[name] = MacTestFunc()

        return self.dynamic_methods[name]


# 加载动态库
def loadlib() -> CDLL:
    lib_path = Path(__file__).parent
    match platform.system():
        case "Linux":
            from ctypes import cdll

            fmc4030lib = cdll.LoadLibrary(lib_path / "lib/ubuntu/x64/libFMC4030-Lib.so")
        case "Windows":
            from ctypes import windll

            fmc4030lib = windll.LoadLibrary(lib_path / "lib/win/x64/FMC4030-Dll.dll")
        case "Darwin":
            print("WARNNING:running in Mac system! lib not found!")
            fmc4030lib = MacTestLib()
        case _:
            raise ValueError(f"unknow system {platform.system()}")
    return fmc4030lib


def validate_code(rcode, func, arguments):
    if -6 <= rcode <= -1:
        raise ValueError(f"error code {rcode}")

    return rcode


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

mb01_operation = flib.FMC4030_MB01_Operation
mb01_operation.argtypes = [c_int, c_int, c_ushort, c_char_p, POINTER(c_int)]
mb01_operation.errcheck = validate_code

mb03_operation = flib.FMC4030_MB03_Operation
mb03_operation.argtypes = [c_int, c_int, c_ushort, c_int, c_char_p, POINTER(c_int)]
mb03_operation.errcheck = validate_code

mb05_operation = flib.FMC4030_MB05_Operation
mb05_operation.argtypes = [c_int, c_int, c_ushort, c_ushort, c_char_p, POINTER(c_int)]
mb05_operation.errcheck = validate_code

mb06_operation = flib.FMC4030_MB06_Operation
mb06_operation.argtypes = [c_int, c_int, c_ushort, c_ushort, c_char_p, POINTER(c_int)]
mb06_operation.errcheck = validate_code

mb16_operation = flib.FMC4030_MB16_Operation
mb16_operation.argtypes = [c_int, c_int, c_ushort, c_int, POINTER(c_ushort), c_char_p, POINTER(c_int)]
mb16_operation.errcheck = validate_code

line_2axis = flib.FMC4030_Line_2Axis
line_2axis.argtypes = [c_int, c_uint, c_float, c_float, c_float, c_float, c_float]
line_2axis.errcheck = validate_code

line_3axis = flib.FMC4030_Line_3Axis
line_3axis.argtypes = [c_int, c_uint, c_float, c_float, c_float, c_float, c_float, c_float]
line_3axis.errcheck = validate_code

arc_2axis = flib.FMC4030_Arc_2Axis
arc_2axis.argtypes = [c_int, c_uint, c_float, c_float, c_float, c_float, c_float, c_float, c_float, c_float, c_int]
arc_2axis.errcheck = validate_code

pause_run = flib.FMC4030_Pause_Run
pause_run.argtypes = [c_int, c_uint]
pause_run.errcheck = validate_code

resume_run = flib.FMC4030_Resume_Run
resume_run.argtypes = [c_int, c_uint]
resume_run.errcheck = validate_code

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

get_version_info = flib.FMC4030_Get_Version_Info
get_version_info.argtypes = [c_int, POINTER(MachineVersion)]
get_version_info.errcheck = validate_code

download_file = flib.FMC4030_Download_File
download_file.argtypes = [c_int, c_char_p, c_int]
download_file.errcheck = validate_code

start_auto_run = flib.FMC4030_Start_Auto_Run
start_auto_run.argtypes = [c_int, c_char_p]
start_auto_run.errcheck = validate_code

stop_auto_run = flib.FMC4030_Stop_Auto_Run
stop_auto_run.argtypes = [c_int]
stop_auto_run.errcheck = validate_code

delete_script_file = flib.FMC4030_Delete_Script_File
delete_script_file.argtypes = [c_int, c_char_p]
delete_script_file.errcheck = validate_code
