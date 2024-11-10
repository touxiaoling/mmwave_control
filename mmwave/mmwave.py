import time
import subprocess
from contextlib import contextmanager
from pathlib import Path
from .util import subprocess_popen
from . import mmwcas


class mmwave:
    def __init__(self, config_dict: dict = None):
        self.config_dict = config_dict or dict()

    def configure(self, config: dict = None):
        if config:
            config = {**self.config_dict, **config}
        else:
            config = self.config_dict
        if status := mmwcas.mmw_set_config(config):
            raise RuntimeError(f"mmw_set_config failed with status {status}")
        if status := mmwcas.mmw_init():
            raise RuntimeError(f"mmw_init failed with status {status}")
        return self

    def start_record(self, datadir: str):
        if status := mmwcas.mmw_arming_tda(datadir):
            raise RuntimeError(f"mmw_arming_tda failed with status {status}")
        time.sleep(2)
        if status := mmwcas.mmw_start_frame():
            raise RuntimeError(f"mmw_start_frame failed with status {status}")
        return self

    def stop_record(self):
        if status := mmwcas.mmw_stop_frame():
            raise RuntimeError(f"mmw_stop_frame failed with status {status}")
        time.sleep(2)
        if status := mmwcas.mmw_dearming_tda():
            raise RuntimeError(f"mmw_dearming_tda failed with status {status}")
        return self

    @contextmanager
    def record(self, datadir: str):
        self.start_record(datadir)
        yield
        self.stop_record()

    def get(self, datadir: str, savedir: str):
        cmd = f"scp -r -O root@192.168.33.180:{datadir} {savedir}"
        return subprocess.run(cmd)
