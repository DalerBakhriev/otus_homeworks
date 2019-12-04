from __future__ import annotations

import datetime
import hashlib
import json
import logging
import uuid
from http.server import HTTPServer, BaseHTTPRequestHandler
from optparse import OptionParser
from typing import (
    Callable,
    Dict,
    List,
    Optional,
    Tuple,
    Union
)

from dateutil.relativedelta import relativedelta

from scoring import get_score, get_interests

SALT = "Otus"
ADMIN_LOGIN = "admin"
ADMIN_SALT = "42"
OK = 200
BAD_REQUEST = 400
FORBIDDEN = 403
NOT_FOUND = 404
INVALID_REQUEST = 422
INTERNAL_ERROR = 500
ERRORS = {
    BAD_REQUEST: "Bad Request",
    FORBIDDEN: "Forbidden",
    NOT_FOUND: "Not Found",
    INVALID_REQUEST: "Invalid Request",
    INTERNAL_ERROR: "Internal Server Error",
}
UNKNOWN = 0
MALE = 1
FEMALE = 2
GENDERS = {
    UNKNOWN: "unknown",
    MALE: "male",
    FEMALE: "female",
}
DATE_FORMAT = "%d.%m.%Y"


class BaseField:

    """
    Base class for all fields
    """

    def __init__(self, required: bool, nullable: bool):

        self.required = required
        self.nullable = nullable

    def __get__(self, instance, owner):
        return instance.__dict__[self.name]

    def __set_name__(self, owner, name: str):
        self.name = name

    def _check_required_and_nullable(self, value):

        """
        Checks required and nullable fields and values
        """

        if self.required and value is None:
            raise ValueError(f"Field {self.name} is required")

        if not self.nullable and value in ("", (), [], {}):
            raise ValueError(f"Field {self.name} is not nullable but empty value found")


class CharField(BaseField):

    def __set__(self, instance: Union[MethodRequest, OnlineScoreRequest], value: str):

        self._check_required_and_nullable(value)
        if value is not None and not isinstance(value, str):
            raise ValueError(f"value should be str, not {type(value)}")
        instance.__dict__[self.name] = value

    def __add__(self, other: CharField) -> CharField:

        result = CharField(required=self.required, nullable=self.nullable)
        result_value = f"{self.__dict__[self.name]} {other.__dict__[self.name]}"
        result.__dict__[self.name] = result_value


class ArgumentsField(BaseField):

    def __get__(self, instance: MethodRequest, owner) -> Dict[str, Union[int, str]]:
        return instance.__dict__.get(self.name, dict())

    def __set__(self, instance: MethodRequest, arguments: Dict[str, Union[int, str]]):

        self._check_required_and_nullable(value=arguments)
        instance.__dict__[self.name] = arguments


class EmailField(CharField):

    def __set__(self, instance: OnlineScoreRequest, email: Optional[str]):

        self._check_required_and_nullable(value=email)

        if email is not None and "@" not in email:
            raise ValueError("Email should contain @")
        instance.__dict__[self.name] = email


class PhoneField(BaseField):

    PHONE_NUM_LENGTH = 11
    PHONE_NUM_START_VALUE = "7"

    def __set__(self, instance: OnlineScoreRequest, phone_num: Optional[Union[int, str]]):

        self._check_required_and_nullable(value=phone_num)

        if phone_num is not None:
            if not isinstance(phone_num, (int, str)):
                raise ValueError(
                    f"Phone number should be one of int, str, not {type(phone_num)}",
                )

            if (phone_num_len := len(str(phone_num))) != PhoneField.PHONE_NUM_LENGTH:
                raise ValueError(
                    f"Phone number length should be "
                    f"{PhoneField.PHONE_NUM_LENGTH}, not {phone_num_len}"
                )

            if not (phone_num_str := str(phone_num)).startswith(PhoneField.PHONE_NUM_START_VALUE):
                raise ValueError(
                    f"Phone number length should start with "
                    f"{PhoneField.PHONE_NUM_START_VALUE}, not {phone_num_str[0]}",
                )
        instance.__dict__[self.name] = phone_num


class DateField(BaseField):

    def __set__(self, instance: ClientsInterestsRequest, date_value: Optional[str]):

        self._check_required_and_nullable(value=date_value)

        if date_value is not None:
            datetime.datetime.strptime(date_value, DATE_FORMAT)
        instance.__dict__[self.name] = date_value


