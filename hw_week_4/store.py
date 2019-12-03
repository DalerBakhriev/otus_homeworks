import json
import logging
from abc import ABC, abstractmethod
from typing import List, NoReturn, Optional, Union

from redis.client import Redis
from redis.exceptions import ConnectionError, TimeoutError


class AbstractKeyValueStorage(ABC):

    """
    Abstract key value storage
    """

    @abstractmethod
    def get(self, key: str):
        pass

    @abstractmethod
    def cache_get(self, key: str):
        pass

    @abstractmethod
    def cache_set(self, key, value, key_expire_time_sec):
        pass


class KeyValueStorage(AbstractKeyValueStorage):

    """
    Key value storage with redis server
    """

    CACHE_INTERACTION_RETRIES_LIMIT = 2

    def __init__(self, host: str, port: int):

        self.host = host
        self.port = port
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
                port=self.port
            )
            self._kv_storage.ping()
        except Exception:
            logging.error(
                "Got error while connecting to redis with host %s and port %d. Retrying...",
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

    def get(self, key: str, retry_counter: int = 0) -> str:

        """
        Gets value by key as from persistent data storage
        :param key: key to get value for
        :param retry_counter: counter of connection retries
        :return: value for specified key
        """

        result = None
        try:
            result = self._kv_storage.get(key)
        except (ConnectionError, TimeoutError) as exception:

            if retry_counter >= self.CACHE_INTERACTION_RETRIES_LIMIT:
                raise exception

            retry_counter += 1
            self._reset_connection()
            self.get(key=key, retry_counter=retry_counter)

        return result.decode("utf-8") if result is not None else result

    def cache_get(self, key: str, retry_counter: int = 0) -> Optional[float]:

        """
        Gets value by key from cache
        :param key: key to get value for
        :param retry_counter: counter of retries number
        :return: float value if found some in cache and None otherwise
        """

        result = None
        try:
            result = self._kv_storage.get(key)
        except (ConnectionError, AttributeError, TimeoutError):
            if retry_counter >= self.CACHE_INTERACTION_RETRIES_LIMIT:
                return result
            retry_counter += 1
            self._reset_connection()
            self.cache_get(key=key, retry_counter=retry_counter)

        return float(result.decode("utf-8")) if result is not None else result

    def cache_set(self, key: str,
                  value: float,
                  key_expire_time_sec: int,
                  retry_counter: int = 0) -> NoReturn:

        """
        Sets the value into cash by specified key
        :param key: key to set value for
        :param value: value for setting
        :param key_expire_time_sec: time in which key will be expired
        :param retry_counter: counter of retries number
        """

        try:
            self._kv_storage.set(key, str(value), ex=key_expire_time_sec)
        except (ConnectionError, AttributeError, TimeoutError):
            if retry_counter >= self.CACHE_INTERACTION_RETRIES_LIMIT:
                logging.error(
                    "Could not set key %s and value %s "
                    "in redis with host %s and port %s.",
                    key,
                    value,
                    self.host,
                    self.port
                )
                return
            logging.error(
                "Got error while setting key %s and value %s "
                "in redis with host %s and port %s. Retrying...",
                key,
                value,
                self.host,
                self.port
            )
            retry_counter += 1
            self._reset_connection()
            self.cache_set(
                key=key,
                value=str(value),
                key_expire_time_sec=key_expire_time_sec,
                retry_counter=retry_counter
            )

    def clear(self) -> NoReturn:
        self._kv_storage.flushall()


class KeyValueTestStorage(AbstractKeyValueStorage):

    """
    Test key value storage
    """

    def __init__(self):

        self._kv_store = dict()

    def get(self, key: str) -> str:

        return self._kv_store[key]

    def set(self, key: str, value: List[str]):
        self._kv_store[key] = json.dumps(value)

    def cache_get(self, key: str) -> Optional[Union[int, float]]:
        return self._kv_store.get(key)

    def cache_set(self,
                  key: str,
                  value: Union[int, float],
                  key_expire_time_sec: int) -> NoReturn:
        self._kv_store[key] = value

    def clear(self) -> NoReturn:
        self._kv_store.clear()


if __name__ == "__main__":
    kv_store = KeyValueStorage(host="localhost", port=6379)
    kv_store.cache_set('ab', '43.8', key_expire_time_sec=60)
    print(kv_store.cache_get('ab'))