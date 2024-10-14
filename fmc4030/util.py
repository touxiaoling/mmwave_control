import time
from functools import wraps
from threading import Lock

def min_delay(min_delay_time=0.001):
    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            with self._next_time_lock:
                sleep_time = self._next_time - time.monotonic()
                if sleep_time > 0:
                    time.sleep(sleep_time)

                res = func(self, *args, **kwargs)

                self._next_time = time.monotonic() + min_delay_time

                return res

        return wrapper

    return decorator
