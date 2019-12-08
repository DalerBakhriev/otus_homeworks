import pytest
from api import OnlineScoreRequest


@pytest.fixture(scope="function")
def score_request():
    return OnlineScoreRequest(request_body={"test_body": "test"})


def test_length_less_than_eleven_int_is_not_valid(score_request):

    """
    Tests if not valid types are detected in phone field
    """

    with pytest.raises(ValueError):
        score_request.phone = 72


def test_length_less_than_eleven_str_is_not_valid(score_request):

    """
    Tests if not valid types are detected in phone field
    """

    with pytest.raises(ValueError):
        score_request.phone = "72"


def test_list_integers_is_not_valid(score_request):

    """
    Tests if not valid types are detected in phone field
    """

    with pytest.raises(ValueError):
        score_request.phone = [1, 2, 3]


def test_set_integers_is_not_valid(score_request):

    """
    Tests if not valid types are detected in phone field
    """

    with pytest.raises(ValueError):
        score_request.phone = {1, 2, 3}


def test_empty_dict_is_not_valid(score_request):

    """
    Tests if not valid types are detected in phone field
    """

    with pytest.raises(ValueError):
        score_request.phone = dict()


def test_byte_string_is_not_valid(score_request):

    """
    Tests if not valid types are detected in phone field
    """

    with pytest.raises(ValueError):
        score_request.phone = b"some_name"


def test_not_starts_with_seven_int_is_not_valid(score_request):

    """
    Tests if phone num not starts with 7 and type is integer
    field is not valid
    """

    with pytest.raises(ValueError):
        score_request.phone = 89999999999


def test_not_starts_with_seven_str_is_not_valid(score_request):

    """
    Tests if phone num not starts with 7 field and type is str
    field is not valid
    """

    with pytest.raises(ValueError):
        score_request.phone = "89999999999"


def test_valid_phone_number_str(score_request):

    """
    Tests valid phone number value as string
    """

    test_valid_phone_num_str = "79999999999"
    score_request.phone = test_valid_phone_num_str

    assert score_request.phone == test_valid_phone_num_str


def test_valid_phone_number_int(score_request):

    """
    Tests valid phone number value as int
    """

    test_valid_phone_num_int = 79999999999
    score_request.phone = test_valid_phone_num_int

    assert score_request.phone == test_valid_phone_num_int
