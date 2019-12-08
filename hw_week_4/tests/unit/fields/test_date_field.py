import pytest
from api import ClientsInterestsRequest


@pytest.fixture()
def clients_interests_request():
    return ClientsInterestsRequest(request_body={"test_body": "test"})


def test_integer_is_not_valid(clients_interests_request):

    """
    Tests if not valid types are detected in date field
    """

    with pytest.raises(TypeError):
        clients_interests_request.date = 42


def test_list_integers_is_not_valid(clients_interests_request):

    """
    Tests if not valid types are detected in date field
    """

    with pytest.raises(TypeError):
        clients_interests_request.date = [1, 2, 3]


def test_set_integers_is_not_valid(clients_interests_request):

    """
    Tests if not valid types are detected in date field
    """

    with pytest.raises(TypeError):
        clients_interests_request.date = {1, 2, 3}


def test_empty_dict_is_not_valid(clients_interests_request):

    """
    Tests if not valid types are detected in date field
    """

    with pytest.raises(TypeError):
        clients_interests_request.date = dict()


def test_byte_string_is_not_valid(clients_interests_request):

    """
    Tests if not valid types are detected in date field
    """

    with pytest.raises(TypeError):
        clients_interests_request.date = b"some_name"


def test_year_month_day_format_is_not_valid(clients_interests_request):

    with pytest.raises(ValueError):
        clients_interests_request.date = "2000.01.01"


def test_month_day_year_format_is_not_valid(clients_interests_request):

    with pytest.raises(ValueError):
        clients_interests_request.date = "01.13.2000"


def test_day_month_year_format_is_valid(clients_interests_request):

    test_valid_date_value = "13.01.2000"
    clients_interests_request.date = test_valid_date_value

    assert clients_interests_request.date == test_valid_date_value
