
from fmc4030 import FMC4030,MMWBraket



def main():
    fmc4030 = FMC4030()
    mmwb = MMWBraket(fmc4030)
    mmwb.home_axis()
    mmwb.jog_x(100)
    mmwb.jog_y(200)

if __name__ =="__main__":
    main()