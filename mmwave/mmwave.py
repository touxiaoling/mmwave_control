import time
import subprocess
from contextlib import contextmanager
from pathlib import Path
import tomllib

from .util import subprocess_popen,retry
from . import mmwcas


class MMWave:
    def __init__(self, data_dir: Path, config_dict: dict = None):
        self.config_dict = config_dict or dict()
        self.data_dir = data_dir

    def read_config(self, config_file: Path):
        with config_file.open("rb") as file:
            config = tomllib.load(file)
        self.config_dict.update(config)

    def initial(self, config: dict = None):
        if config:
            config = {**self.config_dict, **config}
        else:
            config = self.config_dict
        if status := mmwcas.mmw_set_config(config):
            raise RuntimeError(f"mmw_set_config failed with status {status}")
        if status := mmwcas.mmw_init():
            raise RuntimeError(f"mmw_init failed with status {status}")
        return self

    def start_record(self,data_dir:str):
        if status := mmwcas.mmw_arming_tda(data_dir):
            raise RuntimeError(f"mmw_arming_tda failed with status {status}")
        time.sleep(2)
        for i in range(3):
            if status := mmwcas.mmw_start_frame():
                print("start frame fail")
                time.sleep(2)
                mmwcas.mmw_stop_frame()
                time.sleep(2)
                mmwcas.mmw_dearming_tda()
                time.sleep(2)
                mmwcas.mmw_arming_tda(data_dir)
                time.sleep(2)
            else:
                break
        return self

    def stop_record(self):
        if status := mmwcas.mmw_stop_frame():
            raise RuntimeError(f"mmw_stop_frame failed with status {status}")
        time.sleep(2)
        if status := mmwcas.mmw_dearming_tda():
            raise RuntimeError(f"mmw_dearming_tda failed with status {status}")
        return self

    @contextmanager
    def record(self):
        self.start_record()
        yield
        self.stop_record()

    def get(self, datadir: str, savedir: str):
        cmd = f"scp -r -O root@192.168.33.180:{datadir} {savedir}"
        return subprocess.run(cmd)
