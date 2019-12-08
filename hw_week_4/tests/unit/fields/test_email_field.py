import pytest
from api import OnlineScoreRequest


@pytest.fixture()
def score_request():
    return OnlineScoreRequest(request_body={"test_body": "test"})


def test_integer_is_not_valid(score_request):

    """
    Tests if not valid types are detected in char field
    """

    with pytest.raises(ValueError):
        score_request.email = 42


def test_list_integers_is_not_valid(score_request):

    """
    Tests if not valid types are detected in char field
    """

    with pytest.raises(ValueError):
        score_request.email = [1, 2, 3]


def test_set_integers_is_not_valid(score_request):

    """
    Tests if not valid types are detected in char field
    """

    with pytest.raises(ValueError):
        score_request.email = {1, 2, 3}


def test_empty_dict_is_not_valid(score_request):

    """
    Tests if not valid types are detected in char field
    """

    with pytest.raises(ValueError):
        score_request.email = dict()


def test_byte_string_is_not_valid(score_request):

    """
    Tests if not valid types are detected in char field
    """

    with pytest.raises(ValueError):
        score_request.email = b"some_email"


def test_string_without_at_sign_is_not_valid(score_request):

    """
    Tests if not valid types are detected in char field
    """

    with pytest.raises(ValueError):
        score_request.email = "some_email"


def test_string_with_at_sign_is_valid(score_request):

    """
    Tests if not valid types are detected in char field
    """

    valid_test_value = "some_first_name@some_host.ru"
    score_request.email = valid_test_value
    assert score_request.email == valid_test_value
