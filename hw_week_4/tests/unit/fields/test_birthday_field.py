import pytest
import datetime
from dateutil.relativedelta import relativedelta
from api import OnlineScoreRequest


@pytest.fixture()
def score_request():
    return OnlineScoreRequest(request_body={"test_body": "test"})


def test_integer_is_not_valid(score_request):

    """
    Tests if not valid types are detected in birthday field
    """

    with pytest.raises(TypeError):
        score_request.birthday = 42


def test_list_integers_is_not_valid(score_request):

    """
    Tests if not valid types are detected in birthday field
    """

    with pytest.raises(TypeError):
        score_request.birthday = [1, 2, 3]


def test_set_integers_is_not_valid(score_request):

    """
    Tests if not valid types are detected in birthday field
    """

    with pytest.raises(TypeError):
        score_request.birthday = {1, 2, 3}


def test_empty_dict_is_not_valid(score_request):

    """
    Tests if not valid types are detected in birthday field
    """

    with pytest.raises(TypeError):
        score_request.birthday = dict()


def test_byte_string_is_not_valid(score_request):

    """
    Tests if not valid types are detected in birthday field
    """

    with pytest.raises(TypeError):
        score_request.birthday = b"some_name"


def test_year_month_day_format_is_not_valid(score_request):

    with pytest.raises(ValueError):
        score_request.birthday = "2000.01.01"


def test_month_day_year_format_is_not_valid(score_request):

    with pytest.raises(ValueError):
        score_request.birthday = "01.13.2000"


def test_birthday_from_future_is_not_valid(score_request):

    """
    Tests that birthday with date from future is not valid
    """

    current_date = datetime.datetime.today()
    tomorrow_date = current_date + relativedelta(days=1)
    tomorrow_date_as_string = tomorrow_date.strftime("%d.%m.%Y")

    with pytest.raises(ValueError):
        score_request.birthday = tomorrow_date_as_string


def test_birthday_more_than_70_years_ago_is_not_valid(score_request):

    """
    Tests that birthday with date more than 70 years ago is not valid
    """

    current_date = datetime.datetime.today()
    more_than_seventy_years_ago_date = current_date + relativedelta(years=-70, days=-1)
    more_than_seventy_years_ago_date_as_string = more_than_seventy_years_ago_date.strftime("%d.%m.%Y")

    with pytest.raises(ValueError):
        score_request.birthday = more_than_seventy_years_ago_date_as_string


def test_birthday_exactly_70_years_ago_is_valid(score_request):

    """
    Tests that birthday with date exactly 70 years ago is valid
    """

    current_date = datetime.datetime.today()
    exactly_seventy_years_ago_date = current_date + relativedelta(years=-70)
    exactly_seventy_years_ago_date_as_string = exactly_seventy_years_ago_date.strftime("%d.%m.%Y")

    score_request.birthday = exactly_seventy_years_ago_date_as_string
    assert score_request.birthday == exactly_seventy_years_ago_date_as_string


def test_day_month_year_format_is_valid(score_request):

    test_valid_birthday_value = "13.01.2000"
    score_request.birthday = test_valid_birthday_value

    assert score_request.birthday == test_valid_birthday_value
