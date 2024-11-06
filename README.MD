# mmwave_control

This is an active millimeter-wave scanning framework code, which is still under development.

# fmc4030 control issue


FMC4030_Get_Axis_Current_Pos 函数第一次调用会返回正确位置，然后接下来调用任何函数都会卡死（如FMC4030_Jog_Single_Axis），返回错误码-6。作为对比 FMC4030_Get_Axis_Current_Speed函数没有发现同样的问题。


FMC4030_Get_Machine_Status 函数调用后返回代码664，该代码不在说明书的返回值列表里，但返回的状态信息正常。

两个任意函数调用时间间隔小于1ms时，第二次函数调用大概率不会响应。

# References and dependencies:

•	https://github.com/azinke/mmwave
•	https://github.com/azinke/mmwave-repack


#  清华源
pip config set global.index-url https://mirrors.tuna.tsinghua.edu.cn/pypi/web/simple