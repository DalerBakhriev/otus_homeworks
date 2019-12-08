import pytest
from api import MethodRequest


@pytest.fixture(scope="function")
def method_request():
    return MethodRequest(request_body={"test_body": "test"})


def test_integer_is_not_valid(method_request):

    """
    Tests if not valid types are detected in arguments field
    """

    with pytest.raises(ValueError):
        method_request.arguments = 42


def test_list_integers_is_not_valid(method_request):

    """
    Tests if not valid types are detected in arguments field
    """

    with pytest.raises(ValueError):
        method_request.arguments = [1, 2, 3]


def test_set_integers_is_not_valid(method_request):

    """
    Tests if not valid types are detected in arguments field
    """

    with pytest.raises(ValueError):
        method_request.arguments = {1, 2, 3}


def test_empty_dict_is_valid(method_request):

    """
    Tests if not valid types are detected in arguments field
    """

    method_request.arguments = dict()
    assert method_request.arguments == dict()


def test_byte_string_is_not_valid(method_request):

    """
    Tests if not valid types are detected in arguments field
    """

    with pytest.raises(ValueError):
        method_request.arguments = b"some_name"


def test_none_is_not_valid(method_request):

    """
    Tests if not valid types are detected in arguments field
    """

    with pytest.raises(ValueError):
        method_request.arguments = None
