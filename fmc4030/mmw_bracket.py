import time
import math

from .fmc4030 import FMC4030
from . import fmc4030lib as flib


def cal_running_time(length, speed, acc, dec):
    t_acc_dec = speed / acc + speed / dec  # 刚好加速到speed就减速的总时间
    min_length = t_acc_dec * speed / 2  # 最小移动距离
    length = abs(length)
    if length < min_length:
        running_t = t_acc_dec * min_length / length  # 如果小于最小移动距离，就根据相似三角形计算时间
    else:
        running_t = t_acc_dec + (length - min_length) / speed

    return running_t


class MMWBraket:
    def __init__(
        self,
        bc: FMC4030,
        x_speed: float = 200.0,
        x_acc: float = 200.0,
        x_dec: float = 200.0,
        x_fall_step: float = 5,
        x_home_speed: float = 50,
        x_reverse: bool = False,
        y_speed: float = 150.0,
        y_acc=200.0,
        y_dec=200.0,
        y_home_speed: float = 50,
        y_fall_step: float = 5,
        y_reverse: int = True,
    ):
        self.bc = bc
        self.x_speed = x_speed
        self.x_acc = x_acc
        self.x_dec = x_dec
        self.x_fall_step = x_fall_step
        self.x_home_speed = x_home_speed
        self.x_reverse = x_reverse
        self.x_pos_limit = 970

        self.y_speed = y_speed
        self.y_acc = y_acc
        self.y_dec = y_dec
        self.y_fall_step = y_fall_step
        self.y_home_speed = y_home_speed
        self.y_reverse = y_reverse
        self.y_pos_limit = 1970

        self.x_pos = 0.0
        self.y_pos = 0.0

        if not self.bc.connected:
            self.bc.open_device()

    def jog_x(self, pos: float, speed: float = None, acc: float = None, dec: float = None):
        if not 0 <= pos <= self.x_pos_limit:
            raise ValueError(f"x pos {pos} out limit 0~{self.x_pos_limit}")
        speed = speed or self.x_speed
        acc = acc or self.x_acc
        dec = dec or self.x_dec

        real_pos = -pos if self.x_reverse else pos
        self.bc.jog_single_axis_absolute(flib.AXIS_X, real_pos, speed, acc, dec)

        running_time = cal_running_time(pos - self.x_pos, speed, acc, dec) - 0.1
        if running_time >= 0:
            time.sleep(running_time)

        self.bc.wait_axis_stop(flib.AXIS_X)
        self.x_pos = pos

    def jog_y(self, pos: float, speed: float = None, acc: float = None, dec: float = None):
        if not 0 <= pos <= self.y_pos_limit:
            raise ValueError(f"y pos {pos} out limit 0~{self.y_pos_limit}")
        speed = speed or self.y_speed
        acc = acc or self.y_acc
        dec = dec or self.y_dec

        real_pos = -pos if self.y_reverse else pos
        self.bc.jog_single_axis_absolute(flib.AXIS_Y, real_pos, speed, acc, dec)

        running_time = cal_running_time(pos - self.y_pos, speed, acc, dec) - 0.1
        if running_time >= 0:
            time.sleep(running_time)

        self.bc.wait_axis_stop(flib.AXIS_Y)
        self.y_pos = pos

    def home_axis(self, home_axis=True, x_reverse_corrector=False, y_reverse_corrector=False):
        x_pos = self.x_pos_limit if x_reverse_corrector else 0
        y_pos = self.y_pos_limit if y_reverse_corrector else 0

        self.bc.jog_single_axis_absolute(flib.AXIS_X, x_pos, self.x_speed, self.x_acc, self.x_dec)
        self.bc.jog_single_axis_absolute(flib.AXIS_Y, y_pos, self.y_speed, self.y_acc, self.y_dec)

        self.bc.wait_axis_stop(flib.AXIS_X)
        self.bc.wait_axis_stop(flib.AXIS_Y)

        if home_axis:
            x_dir = 2 if self.x_reverse else 1
            self.bc.home_single_axis(flib.AXIS_X, self.x_home_speed, self.x_acc, self.x_fall_step, x_dir)
            y_dir = 2 if self.y_reverse else 1
            self.bc.home_single_axis(flib.AXIS_Y, self.y_home_speed, self.y_acc, self.y_fall_step, y_dir)
            time.sleep(12)
            
        self.x_pos = 0.0
        self.y_pos = 0.0