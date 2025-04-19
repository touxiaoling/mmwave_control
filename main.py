from fmc4030 import FMC4030, Braket

fmc4030 = FMC4030()
with Braket(fmc4030) as mmwb:
    mmwb.home_axis()
    mmwb.jog_x(100)
    mmwb.jog_y(200)
