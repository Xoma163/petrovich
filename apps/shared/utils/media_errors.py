from contextlib import contextmanager

import requests
from selenium.common import TimeoutException
from urllib3.exceptions import ReadTimeoutError

from apps.shared.exceptions import PWarning


@contextmanager
def media_request_errors():
    """Translate transport failures without hiding parser or programming errors."""
    try:
        yield
    except (requests.Timeout, TimeoutException, ReadTimeoutError) as error:
        raise PWarning("Медиасервис не ответил вовремя. Попробуйте позже") from error
    except requests.exceptions.ChunkedEncodingError as error:
        raise PWarning("Загрузка медиа оборвалась. Попробуйте ещё раз") from error
    except requests.ConnectionError as error:
        raise PWarning("Не удалось подключиться к медиасервису. Попробуйте позже") from error
    except requests.HTTPError as error:
        status = error.response.status_code if error.response is not None else None
        if status == 429:
            message = "Медиасервис ограничил число запросов. Попробуйте позже"
        elif status in (401, 403):
            message = "Медиасервис отказал в доступе. Не удалось загрузить медиа"
        else:
            message = "Не удалось загрузить медиа с сервиса. Попробуйте позже"
        raise PWarning(message) from error
    except requests.RequestException as error:
        raise PWarning("Не удалось загрузить медиа с сервиса. Попробуйте позже") from error
