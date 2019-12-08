import pytest
from api import ClientsInterestsRequest


@pytest.fixture(scope="function")
def clients_interests_request():
    return ClientsInterestsRequest(request_body={"test_body": "test"})


def test_integer_is_not_valid(clients_interests_request):

    """
    Tests if not valid types are detected in client_ids field
    """

    with pytest.raises(ValueError):
        clients_interests_request.client_ids = 42


def test_set_integers_is_not_valid(clients_interests_request):

    """
    Tests if not valid types are detected in client_ids field
    """

    with pytest.raises(ValueError):
        clients_interests_request.client_ids = {1, 2, 3}


def test_empty_dict_is_not_valid(clients_interests_request):

    """
    Tests if not valid types are detected in client_ids field
    """

    with pytest.raises(ValueError):
        clients_interests_request.client_ids = dict()


def test_byte_string_is_not_valid(clients_interests_request):

    """
    Tests if not valid types are detected in client_ids field
    """

    with pytest.raises(ValueError):
        clients_interests_request.client_ids = b"some_name"


def test_list_with_at_least_one_string_is_not_valid(clients_interests_request):

    """
    Tests if at least one value in list is not integer type
    then value is invalid
    """

    with pytest.raises(ValueError):
        clients_interests_request.client_ids = [1, 2, "3"]


def test_tuple_with_at_least_one_string_is_not_valid(clients_interests_request):

    """
    Tests if at least one value in tuple is not integer type
    then value is invalid
    """

    with pytest.raises(ValueError):
        clients_interests_request.client_ids = (1, 2, "3")


def test_list_integers_is_valid(clients_interests_request):

    """
    Tests if list of integers is valid type for client_ids field
    """

    test_valid_client_ids_value = [1, 2, 3]
    clients_interests_request.client_ids = test_valid_client_ids_value
    assert clients_interests_request.client_ids == test_valid_client_ids_value


def test_tuple_integers_is_valid(clients_interests_request):

    """
    Tests if tuple of integers is valid type for client_ids field
    """

    test_valid_client_ids_value = (1, 2, 3)
    clients_interests_request.client_ids = test_valid_client_ids_value
    assert clients_interests_request.client_ids == test_valid_client_ids_value
