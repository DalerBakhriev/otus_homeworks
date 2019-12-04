import api
import pytest
from store import KeyValueTestStorage
from tests.utils import set_valid_auth


@pytest.fixture(scope="function", params=[
    {"account": "horns&hoofs", "login": "h&f", "method": "online_score", "token": "", "arguments": {}},
    {"account": "horns&hoofs", "login": "h&f", "method": "online_score", "token": "sdd", "arguments": {}},
    {"account": "horns&hoofs", "login": "admin", "method": "online_score", "token": "", "arguments": {}}
],
    ids=["empty_token_not_admin", "wrong_token_not_admin", "empty_token_admin"]
)
def param_test_bad_auth(request):
    return request.param


@pytest.fixture(scope="function", params=[
        {"account": "horns&hoofs", "login": "h&f", "method": "online_score"},
        {"account": "horns&hoofs", "login": "h&f", "arguments": {}},
        {"account": "horns&hoofs", "method": "online_score", "arguments": {}},
    ],
    ids=["no_arguments_for_method", "no_method_name", "no_login"]
)
def param_test_invalid_method_request(request):
    return request.param


def test_empty_request():

    """
    Tests response on empty body request
    """

    _, code = api.method_handler(
        request={"body": dict(), "headers": dict()},
        ctx=dict(),
        store=KeyValueTestStorage()
    )

    assert code == api.INVALID_REQUEST


def test_bad_auth(param_test_bad_auth):

    """
    Tests response on request with bad authorization token
    """

    _, code = api.method_handler(
        request={"body": param_test_bad_auth, "headers": dict()},
        ctx=dict(),
        store=KeyValueTestStorage()
    )
    assert code == api.FORBIDDEN


def test_invalid_method_request(param_test_invalid_method_request):

    """

    :param param_test_invalid_method_request:
    :return:
    """

    set_valid_auth(param_test_invalid_method_request)
    response, code = api.method_handler(
        request={"body": param_test_invalid_method_request, "headers": dict()},
        ctx=dict(),
        store=KeyValueTestStorage()
    )
    assert code == api.INVALID_REQUEST
    assert response
