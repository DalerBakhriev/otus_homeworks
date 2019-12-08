import pytest
from api import OnlineScoreRequest


@pytest.fixture()
def score_request():
    return OnlineScoreRequest(request_body={"test_body": "test"})


def test_integer_except_zero_one_two_is_not_valid(score_request):

    """
    Tests if not valid types are detected in gender field
    """

    with pytest.raises(ValueError):
        score_request.gender = 3


def test_list_integers_is_not_valid(score_request):

    """
    Tests if not valid types are detected in gender field
    """

    with pytest.raises(TypeError):
        score_request.gender = [1, 2, 3]


def test_set_integers_is_not_valid(score_request):

    """
    Tests if not valid types are detected in gender field
    """

    with pytest.raises(TypeError):
        score_request.gender = {1, 2, 3}


def test_empty_dict_is_not_valid(score_request):

    """
    Tests if not valid types are detected in gender field
    """

    with pytest.raises(TypeError):
        score_request.gender = dict()


def test_byte_string_is_not_valid(score_request):

    """
    Tests if not valid types are detected in gender field
    """

    with pytest.raises(ValueError):
        score_request.gender = b"some_name"


def test_zero_one_or_two_are_valid_values(score_request):

    """
    Tests that zero, one or two are valid values for gender field
    """

    for valid_value in (0, 1, 1):
        score_request.gender = valid_value
        assert score_request.gender == valid_value