class BirthDayField(DateField):

    MAX_YEARS_AGO = 70

    def __set__(self, instance: OnlineScoreRequest, birthday: Optional[str]):

        self._check_required_and_nullable(value=birthday)

        if birthday is not None:

            current_date = datetime.datetime.today()
            birthday_as_date = datetime.datetime.strptime(birthday, DATE_FORMAT)
            date_max_years_ago = datetime.datetime.today() + relativedelta(years=-BirthDayField.MAX_YEARS_AGO)

            if birthday_as_date < date_max_years_ago:
                raise ValueError("Birth date should be later than 70 years ago")
            if birthday_as_date > current_date:
                raise ValueError(
                    f"Birth date can't be later than current date: {current_date}"
                )
        instance.__dict__[self.name] = birthday


class GenderField(BaseField):

    def __set__(self, instance: OnlineScoreRequest, gender_value: Optional[int]):

        self._check_required_and_nullable(value=gender_value)

        if gender_value is not None and gender_value not in GENDERS:
            raise ValueError(f"Value should be is one of {GENDERS}")
        instance.__dict__[self.name] = gender_value


class ClientIDsField(BaseField):

    def __init__(self, required: bool, nullable: bool = False):

        super().__init__(required, nullable)

    def __set__(self, instance: ClientsInterestsRequest, client_ids: Optional[List[int]]):

        self._check_required_and_nullable(value=client_ids)

        client_ids = [] if client_ids is None else client_ids
        if not isinstance(client_ids, (list, tuple)):
            raise ValueError(f"client ids should be of type list, not {type(client_ids)}")

        if not client_ids:
            raise ValueError("Client ids should be not empty")

        for single_id in client_ids:
            if not isinstance(single_id, int):
                raise ValueError(f"Client id should be int, not {type(single_id)}")

        instance.__dict__[self.name] = client_ids


class RequestMeta(type):

    def __new__(mcs, name, bases, attrs):

        fields = []
        attributes = list(attrs.items())
        for attr_name, attr_value in attributes:
            if isinstance(attr_value, BaseField):
                fields.append((attr_name, attr_value))

        attrs["fields"] = fields

        return super().__new__(mcs, name, bases, attrs)


class BaseRequest(metaclass=RequestMeta):

    def __init__(self, request_body: Dict[str, Union[List[int], Optional[str]]]):

        self.request_body = request_body

    def _validate_form(self) -> Dict[str, str]:

        """
        Validates form values
        """

        validation_errors = dict()
        for field_name, field_ in self.fields:
            try:
                field_request_value = self.request_body.get(field_name)
                setattr(self, field_name, field_request_value)
            except Exception as exc:
                validation_errors[field_name] = str(exc)

        return validation_errors

    def is_valid(self) -> Tuple[bool, Optional[str]]:

        """
        Checks if request is valid
        """

        validation_errors = self._validate_form()
        if not validation_errors:
            return True, None

        return False, validation_errors


class ClientsInterestsRequest(BaseRequest):

    client_ids = ClientIDsField(required=True)
    date = DateField(required=False, nullable=True)


class OnlineScoreRequest(BaseRequest):

    first_name = CharField(required=False, nullable=True)
    last_name = CharField(required=False, nullable=True)
    email = EmailField(required=False, nullable=True)
    phone = PhoneField(required=False, nullable=True)
    birthday = BirthDayField(required=False, nullable=True)
    gender = GenderField(required=False, nullable=True)

    def is_valid(self) -> Tuple[bool, Optional[str]]:

        """
        Checks if request is valid.
        Request is valid if every single field is valid
        and at least one pair of fields (phone-mail, first_name-last_name, gender-birthday)
        is not empty
        :return: boolean if request is valid and error text if it is not valid
        """

        validation_errors = self._validate_form()
        if not validation_errors:
            if self.phone and self.email:
                return True, None
            elif self.first_name and self.last_name:
                return True, None
            elif self.gender is not None and self.birthday:
                return True, None
            return False, "No required fields found together"

        return False, validation_errors


class MethodRequest(BaseRequest):

    account = CharField(required=False, nullable=True)
    login = CharField(required=True, nullable=True)
    token = CharField(required=True, nullable=True)
    arguments = ArgumentsField(required=True, nullable=True)
    method = CharField(required=True, nullable=False)

    @property
    def is_admin(self):
        return self.login == ADMIN_LOGIN


