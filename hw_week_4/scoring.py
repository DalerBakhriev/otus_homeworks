import datetime
import hashlib
import json
from typing import List, Optional, Union

from store import KeyValueStorage


def get_score(store: KeyValueStorage,
              phone: Optional[Union[str, int]],
              email: Optional[str],
              birthday: Optional[datetime.date] = None,
              gender: Optional[int] = None,
              first_name: Optional[str] = None,
              last_name: Optional[str] = None) -> Union[int, float]:

    """
    Returns score based on user's information
    :param store: key-value cache
    :param phone: phone number
    :param email: email address
    :param birthday: birthday date
    :param gender: gender
    :param first_name: first name
    :param last_name: last name
    :return: score
    """

    key_parts = [
        first_name or "",
        last_name or "",
        str(phone) or "",
        birthday if birthday is not None else "",
    ]

    key = "uid:" + hashlib.md5("".join(key_parts).encode("utf-8")).hexdigest()
    # try get from cache,
    # fallback to heavy calculation in case of cache miss
    score = store.cache_get(key) or 0
    if score:
        return score
    if phone:
        score += 1.5
    if email:
        score += 1.5
    if birthday and gender:
        score += 1.5
    if first_name and last_name:
        score += 0.5
    # cache for 60 minutes
    store.cache_set(key, score, key_expire_time_sec=60 * 60)

    return score


def get_interests(store: KeyValueStorage, client_id: int) -> List[str]:

    """
    Gets client's interests by id
    :param store: ke-value storage
    :param client_id: id of client
    :return: list of clients interests
    """

    r = store.get("i:%s" % client_id)
    return json.loads(r) if r else []
