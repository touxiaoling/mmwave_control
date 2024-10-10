import time
from functools import wraps


class DelayDecorator:
    def __init__(self, delay_time):
        self.delay_time = delay_time
        self.next_time_lock = 0

    def __call__(self, func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            sleep_time = self.next_time_lock - time.monotonic()
            if sleep_time > 0:
                time.sleep(sleep_time)

            res = func(*args, **kwargs)

            self.next_time_lock = time.monotonic() + self.delay_time

            return res

        return wrapper
