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
        score_request.first_name = 42


def test_list_integers_is_not_valid(score_request):

    """
    Tests if not valid types are detected in char field
    """

    with pytest.raises(ValueError):
        score_request.last_name = [1, 2, 3]


def test_set_integers_is_not_valid(score_request):

    """
    Tests if not valid types are detected in char field
    """

    with pytest.raises(ValueError):
        score_request.last_name = {1, 2, 3}


def test_empty_dict_is_not_valid(score_request):

    """
    Tests if not valid types are detected in char field
    """

    with pytest.raises(ValueError):
        score_request.last_name = dict()


def test_byte_string_is_not_valid(score_request):

    """
    Tests if not valid types are detected in char field
    """

    with pytest.raises(ValueError):
        score_request.last_name = b"some_name"


def test_string_is_valid(score_request):

    """
    Tests if not valid types are detected in char field
    """

    score_request.first_name = "some_first_name"
    score_request.last_name = "some_last_name"

    assert score_request.first_name == "some_first_name"
    assert score_request.last_name == "some_last_name"
