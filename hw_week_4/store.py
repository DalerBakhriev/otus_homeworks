import logging
from typing import Callable, NoReturn, Optional, Union
from functools import wraps
from redis.client import Redis
from redis.exceptions import ConnectionError, TimeoutError


def make_retries(method: Callable) -> Callable:

    """
    Decorator for making auto retries
    fro methods of key-value storage
    """

    @wraps(method)
    def wrapper(self, *method_args, **method_kwargs):
        result = None
        try:
            result = method(self, *method_args, **method_kwargs)
        except (ConnectionError, TimeoutError) as exception:
            if wrapper.calls >= self.retries_limit:
                if "cache" in method.__name__:
                    return
                raise exception
            wrapper.calls += 1
            self._reset_connection()
            wrapper(self, *method_args, **method_kwargs)
        return result

    wrapper.calls = 0
    return wrapper


class KeyValueStorage:

    """
    Key value storage with redis server
    """

    def __init__(self, host: str, port: int, retries_limit: int, timeout: int):

        self.host = host
        self.port = port
        self.timeout = timeout
        self.retries_limit = retries_limit
        self._kv_storage = None
        self._connect()

    def _connect(self) -> NoReturn:

        """
        Connection to redis server with retries
        :param retry_counter: counter of times of retrying
        :return: Redis connection if it was successful and None otherwise
        """

        try:
            self._kv_storage = Redis(
                host=self.host,
                port=self.port,
                socket_timeout=self.timeout
            )
            self._kv_storage.ping()
        except Exception:
            logging.error(
                "Got error while connecting to redis with host %s and port %d.",
                self.host,
                self.port
            )

    def _reset_connection(self) -> NoReturn:

        """
        Resets connection to redis server
        :return:
        """

        self._kv_storage.close()
        self._connect()

    @make_retries
    def get(self, key: str) -> str:

        """
        Gets value by key as from persistent data storage
        :param key: key to get value for
        :return: value for specified key
        """

        result = self._kv_storage.get(key)

        return result.decode("utf-8") if result is not None else result

    @make_retries
    def cache_get(self, key: str) -> Optional[float]:

        """
        Gets value by key from cache
        :param key: key to get value for
        :return: float value if found some in cache and None otherwise
        """

        result = self._kv_storage.get(key)

        return float(result.decode("utf-8")) if result is not None else result

    @make_retries
    def cache_set(self, key: str,
                  value: Union[float, int],
                  key_expire_time_sec: int) -> NoReturn:

        """
        Sets the value into cache by specified key
        :param key: key to set value for
        :param value: value for setting
        :param key_expire_time_sec: time in which key will be expired
        """

        self._kv_storage.set(key, str(value), ex=key_expire_time_sec)

    def clear(self) -> NoReturn:
        self._kv_storage.flushall()
