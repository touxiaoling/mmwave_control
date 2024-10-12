import time
from functools import wraps


def min_delay(min_delay_time=0.001):
    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            sleep_time = self._next_time_lock - time.monotonic()
            if sleep_time > 0:
                time.sleep(sleep_time)

            res = func(self, *args, **kwargs)

            self._next_time_lock = time.monotonic() + min_delay_time

            return res

        return wrapper

    return decorator
