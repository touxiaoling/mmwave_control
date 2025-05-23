import tomllib
import subprocess
from subprocess import PIPE
import functools
import time
from pathlib import Path

import numpy as np
import tomli_w


def subprocess_popen(cmd):
    start_cmd = ["stdbuf", "-oL"]
    start_cmd.extend(cmd)
    with subprocess.Popen(start_cmd, stdout=PIPE, stderr=PIPE, bufsize=0) as process:
        while True:
            stdout_line = process.stdout.readline().decode().strip()
            stderr_line = process.stderr.readline().decode().strip()

            if stdout_line:
                yield stdout_line
            if stderr_line:
                yield stderr_line

            if not stdout_line and not stderr_line and process.poll() is not None:
                break

        process.stdout.close()
        process.stderr.close()
        return_code = process.wait()

        if return_code != 0:
            raise IOError(f"command return code {return_code}, error info:\n{stderr_line}")


def retry(times=3, delay=1):
    """
    一个重试装饰器。

    :param times: 重试次数，默认为3次。
    :param delay: 每次重试之间的延迟时间（秒），默认为1秒。
    """

    def decorator_retry(func):
        @functools.wraps(func)
        def wrapper_retry(*args, **kwargs):
            attempts = 0
            while attempts < times:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    attempts += 1
                    if attempts >= times:
                        raise
                    time.sleep(delay)

        return wrapper_retry

    return decorator_retry


def turn_toml(save_path: Path | str, info_dict: dict):
    save_path = Path(save_path)
    if Path(save_path).exists():
        Path(save_path).unlink()
    save_path.write_text(tomli_w.dumps(info_dict), encoding="utf-8")


def load_config(config_path: str = "config.toml"):
    """
    Load a configuration file and return the MMWConfig object.
    """
    from mmwave import schemas

    with Path(config_path).open("rb") as f:
        cfg = tomllib.load(f)
        cfg = schemas.MMWConfig.model_validate(cfg)
    return cfg


def load_frame(input_dir: Path, repack=False):
    cfg = load_config(input_dir / "config.toml")
    frame_file_path = input_dir / "all_mmw_array.npy"
    if not frame_file_path.exists() or repack:
        from mmwave.repack import turn_frame

        turn_frame(input_dir, cfg)

    frame_file: np.memmap = np.load(frame_file_path, mmap_mode="r")

    if frame_file.shape[0] != 16 or frame_file.shape[1] != 12:
        from mmwave.repack import turn_frame

        print("cache array old,return new array")
        turn_frame(input_dir, cfg)

        frame_file: np.memmap = np.load(frame_file_path, mmap_mode="r")

    return frame_file, cfg
