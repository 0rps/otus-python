#!/usr/bin/env python3

from abc import ABC, abstractclassmethod, ABCMeta
import json
import datetime
import logging
import hashlib
import uuid
from weakref import WeakKeyDictionary
from optparse import OptionParser
from http.server import HTTPServer, BaseHTTPRequestHandler

import store
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

REQUIRED_FIELD_ERROR = 'Field "{}" is required'
NON_NULLABLE_FIELD_ERROR = 'Field "{}" couldn\'t be null'


class ValidationError(Exception):
    pass


class Field(ABC):

    def __init__(self, required=False, nullable=False):
        self._required = required
        self._nullable = nullable
        self._data = WeakKeyDictionary()

    def __get__(self, instance, owner):
        return self._data.get(instance, None)

    def __set__(self, instance, value):
        if self.is_null_value(value):
            self._data[instance] = None
        else:
            self._data[instance] = value

    def is_set(self, instance):
        return instance in self._data

    def validate(self, instance):
        if self.is_set(instance):
            value = self._data.get(instance)
            if value is not None:
                value = self.validate_value(value)
                self._data[instance] = value
            elif not self._nullable:
                msg = NON_NULLABLE_FIELD_ERROR.format(self.field_name)
                raise ValidationError(msg)
        elif self._required:
            msg = REQUIRED_FIELD_ERROR.format(self.field_name)
            raise ValidationError(msg)

    @abstractclassmethod
    def validate_value(self, value):
        return NotImplemented

    @abstractclassmethod
    def is_null_value(self, value):
        return NotImplemented


class CharField(Field):

    def validate_value(self, value):
        if not isinstance(value, str):
            raise ValidationError('Field "{}"'
                                  ' is not string'.format(self.field_name))
        return value

    def is_null_value(self, value):
        return value is None or value == ''


class ArgumentsField(Field):

    def validate_value(self, value):
        if not isinstance(value, dict):
            raise ValidationError('Field "{}" is not'
                                  ' dict'.format(self.field_name))
        return value

    def is_null_value(self, value):
        return value is None or (isinstance(value, dict) and len(value) == 0)


class EmailField(CharField):

    def validate_value(self, value):
        if not isinstance(value, str):
            raise ValidationError('Field "{}" is '
                                  'not string'.format(self.field_name))
        splitted = value.split('@')
        if len(splitted) != 2 \
                or len(splitted[0]) == 0 \
                or len(splitted[1]) == 0:
            raise ValidationError('Field "{}" must be email '
                                  'string with one '
                                  '"@" '.format(self.field_name))

        return value

    def is_null_value(self, value):
        return value is None or value == ''


class PhoneField(Field):

    def validate_value(self, value):
        if isinstance(value, str):
            try:
                int(value)
            except ValueError:
                raise ValidationError('Field "{}" has not number'
                                      ' symbols'.format(self.field_name))

        if isinstance(value, int):
            value = str(value)
        if not isinstance(value, str) or len(value) != 11 or value[0] != '7':
            raise ValidationError('Field "{}" must '
                                  'be number/string with 11 symbols '
                                  'starting with 7'.format(self.field_name))
        return value

    def is_null_value(self, value):
        return value is None or value == ''


class DateField(Field):

    def validate_value(self, value):
        if not isinstance(value, str):
            raise ValidationError('Field "{}" is not string')

        try:
            value = datetime.datetime.strptime(value, '%d.%m.%Y')
        except ValueError:
            raise ValidationError('Field "{}" doesn\'t have '
                                  'format DD.MM.YYYY'.format(self.field_name))

        return value

    def is_null_value(self, value):
        return value is None or value == ''


class BirthDayField(DateField):

    def validate_value(self, value):
        real_value = super().validate_value(value)

        date_value = datetime.datetime.strptime(value, '%d.%m.%Y').date()
        delta_days = (datetime.datetime.now().date() - date_value).days
        if delta_days / 365 > 70:
            raise ValidationError('Value of field "{}"'
                                  ' older than 70'
                                  ' years'.format(self.field_name))

        return real_value


class GenderField(Field):

    def validate_value(self, value):
        if not isinstance(value, int) or value not in (0, 1, 2):
            raise ValidationError('Field "{}" is not int'
                                  ' in range(1,2,3)'.format(self.field_name))
        return value

    def is_null_value(self, value):
        return value is None


class ClientIDsField(Field):

    def validate_value(self, value):
        if not isinstance(value, list):
            raise ValidationError('Field "{}" is not'
                                  ' list'.format(self.field_name))

        for item in value:
            if not isinstance(item, int):
                raise ValidationError('Field "{}" has no'
                                      ' int values'.format(self.field_name))
        return value

    def is_null_value(self, value):
        return value is None or (isinstance(value, list) and len(value) == 0)


class RequestMeta(ABCMeta):

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
        self.__validated = False

        values = values or {}
        for key, value in values.items():
            if hasattr(self, key):
                setattr(self, key, value)

    def clean_data(self):
        data = {}
        for field_name, field in self.fields:
            data[field_name] = getattr(self, field_name)
        return data

    def is_valid(self):
        if self.__validated:
            return self.__errors is None

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

        self.__errors = ';'.join(errors) if len(errors) > 0 else None
        return self.__errors is None

    def errors(self):
        return self.__errors

    def validate(self):
        pass


class ClientsInterestsRequest(Request):
    client_ids = ClientIDsField(required=True)
    date = DateField(required=False, nullable=True)


