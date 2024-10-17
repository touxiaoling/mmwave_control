import time
import math
from contextlib import contextmanager
from threading import Lock

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

        self.x_axis_id = flib.AXIS_X
        self.y_axis_id = flib.AXIS_Z

        if not self.bc.connected:
            self.bc.open_device()

        self._break_lock_flag = True

    @property
    def x_dir(self):
        return 1 if self.x_reverse else 2

    @property
    def y_dir(self):
        return 1 if self.y_reverse else 2

    def _real_pos(self, pos, reverse):
        return -pos if reverse else pos

    @contextmanager
    def break_conrtol(self):
        io_id = 0
        if self._break_lock_flag:
            self._break_unlock_flag = False
            self.bc.set_output(io_id, 1)
            try:
                yield
            finally:
                self.bc.set_output(io_id, 0)
                self._break_unlock_flag = True
        else:
            yield

    def jog_x(self, pos: float, speed: float = None, acc: float = None, dec: float = None):
        if not 0 <= pos <= self.x_pos_limit:
            raise ValueError(f"x pos {pos} out limit 0~{self.x_pos_limit}")
        speed = speed or self.x_speed
        acc = acc or self.x_acc
        dec = dec or self.x_dec

        real_pos = self._real_pos(pos, self.x_reverse)
        self.bc.jog_single_axis_absolute(self.x_axis_id, real_pos, speed, acc, dec)

        running_time = cal_running_time(pos - self.x_pos, speed, acc, dec) - 0.1
        if running_time >= 0:
            time.sleep(running_time)

        self.bc.wait_axis_stop(self.x_axis_id)
        self.x_pos = pos

    def jog_y(self, pos: float, speed: float = None, acc: float = None, dec: float = None):
        if not 0 <= pos <= self.y_pos_limit:
            raise ValueError(f"y pos {pos} out limit 0~{self.y_pos_limit}")
        speed = speed or self.y_speed
        acc = acc or self.y_acc
        dec = dec or self.y_dec

        real_pos = self._real_pos(pos, self.y_reverse)
        with self.break_conrtol():
            self.bc.jog_single_axis_absolute(self.y_axis_id, real_pos, speed, acc, dec)

            running_time = cal_running_time(pos - self.y_pos, speed, acc, dec) - 0.1
            if running_time >= 0:
                time.sleep(running_time)

            self.bc.wait_axis_stop(self.y_axis_id)

        self.y_pos = pos

    def home_axis(self, home_axis=True, x_reverse_corrector=False, y_reverse_corrector=False):
        # x_pos = self.x_pos_limit if x_reverse_corrector else 0
        # y_pos = self.y_pos_limit if y_reverse_corrector else 0
        relative_len = 100

        with self.break_conrtol():
            pos = self._real_pos(relative_len, self.x_reverse)
            self.bc.jog_single_axis_relative(self.x_axis_id, pos, self.x_speed, self.x_acc, self.x_dec)
            pos = self._real_pos(relative_len, self.y_reverse)
            self.bc.jog_single_axis_relative(self.y_axis_id, pos, self.y_speed, self.y_acc, self.y_dec)

            self.bc.wait_axis_stop(self.x_axis_id)
            self.bc.wait_axis_stop(self.y_axis_id)

            if home_axis:
                self.bc.home_single_axis(self.x_axis_id, self.x_home_speed, self.x_acc, self.x_fall_step, self.x_dir)
                self.bc.home_single_axis(self.y_axis_id, self.y_home_speed, self.y_acc, self.y_fall_step, self.y_dir)

                time.sleep(1)

                self.bc.wait_axis_stop(self.x_axis_id, 1)
                self.bc.wait_axis_stop(self.y_axis_id, 1)
            # time.sleep(12)
        self.x_pos = 0.0
        self.y_pos = 0.0
