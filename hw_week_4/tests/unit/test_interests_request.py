import datetime
import json
import random

import api
import pytest
from dateutil.relativedelta import relativedelta
from store import KeyValueTestStorage
from tests.utils import set_valid_auth


@pytest.fixture(scope="function", params=[
        {},
        {"date": "20.07.2017"},
        {"client_ids": [], "date": "20.07.2017"},
        {"client_ids": {1: 2}, "date": "20.07.2017"},
        {"client_ids": ["1", "2"], "date": "20.07.2017"},
        {"client_ids": [1, 2], "date": "XXX"},
    ],
    ids=["empty_request",
         "date_only",
         "empty_client_ids",
         "client_ids_as_dict",
         "client_id_as_string",
         "date_is_not_convertible"])
def param_test_invalid_interests_request(request):
    return request.param


@pytest.fixture(scope="function", params=[
        {"client_ids": [1, 2, 3], "date": datetime.datetime.today().strftime("%d.%m.%Y")},
        {"client_ids": [1, 2], "date": "19.07.2017"},
        {"client_ids": [0]}
    ],
    ids=["three_ids_today", "two_ids_some_time_ago", "one_id_without_date"]
)
def param_test_ok_interests_request(request):
    interests = [
        "cars", "pets", "travel", "hi-tech", "sport",
        "music", "books", "tv", "cinema", "geek", "otus"
    ]
    store = KeyValueTestStorage()
    for client_id in request.param["client_ids"]:
        store.set(f"i:{client_id}", random.sample(interests, 2))

    def clear_storage():
        store.clear()

    request.addfinalizer(clear_storage)

    return request.param, store


@pytest.fixture(scope="function", params=[
        {"client_ids": [1, 2, 3], "date": "01.30.1995"},
        {"client_ids": [1, 2, 3], "date": "1995.01.30"},
        {"client_ids": [1, 2, 3], "date": 10012000},
        {"client_ids": [1, 2, 3], "date": "long time ago"},
        {"client_ids": [1, 2, 3], "date": datetime.datetime.today().date() + relativedelta(days=1)},
        {"client_ids": [1, 2, 3], "date": datetime.datetime.today()},
        {"client_ids": [1, 2, 3], "date": (datetime.datetime.today().date() + relativedelta(days=1)).strftime("%d%m%Y")},
        {"client_ids": [1, 2, 3], "date": "yesterday"},
        {"client_ids": [1, 2, 3], "date": "tomorrow"}
    ],
    ids=[
        "date_format_day.month.year",
        "date_format_year.month.day",
        "date_format_as_integer",
        "long_time_ago",
        "current date plus one day as date",
        "current date as date",
        "current date plus one day as string",
        "yesterday",
        "tomorrow"
    ]
)
def param_test_invalid_date_interests_request(request):

    interests = [
        "cars", "pets", "travel", "hi-tech", "sport",
        "music", "books", "tv", "cinema", "geek", "otus"
    ]
    store = KeyValueTestStorage()
    for client_id in request.param["client_ids"]:
        store.set(f"i:{client_id}", random.sample(interests, 2))

    def clear_storage():
        store.clear()

    request.addfinalizer(clear_storage)

    return request.param, store


def test_invalid_interests_request(param_test_invalid_interests_request):

    """
    Tests invalid clients interests request
    """

    request = {
        "account": "horns&hoofs", "login": "h&f",
        "method": "clients_interests", "arguments": param_test_invalid_interests_request
    }
    set_valid_auth(request)
    response, code = api.method_handler(
        request={"body": request, "headers": dict()},
        ctx=dict(),
        store=KeyValueTestStorage()
    )
    assert code == api.INVALID_REQUEST
    assert response


def test_ok_interests_request(param_test_ok_interests_request):

    """
    Tests ok clients interests request
    """

    test_context = dict()
    request_arguments, test_store = param_test_ok_interests_request
    request = {
        "account": "horns&hoofs", "login": "h&f", "method":
            "clients_interests", "arguments": request_arguments
    }
    set_valid_auth(request)
    response, code = api.method_handler(
        request={"body": request, "headers": dict()},
        ctx=test_context,
        store=test_store
    )
    assert code == api.OK
    assert len(request_arguments["client_ids"]) == len(response)
    assert all(
        v and isinstance(v, list) and all(isinstance(i, str) for i in v)
        for v in response.values()
    )
    assert test_context.get("nclients") == len(request_arguments["client_ids"])


def test_invalid_date_interests_request(param_test_invalid_date_interests_request):

    """
    Tests clients_interests request with invalid date
    """

    request_arguments, test_store = param_test_invalid_date_interests_request
    request = {
        "account": "horns&hoofs", "login": "h&f",
        "method": "clients_interests", "arguments": request_arguments
    }
    set_valid_auth(request)
    response, code = api.method_handler(
        request={"body": request, "headers": dict()},
        ctx=dict(),
        store=test_store
    )
    assert code == api.INVALID_REQUEST
    assert "error" in response
    errors = json.loads(response["error"])
    assert "date" in errors
    assert len(errors) == 1
