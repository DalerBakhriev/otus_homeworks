import datetime
import json

import api
import pytest
from dateutil.relativedelta import relativedelta
from tests.test_storage import KeyValueTestStorage
from tests.utils import set_valid_auth


@pytest.fixture(scope="function", params=[
        {},
        {"phone": "79175002040"},
        {"phone": "89175002040", "email": "stupnikov@otus.ru"},
        {"phone": "79175002040", "email": "stupnikovotus.ru"},
        {"phone": "79175002040", "email": "stupnikov@otus.ru", "gender": -1},
        {"phone": "79175002040", "email": "stupnikov@otus.ru", "gender": "1"},
        {"phone": "79175002040", "email": "stupnikov@otus.ru", "gender": 1, "birthday": "01.01.1890"},
        {"phone": "79175002040", "email": "stupnikov@otus.ru", "gender": 1, "birthday": "XXX"},
        {"phone": "79175002040", "email": "stupnikov@otus.ru", "gender": 1, "birthday": "01.01.2000", "first_name": 1},
        {"phone": "79175002040", "email": "stupnikov@otus.ru", "gender": 1, "birthday": "01.01.2000",
         "first_name": "s", "last_name": 2},
        {"phone": "79175002040", "birthday": "01.01.2000", "first_name": "s"},
        {"email": "stupnikov@otus.ru", "gender": 1, "last_name": 2},
    ],
    ids=[
        "empty_request",
        "only_phone",
        "phone_starts_with_eight_and_email",
        "phone_and_email_without_@",
        "invalid_gender_value",
        "gender_in_string_format",
        "too_old_birth_date",
        "birth_date_not_converted_to_date",
        "first_name_as_integer",
        "last_name_as_integer",
        "no_completed_pair",
        "no_completed_pair_and_last_name_as_integer"
    ])
def param_test_invalid_score_request(request):
    return request.param


@pytest.fixture(scope="function", params=[
        {"phone": "79175002040", "email": "stupnikov@otus.ru"},
        {"phone": 79175002040, "email": "stupnikov@otus.ru"},
        {"gender": 1, "birthday": "01.01.2000", "first_name": "a", "last_name": "b"},
        {"gender": 0, "birthday": "01.01.2000"},
        {"gender": 2, "birthday": "01.01.2000"},
        {"first_name": "a", "last_name": "b"},
        {"phone": "79175002040", "email": "stupnikov@otus.ru", "gender": 1, "birthday": "01.01.2000",
         "first_name": "a", "last_name": "b"},
    ],
    ids=["phone_str_email_ok",
         "phone_int_email_ok",
         "gender_birthday_first_last_name_ok",
         "gender_unknown_birthday_ok",
         "gender_female_birthday_ok",
         "first_last_name_ok",
         "phone_email_gender_first_last_name_ok"])
def param_test_ok_score_request(request):
    return request.param


@pytest.fixture(scope="function", params=[
    {"phone": {"79175002040"}, "email": "some_email@some_mail.ru"},
    {"phone": {79175002040}, "email": "some_email@some_mail.ru"},
    {"phone": [79175002040], "email": "some_email@some_mail.ru"},
    {"phone": [], "email": "some_email@some_mail.ru"},
    {"phone": "7917500204024", "email": "some_email@some_mail.ru"},
    {"phone": 791750020402, "email": "some_email@some_mail.ru"},
    {"phone": "7917500204", "email": "some_email@some_mail.ru"},
    {"phone": "791750020", "email": "some_email@some_mail.ru"},
    {"phone": "79175002", "email": "some_email@some_mail.ru"},
    {"phone": "7917500", "email": "some_email@some_mail.ru"},
    {"phone": "791750", "email": "some_email@some_mail.ru"},
    {"phone": "79175", "email": "some_email@some_mail.ru"},
    {"phone": "7917", "email": "some_email@some_mail.ru"},
    {"phone": "791", "email": "some_email@some_mail.ru"},
    {"phone": "79", "email": "some_email@some_mail.ru"},
    {"phone": "7", "email": "some_email@some_mail.ru"}
],
    ids=[
        "phone_11_numbers_as_str_in_set",
        "phone_11_numbers_in_set",
        "phone_11_numbers_in_list",
        "phone_empty_list",
        "phone_13_numbers_str",
        "phone_12_numbers_int",
        "phone_10_numbers",
        "phone_9_numbers",
        "phone_8_numbers",
        "phone_7_numbers",
        "phone_6_numbers",
        "phone_5_numbers",
        "phone_4_numbers",
        "phone_3_numbers",
        "phone_2_numbers",
        "phone_1_number"
    ])
def param_test_invalid_phone_score_request(request):
    return request.param


@pytest.fixture(scope="function", params=[
    {"gender": "MALE", "birthday": "01.01.2000"},
    {"gender": "FEMALE", "birthday": "01.01.2000"},
    {"gender": "not your business", "birthday": "01.01.2000"},
    {"gender": "", "birthday": "01.01.2000"},
    {"gender": [0, 1, 2], "birthday": "01.01.2000"},
    {"gender": {1, 2}, "birthday": "01.01.2000"},
    {"gender": ["male", "female"], "birthday": "01.01.2000"},
    {"gender": "male", "birthday": "01.01.2000"},
    {"gender": "female", "birthday": "01.01.2000"},
    {"gender": "1", "birthday": "01.01.2000"},
    {"gender": "0", "birthday": "01.01.2000"},
    {"gender": [], "birthday": "01.01.2000"}
], ids=[
    "gender_male_uppercase",
    "gender_female_uppercase",
    "gender_not_your_business",
    "gender_empty_string",
    "gender_all_possible_values_in_list",
    "gender_one_two_in_set",
    "gender_male_female_in_list",
    "gender_male_lowercase",
    "gender_female_lowercase",
    "gender_one_as_string",
    "gender_zero_as_string",
    "gender_empty_list"
])
def param_test_invalid_gender_score_request(request):
    return request.param