class OnlineScoreRequest(Request):
    first_name = CharField(required=False, nullable=True)
    last_name = CharField(required=False, nullable=True)
    email = EmailField(required=False, nullable=True)
    phone = PhoneField(required=False, nullable=True)
    birthday = BirthDayField(required=False, nullable=True)
    gender = GenderField(required=False, nullable=True)

    def validate(self):
        data = self.clean_data()

        if data['phone'] is not None and data['email'] is not None:
            return
        elif data['first_name'] is not None and data['last_name'] is not None:
            return
        if data['gender'] is not None and data['birthday'] is not None:
            return

        raise ValidationError('No not empty pair(phone-email, '
                              'first_name-last_name, '
                              'gender-birthday) in request')


class MethodRequest(Request):
    account = CharField(required=False, nullable=True)
    login = CharField(required=True, nullable=True)
    token = CharField(required=True, nullable=True)
    arguments = ArgumentsField(required=True, nullable=True)
    method = CharField(required=True, nullable=False)

    @property
    def is_admin(self):
        return self.login == ADMIN_LOGIN


def check_auth(request):
    if request.is_admin:
        digest = hashlib.sha512((datetime.datetime.now().strftime("%Y%m%d%H") +
                                 ADMIN_SALT).encode('utf-8')).hexdigest()
    else:
        digest = hashlib.sha512((request.account + request.login +
                                 SALT).encode('utf-8')).hexdigest()
    if digest == request.token:
        return True
    return False


def online_score_handler(request, ctx, store):
    method = OnlineScoreRequest(request.arguments)

    if not method.is_valid():
        logging.error('Online score request is not valid')
        return method.errors(), INVALID_REQUEST

    clean_data = method.clean_data()
    ctx['has'] = []
    for key, value in clean_data.items():
        if value is not None:
            ctx['has'].append(key)

    if request.is_admin:
        logging.info('Admin in online_score: returning 42')
        return {'score': 42}, OK

    return {'score': scoring.get_score(store, **clean_data)}, OK


def client_interests_handler(request, ctx, store):
    method = ClientsInterestsRequest(request.arguments)

    if not method.is_valid():
        logging.error('client_interests request is not valid')
        return method.errors(), INVALID_REQUEST

    ctx['nclients'] = len(method.client_ids)
    response = {}
    for cid in method.client_ids:
        response[cid] = scoring.get_interests(store, cid)
    return response, OK


def method_handler(request, ctx, store):
    router = {
        'online_score': online_score_handler,
        'clients_interests': client_interests_handler
    }

    body = request['body']
    method_request = MethodRequest(body)

    if not method_request.is_valid():
        logging.error('Method request is not valid')
        return method_request.errors(), INVALID_REQUEST

    if not check_auth(method_request):
        logging.error('Auth failed')
        return None, FORBIDDEN

    try:
        concrete_method_handler = router[method_request.method]
    except KeyError:
        logging.error('Unknown method:'
                      ' "{}"'.format(method_request.method))
        return None, NOT_FOUND
    logging.info('Method request: {}'.format(method_request.method))
    response, code = concrete_method_handler(method_request,
                                             ctx, store)
    return response, code


class MainHTTPHandler(BaseHTTPRequestHandler):
    router = {
        "method": method_handler
    }
    store = store.Store()

    def get_request_id(self, headers):
        return headers.get('HTTP_X_REQUEST_ID', uuid.uuid4().hex)

    def do_POST(self):
        response, code = {}, OK
        context = {"request_id": self.get_request_id(self.headers)}
        request = None
        try:
            data_string = self.rfile.read(int(self.headers['Content-Length']))
            request = json.loads(data_string.decode('utf-8'))
        except Exception:
            logging.error('Couldn\'t parse request json')
        else:
            if not request:
                logging.error('Request data is empty')

        if request:
            path = self.path.strip("/")
            logging.info("%s: %s %s" % (self.path, data_string,
                                        context["request_id"]))
            if path in self.router:
                try:
                    response, code = self.router[path](
                        {"body": request, "headers": self.headers},
                        context, self.store)
                except Exception as e:
                    logging.exception("Unexpected error: {}".format(e))
                    code = INTERNAL_ERROR
            else:
                code = NOT_FOUND
        else:
            code = BAD_REQUEST

        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        if code not in ERRORS:
            r = {"response": response, "code": code}
        else:
            error = response or ERRORS.get(code, "Unknown Error")
            logging.error("Request errors: {}".format(error))
            r = {"error": error, "code": code}
        context.update(r)
        logging.info(context)
        self.wfile.write(json.dumps(r).encode('utf-8'))


if __name__ == "__main__":
    op = OptionParser()

    op.add_option("-p", "--port", action="store", type=int, default=8080)
    op.add_option("-s", "--store", action="store",)
    op.add_option("-l", "--log", action="store", default=None)
    (opts, args) = op.parse_args()
    logging.basicConfig(filename=opts.log, level=logging.INFO,
                        format='[%(asctime)s] %(levelname).1s %(message)s',
                        datefmt='%Y.%m.%d %H:%M:%S')

    store_addr, store_port = opts.store.split(':')
    MainHTTPHandler.store = store.Store(store_addr, store_port)

    server = HTTPServer(("localhost", opts.port), MainHTTPHandler)

    logging.info("Starting server at %s" % opts.port)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    except Exception as e:
        logging.exception("Server is shutting down, error: {}".format(e))
    server.server_close()
