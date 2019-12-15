import random

import pytest
from redis.exceptions import ConnectionError
from store import KeyValueStorage


TEST_RETRIES_LIMIT = 3
TEST_TIMEOUT = 3


@pytest.fixture()
def working_store(request):

    store = KeyValueStorage(
        host="localhost",
        port=6379,
        retries_limit=TEST_RETRIES_LIMIT,
        timeout=TEST_TIMEOUT
    )

    def clear_store():
        store.clear()

    request.addfinalizer(clear_store)

    return store


@pytest.fixture()
def not_working_store():
    not_working_store = KeyValueStorage(
        host="non_existent_host",
        port=404,
        retries_limit=TEST_RETRIES_LIMIT,
        timeout=TEST_TIMEOUT
    )
    return not_working_store


def test_get_key_from_cache(working_store):

    """
    Tests that we get exactly same value
    that we put in cache_store by the same key
    """

    test_value = random.randint(1, 200)
    test_key = "test_key"
    working_store.cache_set(test_key, test_value, key_expire_time_sec=60*60)

    assert working_store.cache_get(test_key) == test_value


def test_get_non_existent_key_from_cache(working_store):

    """
    Tests getting non-existent key from cache
    """

    assert working_store.cache_get("non_existent_key") is None


def test_get_non_existent_key_from_storage(working_store):

    """
    Tests getting non-existent key from storage
    """

    assert working_store.get("non_existent_key") is None


def test_get_key_from_closed_cache(not_working_store):

    """
    Tests getting key from closed or dead cache
    """

    test_key = "test_key_for_not_working_cache"
    not_working_store.cache_set(test_key, 404, key_expire_time_sec=60*60)

    assert not_working_store.cache_get(test_key) is None
    assert not_working_store.get.calls == not_working_store.retries_limit


def test_get_key_from_closed_storage(not_working_store):

    """
    Tests get key from closed or dead storage
    """

    with pytest.raises(ConnectionError):
        assert not_working_store.get("non_existent_key")
