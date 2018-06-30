#!/usr/bin/env python
# -*- coding: utf-8 -*-

from abc import ABC, abstractclassmethod
import json
import datetime
import logging
import hashlib
import uuid
from weakref import WeakKeyDictionary
from optparse import OptionParser
from http.server import HTTPServer, BaseHTTPRequestHandler
import scoring

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

REQUIRED_FIELD_ERROR = "Field {} is requeired"
NON_NULLABLE_FIELD_ERROR = "Field {} must be non nullable"


class ValidationError(Exception):
    def __init__(self, msg):
        super().__init__(msg)


class Field(ABC):

    def __init__(self, required=False, nullable=True):
        self.required = required
        self.nullable = nullable
        self.data = WeakKeyDictionary()

    def __get__(self, instance, owner):
        return self.data.get(instance, None)

    def __set__(self, instance, value):
        # if not self._is_null(value):
        self.data[instance] = value
        # else:
        #     self.data[instance] = None

    def error_message(self):
        return 'Field "{}" is not valid'.format(self.field_name)

    def is_null(self, instance):
        value = self.data.get(instance)
        return self._is_null(value)

    def is_set(self, instance):
        return instance in self.data

    def validate(self, instance):
        if not self.is_set(instance):
            if self.required:
                raise ValidationError(REQUIRED_FIELD_ERROR.format(self.field_name))

        value = self.data.get(instance)
        if self._is_null(value):
            if not self.nullable:
                raise ValidationError(NON_NULLABLE_FIELD_ERROR.format(self.field_name))

        self.validate_value(value)

    @abstractclassmethod
    def validate_value(self, value):
        return NotImplemented

    @staticmethod
    def _is_null(value):
        if value is None:
            return True

        # TODO: поправить это место
        if isinstance(value, str) or isinstance(value, dict) or isinstance(value, list):
            return len(value) == 0

        return False


class CharField(Field):

    def validate_value(self, value):
        if self.nullable:
            if value == '' or value is None:
                return
        if not isinstance(value, str):
            raise ValidationError(self.error_message())


class ArgumentsField(Field):

    def validate_value(self, value):
        if self.nullable and value is None:
            return
        if not isinstance(value, dict):
            raise ValidationError(self.error_message())


class EmailField(CharField):

    def validate_value(self, value):
        if self.nullable and (value is None or value == ''):
            return
        if not isinstance(value, str):
            raise ValidationError("{} is not email string".format(self.field_name))
        splitted = value.split('@')
        if len(splitted) != 2 or len(splitted[0]) == 0 or len(splitted[1]) == 0:
            raise ValidationError("{} must be email value with '@' ".format(self.field_name))


class PhoneField(Field):

    def validate_value(self, value):
        if self.nullable and (value is None or value == ''):
            return
        if isinstance(value, int):
            value = str(value)
        error = "{} must be 11 symbol number/string starting with 7".format(self.field_name)
        if not isinstance(value, str) or len(value) != 11 or value[0] != '7':
            raise ValidationError(error)


class DateField(Field):

    def validate_value(self, value):
        return


class BirthDayField(Field):

    def validate_value(self, value):
        if self.nullable and (value == '' or value is None):
            return
        if not isinstance(value, str):
            raise ValidationError(self.error_message())

        try:
            date_value = datetime.datetime.strptime(value, '%d.%m.%Y')
            date_value = date_value.date()
        except ValueError:
            raise ValidationError(self.error_message())

        date_delta = datetime.datetime.now().date() - date_value
        if date_delta.days / 365 > 70:
            raise ValidationError(self.error_message())


class GenderField(Field):

    def validate_value(self, value):
        if self.nullable and value is None:
            return

        if not isinstance(value, int) or value not in (0, 1, 2):
            raise ValidationError('Field "{}" is not valid'.format(self.field_name))


class ClientIDsField(Field):

    def validate_value(self, value):
        if self.nullable and value is None:
            return
        error = 'Field "{}" is not valid'.format(self.field_name)
        if not isinstance(value, list):
            raise ValidationError(error)

        for item in value:
            if not isinstance(item, int):
                raise ValidationError('Field "{}" is not valid'.format(self.field_name))


class RequestMeta(type):

    def __init__(mcs, name, bases, attrs):
        super().__init__(name, bases, attrs)
        fields = []
        for item, value in attrs.items():
            if isinstance(value, Field):
                value.field_name = item
                fields.append((item, value))
        mcs.fields = fields


