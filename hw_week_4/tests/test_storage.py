import json
from typing import List, NoReturn, Optional, Union


class KeyValueTestStorage:

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