import subprocess


class mmwave():
    def __init__(self,):
        pass

    def run(self,datadir:str,record_time:int):
        cmd = f"mmwave -d {datadir} --configure --record --time {record_time}"
        return subprocess.run(cmd)

    def get(self,datadir:str,savedir:str):
        cmd = f"scp -r -O root@192.168.33.180:{datadir} {savedir}"
        return subprocess.run(cmd)