class Request(metaclass=RequestMeta):

    def __init__(self, values):
        self.__errors = None
        for key, value in values.items():
            if hasattr(self, key):
                setattr(self, key, value)

    def all_data(self):
        data = {}
        for field_name, field in self.fields:
            data[field_name] = getattr(self, field_name)
        return data

    def clean_data(self):
        data = {}
        for field_name, field in self.fields:
            if field.is_set(self):
                data[field_name] = getattr(self, field_name)
        return data

    def is_valid(self):
        errors = []
        for field_name, field in self.fields:
            try:
                field.validate(self)
            except ValidationError as ex:
                errors.append(str(ex))

        # Start 'validate' only when all fields are valid
        if len(errors) == 0:
            try:
                self.validate()
            except ValidationError as ex:
                errors.append(str(ex))

        self.__errors = errors if len(errors) > 0 else None
        return self.__errors is None

    def errors(self):
        return self.__errors.copy()

    def validate(self):
        return NotImplemented


class ClientsInterestsRequest(Request):
    client_ids = ClientIDsField(required=True)
    date = DateField(required=False, nullable=True)

    def validate(self):
        return True

    @staticmethod
    def handle(request, ctx):
        pass


class OnlineScoreRequest(Request):
    first_name = CharField(required=False, nullable=True)
    last_name = CharField(required=False, nullable=True)
    email = EmailField(required=False, nullable=True)
    phone = PhoneField(required=False, nullable=True)
    birthday = BirthDayField(required=False, nullable=True)
    gender = GenderField(required=False, nullable=True)

    def validate(self):
        data = self.clean_data()

        if 'phone' in data and 'email' in data:
            return
        elif 'first_name' in data and 'last_name' in data:
            return
        elif 'gender' in data and 'birthday' in data:
            return

        raise ValidationError('No full pair in request')

    @staticmethod
    def handle(request, ctx, store):
        method = OnlineScoreRequest(request.arguments)

        if not method.is_valid():
            errors = method.errors()
            return ';'.join(errors), INVALID_REQUEST

        ctx['has'] = method.clean_data().keys()

        if request.is_admin:
            return {'score': 42}, OK

        data = method.all_data()
        return {'score': scoring.get_score(store, **data)}, OK


class MethodRequest(Request):
    account = CharField(required=False, nullable=True)
    login = CharField(required=True, nullable=True)
    token = CharField(required=True, nullable=True)
    arguments = ArgumentsField(required=True, nullable=True)
    method = CharField(required=True, nullable=False)

    def validate(self):
        return True

    @property
    def is_admin(self):
        return self.login == ADMIN_LOGIN


def check_auth(request):
    if request.is_admin:
        digest = hashlib.sha512((datetime.datetime.now().strftime("%Y%m%d%H") + ADMIN_SALT).encode('utf-8   ')).hexdigest()
    else:
        digest = hashlib.sha512((request.account + request.login + SALT).encode('utf-8')).hexdigest()
    if digest == request.token:
        return True
    return False


def method_handler(request, ctx, store):
    router = {
        'online_score': OnlineScoreRequest,
        'client_interests': ClientsInterestsRequest
    }

    body = request['body']

    method_request = MethodRequest(body)

    if not method_request.is_valid():
        return ';'.join(method_request.errors()), INVALID_REQUEST

    if not check_auth(method_request):
        return ERRORS[FORBIDDEN], FORBIDDEN

    concrete_method_class = router[method_request.method]
    response, code = concrete_method_class.handle(method_request, ctx, store)

    return response, code


class MainHTTPHandler(BaseHTTPRequestHandler):
    router = {
        "method": method_handler
    }
    store = None

    def get_request_id(self, headers):
        return headers.get('HTTP_X_REQUEST_ID', uuid.uuid4().hex)

    def do_POST(self):
        response, code = {}, OK
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
    (opts, args) = op.parse_args()
    logging.basicConfig(filename=opts.log, level=logging.INFO,
                        format='[%(asctime)s] %(levelname).1s %(message)s', datefmt='%Y.%m.%d %H:%M:%S')
    server = HTTPServer(("localhost", opts.port), MainHTTPHandler)
    logging.info("Starting server at %s" % opts.port)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    server.server_close()
