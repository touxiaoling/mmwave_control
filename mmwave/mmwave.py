import time
import subprocess
from contextlib import contextmanager
from pathlib import Path
import tomllib

from .util import subprocess_popen, retry

try:
    from . import mmwcas
except Exception as e:
    pass


class MMWaveCmd:
    def __init__(self, config_file: Path = None):
        self.config_file = config_file

    @contextmanager
    def record(self, data_dir: str, record_time: int):
        cmd = ["mmwave"]
        if self.config_file:
            cmd.extend(["-f", f"{self.config_file}"])
        cmd.extend(["--configure", "-d", f"{data_dir}", "--record", "--time", f"{record_time}"])
        for line in subprocess_popen(cmd):
            print(line)
            if "Framing" in line:
                print("capture Framing")
                yield self

    def _sync_time(self, start_time: float):
        start_cmd = ["stdbuf", "-oL"]
        cmd = ["ssh", "root@192.168.33.180", "cat /proc/uptime"]
        start_cmd.extend(cmd)
        with subprocess.Popen(start_cmd, stdout=subprocess.PIPE, bufsize=0) as process:
            device_time = process.stdout.readline()
            pc_time = time.time()

        device_time = float(device_time.decode().strip().split()[0])
        time_offset = pc_time - start_time - device_time
        return time_offset

    def sync_time(self, start_time, sync_time=10):
        offset = []
        for i in range(sync_time):
            offset.append(self._sync_time(start_time))
        return sum(offset) / len(offset)

    def get(self, datadir: str, savedir: str):
        cmd = ["scp", "-r", "-O", f"root@192.168.33.180:/mnt/ssd/{datadir}{savedir}"]
        return subprocess.run(cmd)


class MMWave:
    def __init__(self, config_dict: dict = None):
        self.config_dict = config_dict or dict()

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

    def start_record(self, data_dir: str):
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
    def record(self, data_dir: str):
        self.start_record(data_dir)
        yield
        self.stop_record()
