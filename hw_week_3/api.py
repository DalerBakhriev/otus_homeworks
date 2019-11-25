from __future__ import annotations

import datetime
import hashlib
import json
import logging
import uuid
from http.server import HTTPServer, BaseHTTPRequestHandler
from optparse import OptionParser
from typing import Callable, Dict, List, Optional, Tuple, Union

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


class CharField:

    def __init__(self, required: bool, nullable: bool):

        self.required = required
        self.nullable = nullable

    def __get__(self, instance: Union[MethodRequest, OnlineScoreRequest], owner):
        return instance.__dict__.get(self.name, "")

    def __set__(self, instance: Union[MethodRequest, OnlineScoreRequest], value: str):

        if self.required and value is None:
            raise ValueError(f"Field {self.name} is required")

        if not self.nullable and value in ("", (), [], {}):
            raise ValueError(f"Field {self.name} is not nullable but empty value found")

        if value is not None and not isinstance(value, str):
            raise ValueError(f"value should be str, not {type(value)}")
        instance.__dict__[self.name] = value

    def __set_name__(self, owner, name: str):
        self.name = name

    def __add__(self, other: CharField) -> CharField:

        result = CharField(required=self.required, nullable=self.nullable)
        result_value = f"{self.__dict__[self.name]} {other.__dict__[self.name]}"
        result.__dict__[self.name] = result_value


class ArgumentsField:

    def __init__(self, required: bool, nullable: bool):

        self.required = required
        self.nullable = nullable

    def __get__(self, instance: MethodRequest, owner) -> Dict[str, Union[int, str]]:
        return instance.__dict__.get(self.name, dict())

    def __set__(self, instance: MethodRequest, arguments: Dict[str, Union[int, str]]):

        if self.required and arguments is None:
            raise ValueError(f"Field {self.name} is required")

        if not self.nullable and arguments in ("", (), [], {}):
            raise ValueError(f"Field {self.name} is not nullable but empty value found")
        instance.__dict__[self.name] = arguments

    def __set_name__(self, owner, name: str):
        self.name = name


class EmailField(CharField):

    def __set__(self, instance: OnlineScoreRequest, email: Optional[str]):

        if self.required and email is None:
            raise ValueError(f"Field {self.name} is required")

        if not self.nullable and email in ("", (), [], {}):
            raise ValueError(f"Field {self.name} is not nullable but empty value found")

        if email is not None and "@" not in email:
            raise ValueError("Email should contain @")
        instance.__dict__[self.name] = email


class PhoneField:

    PHONE_NUM_LENGTH = 11
    PHONE_NUM_START_VALUE = "7"

    def __init__(self, required: bool, nullable: bool):

        self.required = required
        self.nullable = nullable

    def __get__(self, instance: OnlineScoreRequest, owner) -> Union[int, str]:
        return instance.__dict__[self.name]

    def __set__(self, instance: OnlineScoreRequest, phone_num: Optional[Union[int, str]]):

        if self.required and phone_num is None:
            raise ValueError(f"Field {self.name} is required")

        if not self.nullable and phone_num in ("", (), [], {}):
            raise ValueError(f"Field {self.name} is not nullable but empty value found")

        if phone_num is not None:
            if not isinstance(phone_num, (int, str)):
                raise ValueError("Phone number should be one of int, str, not %s", str(type(phone_num)))

            if (phone_num_len := len(str(phone_num))) != PhoneField.PHONE_NUM_LENGTH:
                raise ValueError(
                    f"Phone number length should be {PhoneField.PHONE_NUM_LENGTH}, not {phone_num_len}"
                )

            if not (phone_num_str := str(phone_num)).startswith(PhoneField.PHONE_NUM_START_VALUE):
                raise ValueError(
                    "Phone number length should start with %s, not %s",
                    PhoneField.PHONE_NUM_START_VALUE,
                    phone_num_str[0]
                )
        instance.__dict__[self.name] = phone_num

    def __set_name__(self, owner, name: str):
        self.name = name


class DateField:

    def __init__(self, required: bool, nullable: bool):

        self.required = required
        self.nullable = nullable

    def __get__(self, instance: ClientsInterestsRequest, owner) -> str:
        return instance.__dict__[self.name]

    def __set__(self, instance: ClientsInterestsRequest, date_value: Optional[str]):

        if self.required and date_value is None:
            raise ValueError(f"Field {self.name} is required")

        if not self.nullable and date_value in ("", (), [], {}):
            raise ValueError(f"Field {self.name} is not nullable but empty value found")

        if date_value is not None:
            datetime.datetime.strptime(date_value, DATE_FORMAT)
        instance.__dict__[self.name] = date_value

    def __set_name__(self, owner, name: str):
        self.name = name


