import subprocess
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