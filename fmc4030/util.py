import time
from functools import wraps


next_time_lock = 0


def min_delay(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        global next_time_lock
        sleep_time = next_time_lock - time.monotonic()
        if sleep_time > 0:
            time.sleep(sleep_time)

        res = func(*args, **kwargs)

        next_time_lock = time.monotonic() + 0.001

        return res

    return wrapper
