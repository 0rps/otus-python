import unittest
import functools
import hashlib
import json
from unittest import mock
from datetime import datetime
from datetime import timedelta

import api
import scoring


def cases(cases):
    def decorator(f):
        @functools.wraps(f)
        def wrapper(*args):
            for c in cases:
                new_args = args + (c if isinstance(c, tuple) else (c,))
                f(*new_args)
        return wrapper
    return decorator


class TestSuite(unittest.TestCase):
    def setUp(self):
        self.context = {}
        self.headers = {}
        self.store = None

    def get_response(self, request):
        return api.method_handler({"body": request, "headers": self.headers}, self.context, self.store)

    def test_empty_request(self):
        _, code = self.get_response({})
        self.assertEqual(api.INVALID_REQUEST, code)

    def create_class_with_field(self, _field, field_value=None, init_by_value=True):
        class RequestTestClass(api.Request):
            field = _field

            def validate(self): pass

        if init_by_value:
            return RequestTestClass({'field': field_value})

        return RequestTestClass({})

    def set_valid_auth(self, request):
        if request.get("login") == api.ADMIN_LOGIN:
            msg = (datetime.now().strftime("%Y%m%d%H") + api.ADMIN_SALT).encode('utf-8')
            request["token"] = hashlib.sha512(msg).hexdigest()
        else:
            msg = request.get("account", "") + request.get("login", "") + api.SALT
            msg = msg.encode('utf-8')
            request["token"] = hashlib.sha512(msg).hexdigest()

    def test_required_nullable_field(self):
        field = api.CharField(required=True, nullable=True)
        inst = self.create_class_with_field(field, field_value=None, init_by_value=False)
        self.assertRaises(api.ValidationError, field.validate, inst)

    def test_required_non_nullable_field(self):
        field = api.CharField(required=True, nullable=False)
        inst = self.create_class_with_field(field, field_value=None, init_by_value=False)
        self.assertRaises(api.ValidationError, field.validate, inst)

    def test_non_required_non_nullable_field(self):
        field = api.CharField(required=False, nullable=False)
        inst = self.create_class_with_field(field, field_value=None, init_by_value=True)
        self.assertRaises(api.ValidationError, field.validate, inst)

    @cases(['19.12.2001', 'abc', '+777777', ''])
    def test_char_field_validate_no_raise(self, args):
        field = api.CharField()
        field.field_name = 'field'
        field.validate_value(args)

    @cases([1, ['1', '1'], {}])
    def test_char_field_validate_raise(self, args):
        field = api.CharField()
        field.field_name = 'field'
        self.assertRaises(api.ValidationError, field.validate_value, args)

    @cases(['', None])
    def test_char_field_is_null(self, args):
        field = api.CharField()
        field.field_name = 'field'
        self.assertTrue(field.is_null_value(args))

    @cases([{}, {'1': 1}, {'a': [1, 1, 1]}])
    def test_args_field_validate_no_raise(self, args):
        field = api.ArgumentsField()
        field.field_name = 'field'
        field.validate_value(args)

    @cases(['', 1, [1, 2, 3]])
    def test_args_field_validate_raise(self, args):
        field = api.ArgumentsField()
        field.field_name = 'field'
        self.assertRaises(api.ValidationError, field.validate_value, args)

    @cases([None, {}])
    def test_args_field_is_null_true(self, arg):
        field = api.ArgumentsField()
        field.field_name = 'field'
        self.assertTrue(field.is_null_value(arg))

    @cases([{1: 1}])
    def test_args_field_is_null_false(self, args):
        field = api.ArgumentsField()
        field.field_name = 'field'
        self.assertFalse(field.is_null_value(args))

    @cases(['test@test', 'testttt@a'])
    def test_email_field_validate_no_raise(self, arg):
        field = api.EmailField()
        field.field_name = 'field'
        field.validate_value(arg)

    @cases(['@test', 'test@', 'test'])
    def test_email_field_validate_raise(self, arg):
        field = api.EmailField()
        field.field_name = 'field'
        self.assertRaises(api.ValidationError, field.validate_value, arg)

    @cases([None, ''])
    def test_email_field_is_null_true(self, arg):
        field = api.EmailField()
        self.assertTrue(field.is_null_value(arg))

    def test_email_field_is_null_false(self):
        field = api.EmailField()
        self.assertFalse(field.is_null_value('test@test'))

    @cases(['79998887766', 79998887766])
    def test_phone_field_validate_no_raise(self, arg):
        field = api.PhoneField()
        field.field_name = 'field'
        field.validate_value(arg)

    @cases(['799988877661', '7999888776', '89998887766', '7a998887766'])
    def test_phone_field_validate_raise(self, arg):
        field = api.PhoneField()
        field.field_name = 'field'
        self.assertRaises(api.ValidationError, field.validate_value, arg)

    @cases(['', None])
    def test_phone_field_is_null_true(self, arg):
        field = api.PhoneField()
        field.field_name = 'field'
        self.assertTrue(field.is_null_value(arg))

    def test_phone_field_is_null_false(self):
        field = api.PhoneField()
        field.field_name = 'field'
        self.assertFalse(field.is_null_value('89998887766'))

    @cases(['19.12.2001', '01.01.1901'])
    def test_date_field_validate_no_raise(self, arg):
        field = api.DateField()
        field.field_name = 'field'
        field.validate_value(arg)

    @cases(['45.12.2001', 'asdf.12.2001'])
    def test_date_field_validate_raise(self, arg):
        field = api.DateField()
        field.field_name = 'field'
        self.assertRaises(api.ValidationError, field.validate_value, arg)

    @cases(['', None])
    def test_date_field_is_null_true(self, arg):
        field = api.DateField()
        field.field_name = 'field'
        self.assertTrue(field.is_null_value(arg))

    def test_date_field_is_null_false(self):
        field = api.DateField()
        field.field_name = 'field'
        self.assertFalse(field.is_null_value('19.12.2001'))

    def test_birthday_field_validate_no_raise(self):
        old_time = datetime.now() - timedelta(days=365*70-1)
        old_time = old_time.strftime("%d.%m.%Y")

        field = api.BirthDayField()
        field.field_name = 'field'
        field.validate_value(old_time)

    def test_birthday_field_validate_raise(self):
        old_time = datetime.now() - timedelta(days=365*70+1)
        old_time = old_time.strftime("%d.%m.%Y")

        field = api.BirthDayField()
        field.field_name = 'field'
        self.assertRaises(api.ValidationError, field.validate_value, old_time)

    @cases([0, 1, 2])
    def test_gender_field_validate_no_raise(self, arg):
        field = api.GenderField()
        field.field_name = 'field'
        field.validate_value(arg)

    @cases([-1, 3, '2'])
    def test_gender_field_validate_raise(self, arg):
        field = api.GenderField()
        field.field_name = 'field'
        self.assertRaises(api.ValidationError, field.validate_value, arg)

    def test_gender_field_is_null_true(self):
        field = api.GenderField()
        field.field_name = 'field'
        self.assertTrue(field.is_null_value(None))

    def test_gender_field_is_null_false(self):
        field = api.GenderField()
        field.field_name = 'field'
        self.assertFalse(field.is_null_value(1))

    @cases([[1, 2], []])
    def test_client_ids_field_validate_no_raise(self, arg):
        field = api.ClientIDsField()
        field.field_name = 'field'
        field.validate_value(arg)

    @cases(['123', [1, '2']])
    def test_client_ids_field_validate_raise(self, arg):
        field = api.ClientIDsField()
        field.field_name = 'field'
        self.assertRaises(api.ValidationError, field.validate_value, arg)

    @cases([None, []])
    def test_client_ids_field_is_null_true(self, arg):
        field = api.ClientIDsField()
        field.field_name = 'field'
        self.assertTrue(field.is_null_value(arg))

    def test_client_ids_field_is_null_false(self):
        field = api.ClientIDsField()
        field.field_name = 'field'
        self.assertFalse(field.is_null_value([1, 2]))

    @cases([{'client_ids': [1, 2]}, {'client_ids': [1, 2], 'date': '01.01.1990'}])
    def test_request_field_validation_valid(self, args):
        request = api.ClientsInterestsRequest(args)
        self.assertTrue(request.is_valid())

    @cases([{}, {'client_ids': []}, {'client_ids': [1], 'date': '55.01.2018'}])
    def test_request_field_validation_not_valid(self, args):
        request = api.ClientsInterestsRequest(args)
        self.assertFalse(request.is_valid())

    def test_request_field_validation_return_invalid(self):
        class Request:
            def __init__(self, args): self.arguments = args

        request = Request({})
        response, code = api.client_interests_handler(request, None, None)
        self.assertEqual(code, api.INVALID_REQUEST)

    @cases([
        [{'client_ids': [1]}, 1],
        [{'client_ids': [1, 2, 3]}, 3]])
    def test_client_interests_handler_ctx(self, args):
        class A:
            pass

        with mock.patch('scoring.get_interests') as gi:
            gi.return_value = []
            ctx = {}
            request = A()
            request.arguments = args[0]

            api.client_interests_handler(request, ctx, None)
            self.assertEqual(ctx['nclients'], args[1])

    @cases([
        {'phone': '78889998877', 'email': 'tt@tt'},
        {'first_name': '11', 'last_name': '22'},
        {'gender': 1, 'birthday': '01.01.2000'}])
    def test_online_score_validation_valid(self, args):
        request = api.OnlineScoreRequest(args)
        self.assertTrue(request.is_valid())

    @cases([
        {'first_name': '11', 'birthday': '01.01.2000'},
        {'gender': '1', 'last_name': '22'}])
    def test_online_score_validation_not_valid(self, args):
        request = api.OnlineScoreRequest(args)
        self.assertFalse(request.is_valid())

    def test_online_score_handler_ctx(self):
        class Request:
            def __init__(self, args):
                self.arguments = args
                self.is_admin = None

        args = {'phone': '78889990099', 'email': 'tt@tt', 'gender': None, 'first_name': ''}
        res = ['phone', 'email']

        with mock.patch('scoring.get_score') as gs:
            gs.return_value = None

            ctx = {}
            request = Request(args)

            api.online_score_handler(request, ctx, None)
            self.assertListEqual(sorted(res), sorted(ctx['has']))

    def test_online_score_handler_admin(self):
        class Request:
            def __init__(self, args):
                self.arguments = args
                self.is_admin = True

        args = {'phone': '78889990099', 'email': 'tt@tt', 'gender': None, 'first_name': ''}

        with mock.patch('scoring.get_score') as gs:
            gs.return_value = None

            request = Request(args)

            handler_res, _ = api.online_score_handler(request, {}, None)
            self.assertEqual(handler_res['score'], 42)

    @cases([
        {"account": "horns&hoofs", "login": "h&f", "method": "online_score", "token": "", "arguments": {}},
        {"account": "horns&hoofs", "login": "h&f", "method": "online_score", "token": "sdd", "arguments": {}}
    ])
    def test_auth_not_valid(self, request):
        self.assertFalse(api.check_auth(request))

    @cases([
        {"account": "horns&hoofs", "login": "h&f", "method": "online_score", "token": "", "arguments": {}},
        {"account": "horns&hoofs", "login": "h&f", "method": "online_score", "token": "sdd", "arguments": {}}
    ])
    def test_auth_valid(self, request):
        self.set_valid_auth(request)
        self.assertTrue(api.check_auth(request))

    @cases([
        {"account": "horns&hoofs", "login": "admin", "method": "online_score", "token": "", "arguments": {}},
    ])
    def test_auth_admin_not_valid(self, request):
        _, code = self.get_response(request)
        self.assertFalse(api.check_auth(request))

    @cases([
        {"account": "horns&hoofs", "login": "admin", "method": "online_score", "token": "", "arguments": {}},
    ])
    def test_auth_admin_valid(self, request):
        self.set_valid_auth(request)
        self.assertTrue(api.check_auth(request))

    @cases([
        {"account": "horns&hoofs", "login": "h&f", "method": "online_score", "token": "", "arguments": {}},
        {"account": "horns&hoofs", "login": "h&f", "method": "online_score", "token": "sdd", "arguments": {}},
        {"account": "horns&hoofs", "login": "admin", "method": "online_score", "token": "", "arguments": {}},
    ])
    def test_method_fail_auth(self, request):
        _, code = self.get_response(request)
        self.assertEqual(api.FORBIDDEN, code)

    @cases([
        {"account": "horns&hoofs", "login": "admin", "method": "online_scre", "token": "", "arguments": {}},
    ])
    def test_method_fail_method(self, request):
        _, code = self.get_response(request)
        self.assertEqual(api.NOT_FOUND, code)

    @cases([
        [['phone', 'email', 'birthday', 'gender', 'first_name'], 4.5],
        [['phone', 'email', 'gender', 'first_name', 'last_name'], 3.5]
    ])
    def test_get_score(self, args, result):
        class Store:
            def cache_get(self, *_): pass

            def cache_set(self, *_): pass

        args = {key: True for key in args}
        self.assertAlmostEqual(scoring.get_score(Store(), **args), result)

    def test_get_interests(self):
        class Store:
            def __init__(self, d): self.d = d

            def get(self, *_): return self.d

        d = json.dumps({'1': ['a', 'b', 'c']})
        res = json.dumps(scoring.get_interests(Store(d), 1))
        self.assertEqual(res, d)

    @cases([
        {"phone": "79175002040", "email": "tt@tt"},
        {"phone": 79175002040, "email": "tt@tt"},
        {"gender": 1, "birthday": "01.01.2000", "first_name": "a", "last_name": "b"},
        {"gender": 0, "birthday": "01.01.2000"},
        {"gender": 2, "birthday": "01.01.2000"},
        {"first_name": "a", "last_name": "b"},
        {"phone": "79995008811", "email": "ttt@tt", "gender": 1, "birthday": "01.01.2000",
         "first_name": "a", "last_name": "b"},
    ])
    def test_method_online_score(self, arguments):
        class Store:
            def cache_get(self, *_): pass

            def cache_set(self, *_): pass

        self.store = Store()
        request = {"account": "horns&hoofs", "login": "h&f", "method": "online_score", "arguments": arguments}
        self.set_valid_auth(request)

    def test_ok_score_admin_request(self):
        arguments = {"phone": "79995008811", "email": "tt@tt"}
        request = {"account": "horns&hoofs", "login": "admin", "method": "online_score", "arguments": arguments}
        self.set_valid_auth(request)
        response, code = self.get_response(request)
        self.assertEqual(api.OK, code)
        score = response.get("score")
        self.assertEqual(score, 42)

    @cases([
        {"client_ids": [1, 2, 3], "date": datetime.today().strftime("%d.%m.%Y")},
        {"client_ids": [1, 2], "date": "19.07.2017"},
        {"client_ids": [0]},
    ])
    def test_method_client_interests(self, arguments):
        class Store:
            def __init__(self, d): self.d = d

            def get(self, *_): return self.d

        self.store = Store(json.dumps({}))
        request = {"account": "horns&hoofs", "login": "h&f", "method": "clients_interests", "arguments": arguments}
        self.set_valid_auth(request)
        response, code = self.get_response(request)
        self.assertEqual(api.OK, code, arguments)


class StoreTestSuite(unittest.TestCase):

    def test_set_get(self):
        pass

    def test_set_get_with_reconnect(self):
        pass

    def test_set_get_unavailable_store(self):
        pass

    def test_cache(self):
        pass

    def test_cache_expiration(self):
        pass

    def test_cache_unavailable_store(self):
        pass

    def test_get_store(self):
        pass

    def test_get_interests(self):
        pass


class MethodTestSuiteWithStore(unittest.TestCase):

    def test_online_score(self):
        pass

    def test_online_score_invalid_request(self):
        pass

    def test_online_score_store_unavailable(self):
        pass

    def test_client_interests(self):
        pass

    def test_client_interests_store_unavaliable(self):
        pass


if __name__ == "__main__":
    unittest.main()