class BirthDayField:

    MAX_YEARS_AGO = 70

    def __init__(self, required: bool, nullable: bool):

        self.required = required
        self.nullable = nullable

    def __get__(self, instance: OnlineScoreRequest, owner) -> str:
        return instance.__dict__[self.name]

    def __set__(self, instance: OnlineScoreRequest, birthday: Optional[str]):

        if self.required and birthday is None:
            raise ValueError(f"Field {self.name} is required")

        if not self.nullable and birthday in ("", (), [], {}):
            raise ValueError(f"Field {self.name} is not nullable but empty value found")

        if birthday is not None:
            date_max_years_ago = datetime.datetime.now() + relativedelta(years=-BirthDayField.MAX_YEARS_AGO)
            if datetime.datetime.strptime(birthday, DATE_FORMAT) < date_max_years_ago:
                raise ValueError("Birth date should be later than 70 years ago")
        instance.__dict__[self.name] = birthday

    def __set_name__(self, owner, name: str):
        self.name = name


class GenderField:

    def __init__(self, required: bool, nullable: bool):

        self.required = required
        self.nullable = nullable

    def __get__(self, instance: OnlineScoreRequest, owner) -> int:
        return instance.__dict__[self.name]

    def __set__(self, instance: OnlineScoreRequest, gender_value: Optional[int]):

        if gender_value is not None and gender_value not in GENDERS:
            raise ValueError(f"Value should be is one of {GENDERS}")
        instance.__dict__[self.name] = gender_value

    def __set_name__(self, owner, name: str):
        self.name = name


class ClientIDsField:

    def __init__(self, required: bool, nullable: bool = False):

        self.required = required
        self.nullable = nullable

    def __get__(self, instance: ClientsInterestsRequest, owner) -> List[int]:
        return instance.__dict__[self.name]

    def __set__(self, instance: ClientsInterestsRequest, client_ids: Optional[List[int]]):

        if self.required and client_ids is None:
            raise ValueError(f"Field {self.name} is required")

        if not self.nullable and client_ids in ("", (), [], {}):
            raise ValueError(f"Field {self.name} is not nullable but empty value found")

        client_ids = [] if client_ids is None else client_ids
        if not isinstance(client_ids, (list, tuple)):
            raise ValueError(f"client ids should be of type list, not {type(client_ids)}")

        if not client_ids:
            raise ValueError("Client ids should be not empty")

        for single_id in client_ids:
            if not isinstance(single_id, int):
                raise ValueError(f"Client id should be int, not {type(single_id)}")

        instance.__dict__[self.name] = client_ids

    def __set_name__(self, owner, name: str):
        self.name = name


class RequestMeta(type):

    FIELD_TYPES = (
        ClientIDsField, DateField,
        CharField, EmailField,
        PhoneField, BirthDayField,
        GenderField, ArgumentsField
    )

    def __new__(mcs, name, bases, attrs):

        fields = []
        attributes = list(attrs.items())
        for attr_name, attr_value in attributes:
            if isinstance(attr_value, RequestMeta.FIELD_TYPES):
                fields.append((attr_name, attr_value))

        attrs["fields"] = fields

        return super().__new__(mcs, name, bases, attrs)


class BaseRequest(metaclass=RequestMeta):

    def __init__(self, request_body: Dict[str, Union[List[int], Optional[str]]]):

        self.request_body = request_body

    def _validate_form(self) -> Dict[str, str]:

        """
        Validates form values
        :return:
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
        :return:
        """

        validation_errors = self._validate_form()
        if not validation_errors:
            return True, None

        return False, json.dumps(validation_errors)


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

        return False, json.dumps(validation_errors)


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


def get_request_method(method_request: MethodRequest) -> Callable:

    """
    Gets method from method request
    :param method_request: method request
    :return:
    """

    method = ClientsInterestsRequest if method_request.method == "clients_interests" else OnlineScoreRequest

    return method


def method_handler(request: Dict[str, Union[int, str]],
                   ctx,
                   store):

    method_request = MethodRequest(request_body=request["body"])

    # Validate request method
    request_method_is_valid, request_method_errors = method_request.is_valid()
    if not request_method_is_valid:
        code = INVALID_REQUEST
        response = {"code": code, "error": request_method_errors}
        return response, code

    # Check authorization
    if not check_auth(request=method_request):
        code = FORBIDDEN
        response = {"code": code, "error": "Forbidden"}
        return response, code

    # Get method
    method = get_request_method(method_request=method_request)
    concrete_method = method(request_body=method_request.arguments)
    concrete_method_is_valid, concrete_method_errors = concrete_method.is_valid()

    if not concrete_method_is_valid:
        code = INVALID_REQUEST
        response = {"code": code, "error": concrete_method_errors}
        return response, code

    if isinstance(concrete_method, OnlineScoreRequest):

        score = 42 if method_request.is_admin else get_score(
            store=store,
            email=concrete_method.email,
            birthday=concrete_method.birthday,
            gender=concrete_method.gender,
            first_name=concrete_method.first_name,
            last_name=concrete_method.last_name,
            phone=concrete_method.phone
        )
        code = OK
        response = {"score": score}
        ctx["has"] = [
            field_val[0] for field_val in concrete_method.fields
            if concrete_method.__dict__.get(field_val[0]) is not None
        ]

    else:
        response = {
            client_id: get_interests(store=store, cid=client_id) for client_id in concrete_method.client_ids
        }
        code = OK
        ctx["nclients"] = len(concrete_method.client_ids)

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
                    response, code = self.router[path]({"body": request, "headers": self.headers}, context, self.store)
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