def check_auth(request: MethodRequest):

    if request.is_admin:
        digest = hashlib.sha512(
            (datetime.datetime.now().strftime("%Y%m%d%H") + ADMIN_SALT).encode("utf-8")
        ).hexdigest()
    else:
        digest = hashlib.sha512(
            (request.account + request.login + SALT).encode("utf-8")
        ).hexdigest()
    if digest == request.token:
        return True

    return False


def handle_request_method(method_request: MethodRequest,
                          store,
                          context) -> Callable:

    """
    Handles method from method request
    """
    ADMIN_SCORE_RESPONSE = 42

    if method_request.method == "clients_interests":

        client_interests_request = ClientsInterestsRequest(request_body=method_request.arguments)
        request_is_valid, errors = client_interests_request.is_valid()
        if not request_is_valid:
            code = INVALID_REQUEST
            return errors, code
        response = {
            client_id: get_interests(store=store, client_id=client_id)
            for client_id in client_interests_request.client_ids
        }
        code = OK
        context["nclients"] = len(client_interests_request.client_ids)
        return response, code

    elif method_request.method == "online_score":

        online_score_request = OnlineScoreRequest(request_body=method_request.arguments)
        request_is_valid, errors = online_score_request.is_valid()
        if not request_is_valid:
            code = INVALID_REQUEST
            return errors, code

        score = ADMIN_SCORE_RESPONSE if method_request.is_admin else get_score(
            store=store,
            email=online_score_request.email,
            birthday=online_score_request.birthday,
            gender=online_score_request.gender,
            first_name=online_score_request.first_name,
            last_name=online_score_request.last_name,
            phone=online_score_request.phone
        )
        code = OK
        response = {"score": score}
        context["has"] = [
            field_val[0] for field_val in online_score_request.fields
            if online_score_request.__dict__.get(field_val[0]) is not None
        ]
        return response, code

    else:
        return "Unknown method", INVALID_REQUEST


def method_handler(request: Dict[str, Union[int, str]],
                   ctx,
                   store):

    method_request = MethodRequest(request_body=request["body"])

    # Validate request method
    request_method_is_valid, request_method_errors = method_request.is_valid()
    if not request_method_is_valid:
        code = INVALID_REQUEST
        return request_method_errors, code

    # Check authorization
    if not check_auth(request=method_request):
        code = FORBIDDEN
        return "Forbidden", code

    # Get method
    response, code = handle_request_method(
        method_request=method_request,
        context=ctx,
        store=store
    )

    return response, code


class MainHTTPHandler(BaseHTTPRequestHandler):
    router = {
        "method": method_handler
    }
    store = None

    @staticmethod
    def get_request_id(headers):
        return headers.get('HTTP_X_REQUEST_ID', uuid.uuid4().hex)

    def do_POST(self):

        response, code = dict(), OK
        context = {"request_id": self.get_request_id(self.headers)}
        request = None
        try:
            data_string = self.rfile.read(int(self.headers['Content-Length']))
            request = json.loads(data_string)
        except:
            code = BAD_REQUEST

        if request:
            path = self.path.strip("/")
            logging.info("%s: %s %s" % (self.path, data_string, context["request_id"]))
            if path in self.router:
                try:
                    response, code = self.router[path](
                        {"body": request, "headers": self.headers}, context, self.store
                    )
                except Exception as e:
                    logging.exception("Unexpected error: %s" % e)
                    code = INTERNAL_ERROR
            else:
                code = NOT_FOUND

        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        if code not in ERRORS:
            r = {"response": response, "code": code}
        else:
            r = {"error": response or ERRORS.get(code, "Unknown Error"), "code": code}
        context.update(r)
        logging.info(context)
        self.wfile.write(json.dumps(r))
        return


if __name__ == "__main__":

    op = OptionParser()
    op.add_option("-p", "--port", action="store", type=int, default=8080)
    op.add_option("-l", "--log", action="store", default=None)
    opts, args = op.parse_args()
    logging.basicConfig(
        filename=opts.log,
        level=logging.INFO,
        format='[%(asctime)s] %(levelname).1s %(message)s',
        datefmt='%Y.%m.%d %H:%M:%S'
    )
    server = HTTPServer(("localhost", opts.port), MainHTTPHandler)
    logging.info("Starting server at %s" % opts.port)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    server.server_close()