@pytest.fixture(scope="function", params=[
    {"gender": 2, "birthday": "01.01.1900"},
    {"gender": 2, "birthday": "01.30.1995"},
    {"gender": 2, "birthday": "1995.01.30"},
    {"gender": 2, "birthday": 10012000},
    {"gender": 2, "birthday": "long time ago"},
    {"gender": 2, "birthday": datetime.datetime.now().date() + relativedelta(days=1)},
    {"gender": 2, "birthday": datetime.datetime.now()},
    {"gender": 2, "birthday": (datetime.datetime.now().date() + relativedelta(years=-71)).strftime("%d%m%Y")},
    {"gender": 2, "birthday": (datetime.datetime.now().date() + relativedelta(days=1)).strftime("%d%m%Y")},
    {"gender": 2, "birthday": "yesterday"},
    {"gender": 2, "birthday": datetime.datetime.now().date() + relativedelta(years=-71)},
    {"gender": 2, "birthday": "tomorrow"}
], ids=[
    "january_first_1900",
    "date_format_day.month.year",
    "date_format_year.month.day",
    "date_format_as_integer",
    "long_time_ago",
    "current date plus one day as date",
    "current date as date",
    "71 years ago as string",
    "current date plus one day as string",
    "yesterday",
    "71 years ago as date",
    "tomorrow"
])
def param_test_invalid_birthday_score_request(request):
    return request.param


def test_invalid_score_request(param_test_invalid_score_request):

    """
    Tests invalid request for score
    """

    request = {
        "account": "horns&hoofs", "login": "h&f",
        "method": "online_score", "arguments": param_test_invalid_score_request
    }

    set_valid_auth(request)
    response, code = api.method_handler(
        request={"body": request, "headers": dict()},
        ctx=dict(),
        store=KeyValueTestStorage()
    )
    assert code == api.INVALID_REQUEST
    assert response


def test_ok_score_request(param_test_ok_score_request):

    """
    Tests ok score request
    """

    request = {
        "account": "horns&hoofs", "login": "h&f",
        "method": "online_score", "arguments": param_test_ok_score_request
    }

    set_valid_auth(request)
    test_context = dict()
    response, code = api.method_handler(
        request={"body": request, "headers": dict()},
        ctx=test_context,
        store=KeyValueTestStorage()
    )
    assert code == api.OK
    score = response.get("score")
    assert isinstance(score, (int, float)) and score >= 0
    assert sorted(test_context["has"]) == sorted(param_test_ok_score_request)


def test_ok_score_admin_request():

    """
    Tests ok request from admin
    """

    arguments = {"phone": "79175002040", "email": "stupnikov@otus.ru"}
    request = {"account": "horns&hoofs", "login": "admin", "method": "online_score", "arguments": arguments}
    test_context = dict()
    set_valid_auth(request)
    response, code = api.method_handler(
        request={"body": request, "headers": dict()},
        ctx=test_context,
        store=KeyValueTestStorage()
    )
    assert code == api.OK
    score = response.get("score")
    assert score == 42
    assert "has" in test_context
    assert len(test_context["has"]) == 2
    assert "phone" in test_context["has"]
    assert "email" in test_context["has"]


def test_invalid_phone_score_request(param_test_invalid_phone_score_request):

    """
    Tests invalid phone score request
    """
    request = {
        "account": "horns&hoofs", "login": "me",
        "method": "online_score", "arguments": param_test_invalid_phone_score_request
    }
    set_valid_auth(request)
    response, code = api.method_handler(
        request={"body": request, "headers": dict()},
        ctx=dict(),
        store=KeyValueTestStorage()
    )
    assert code == api.INVALID_REQUEST
    assert "error" in response
    errors = json.loads(response["error"])
    assert "phone" in errors
    assert len(errors) == 1


def test_invalid_gender_score_request(param_test_invalid_gender_score_request):

    """
    Tests invalid gender score request
    """

    request = {
        "account": "horns&hoofs", "login": "guess_my_gender",
        "method": "online_score", "arguments": param_test_invalid_gender_score_request
    }

    set_valid_auth(request)
    response, code = api.method_handler(
        request={"body": request, "headers": dict()},
        ctx=dict(),
        store=KeyValueTestStorage()
    )
    assert code == api.INVALID_REQUEST
    assert "error" in response
    errors = json.loads(response["error"])
    assert "gender" in errors
    print(errors)
    assert len(errors) == 1


def test_invalid_birthday_score_request(param_test_invalid_birthday_score_request):

    """
    Tests invalid birthday score request
    """

    request = {
        "account": "horns&hoofs", "login": "guess_my_birthday",
        "method": "online_score", "arguments": param_test_invalid_birthday_score_request
    }

    set_valid_auth(request)
    response, code = api.method_handler(
        request={"body": request, "headers": dict()},
        ctx=dict(),
        store=KeyValueTestStorage()
    )
    assert code == api.INVALID_REQUEST
    assert "error" in response
    errors = json.loads(response["error"])
    assert "birthday" in errors
    assert len(errors) == 1

