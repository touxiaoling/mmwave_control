import subprocess
import functools
import time

def subprocess_popen(cmd):
    start_cmd = ["stdbuf","-oL"]
    start_cmd.extend(cmd)
    with subprocess.Popen(start_cmd,capture_output=True,bufsize=0) as process:
        while True:
            line = process.stdout.readline().decode().strip()
            if not line and process.poll() is not None:
                break
            yield line
        process.stdout.close()
        return_code = process.wait()
        if return_code != 0:
            raise IOError(f"command return code {return_code},error info:\n{process.stderr.readlines()}")

def retry(times=3,delay=1):
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