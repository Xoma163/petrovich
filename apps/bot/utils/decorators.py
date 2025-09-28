import time


def retry(times, exceptions, except_exceptions=None, sleep_time=0):
    """
    Retry Decorator
    Retries the wrapped function/method `times` times if the exceptions listed
    in ``exceptions`` are thrown
    :param times: The number of times to repeat the wrapped function/method
    :type times: Int
    :param Exceptions: lists of exceptions that trigger a retry attempt
    :type Exceptions: tuple of Exceptions
    """

    def decorator(func):
        def wrapper(*args, **kwargs):
            attempt = 0
            while attempt < times:
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    attempt += 1
                    if except_exceptions:
                        if any([isinstance(e, x) for x in except_exceptions]):
                            raise e
                    if sleep_time:
                        time.sleep(sleep_time)
            return func(*args, **kwargs)

        return wrapper

    return decorator
