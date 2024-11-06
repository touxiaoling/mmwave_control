import subprocess
from contextlib import contextmanager
from pathlib import Path
from .util import subprocess_popen
class mmwave():
    def __init__(self,config_file:Path=None):
        self.config_file = config_file

    @contextmanager
    def run(self,datadir:str,record_time:int):
        cmd = ["mmwave","-d",f"{datadir}","--record" ,"--time" ,f"{record_time}"]
        for line in subprocess_popen(cmd):
            print(line)
            if "Framing" in line:
                print("capture Framing")
                yield self

    def configure(self,config:dict):
        cmd = ["mmwave","--configure",]
        if self.config_file:
            cmd.extend["-f",f"{self.config_file}"]
        for line in subprocess_popen(cmd):
            print(line)
        
    def get(self,datadir:str,savedir:str):
        cmd = f"scp -r -O root@192.168.33.180:{datadir} {savedir}"
        return subprocess.run(cmd)