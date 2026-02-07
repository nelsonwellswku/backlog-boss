import time
from functools import wraps
from logging import getLogger
from typing import Callable, TypeVar

logger = getLogger(__name__)

T = TypeVar("T")


def timed(func: Callable[..., T]) -> Callable[..., T]:
    @wraps(func)
    def wrapper(*args, **kwargs) -> T:
        start_time = time.time()
        result = func(*args, **kwargs)
        elapsed_time = time.time() - start_time
        logger.info(f"{func.__name__} took {elapsed_time:.2f} seconds")
        return result

    return wrapper
