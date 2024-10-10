from fmc4030 import FMC4030

fmc4030 = FMC4030()
fmc4030.open_device()
pos = fmc4030.get_axis_current_pos(0)
print(pos)
fmc4030.close_device()
