import unittest
import json
import redis
from unittest import mock
from datetime import datetime
from datetime import timedelta

import store
import api
import scoring

from test_utils import cases, set_valid_auth


class StubStore:

    def __init__(self, optional_get_result=None):
        self.result = optional_get_result

    def get(self, _):
        return self.result

    def set(self, *args, **kwargs):
        pass

    def cache_get(self, *args, **kwargs):
        pass

    def cache_set(self, *args, **kwargs):
        pass


class TestFieldBaseValidation(unittest.TestCase):

    def create_class_with_field(self, _field, field_value=None, init_by_value=True):
        class RequestTestClass(api.Request):
            field = _field

            def validate(self): pass

        if init_by_value:
            return RequestTestClass({'field': field_value})

        return RequestTestClass({})

    def test_required_nullable_field(self):
        field = api.CharField(required=True, nullable=True)
        inst = self.create_class_with_field(field,
                                            field_value=None,
                                            init_by_value=False)
        self.assertRaises(api.ValidationError, field.validate, inst)

    def test_required_non_nullable_field(self):
        field = api.CharField(required=True, nullable=False)
        inst = self.create_class_with_field(field,
                                            field_value=None,
                                            init_by_value=False)
        self.assertRaises(api.ValidationError, field.validate, inst)

    def test_non_required_non_nullable_field(self):
        field = api.CharField(required=False, nullable=False)
        inst = self.create_class_with_field(field,
                                            field_value=None,
                                            init_by_value=True)
        self.assertRaises(api.ValidationError, field.validate, inst)


class TestCharField(unittest.TestCase):

    def setUp(self):
        self.field = api.CharField()
        self.field.field_name = 'char_field'

    @cases(['19.12.2001', 'abc', '+777777', ''])
    def test_field_validate_no_raise(self, args):
        self.field.validate_value(args)

    @cases([1, ['1', '1'], {}])
    def test_field_validate_raise(self, args):
        self.assertRaises(api.ValidationError, self.field.validate_value, args)

    @cases(['', None])
    def test_field_is_null(self, args):
        self.assertTrue(self.field.is_null_value(args))


class TestArgsField(unittest.TestCase):

    def setUp(self):
        self.field = api.ArgumentsField()
        self.field.field_name = 'args_field'

    @cases([{}, {'1': 1}, {'a': [1, 1, 1]}])
    def test_field_validate_no_raise(self, args):
        self.field.validate_value(args)

    @cases(['', 1, [1, 2, 3]])
    def test_field_validate_raise(self, args):
        self.assertRaises(api.ValidationError, self.field.validate_value, args)

    @cases([None, {}])
    def test_field_is_null(self, args):
        self.assertTrue(self.field.is_null_value(args))

    @cases([{1: 1}])
    def test_field_is_null_false(self, args):
        self.assertFalse(self.field.is_null_value(args))


class TestEmailField(unittest.TestCase):

    def setUp(self):
        self.field = api.EmailField()
        self.field.field_name = 'email_field'

    @cases(['test@test', 'testttt@a'])
    def test_field_validate_no_raise(self, args):
        self.field.validate_value(args)

    @cases(['@test', 'test@', 'test'])
    def test_field_validate_raise(self, args):
        self.assertRaises(api.ValidationError, self.field.validate_value, args)

    @cases([None, ''])
    def test_field_is_null(self, args):
        self.assertTrue(self.field.is_null_value(args))

    def test_field_is_null_false(self):
        self.assertFalse(self.field.is_null_value('test@test'))


class TestPhoneField(unittest.TestCase):

    def setUp(self):
        self.field = api.PhoneField()
        self.field.field_name = 'phone_field'

    @cases(['79998887766', 79998887766])
    def test_field_validate_no_raise(self, args):
        self.field.validate_value(args)

    @cases(['799988877661', '7999888776', '89998887766', '7a998887766'])
    def test_field_validate_raise(self, args):
        self.assertRaises(api.ValidationError, self.field.validate_value, args)

    @cases(['', None])
    def test_field_is_null(self, args):
        self.assertTrue(self.field.is_null_value(args))

    def test_field_is_null_false(self):
        self.assertFalse(self.field.is_null_value('89998887766'))


class TestDateField(unittest.TestCase):

    def setUp(self):
        self.field = api.DateField()
        self.field.field_name = 'date_field'

    @cases(['19.12.2001', '01.01.1901'])
    def test_field_validate_no_raise(self, args):
        self.field.validate_value(args)

    @cases(['45.12.2001', 'asdf.12.2001'])
    def test_field_validate_raise(self, args):
        self.assertRaises(api.ValidationError, self.field.validate_value, args)

    @cases(['', None])
    def test_field_is_null(self, args):
        self.assertTrue(self.field.is_null_value(args))

    def test_field_is_null_false(self):
        self.assertFalse(self.field.is_null_value('19.12.2001'))


class TestBirthdayField(unittest.TestCase):

    def setUp(self):
        self.field = api.BirthDayField()
        self.field.field_name = 'birthday_field'

    def test_field_validate_no_raise(self):
        old_time = datetime.now() - timedelta(days=365*70-1)
        old_time = old_time.strftime("%d.%m.%Y")
        self.field.validate_value(old_time)

    def test_field_validate_raise(self):
        old_time = datetime.now() - timedelta(days=365*70+1)
        old_time = old_time.strftime("%d.%m.%Y")
        self.assertRaises(api.ValidationError, self.field.validate_value, old_time)

    @cases(['', None])
    def test_field_is_null(self, args):
        self.assertTrue(self.field.is_null_value(args))

    def test_field_is_null_false(self):
        self.assertFalse(self.field.is_null_value('19.12.2001'))


class TestGenderField(unittest.TestCase):

    def setUp(self):
        self.field = api.GenderField()
        self.field.field_name = 'gender_field'

    @cases([0, 1, 2])
    def test_field_validate_no_raise(self, args):
        self.field.validate_value(args)

    @cases([-1, 3, '2'])
    def test_field_validate_raise(self, args):
        self.assertRaises(api.ValidationError, self.field.validate_value, args)

    def test_field_is_null(self):
        self.assertTrue(self.field.is_null_value(None))

    def test_field_is_null_false(self):
        self.assertFalse(self.field.is_null_value(1))


class TestClientsIds(unittest.TestCase):

    def setUp(self):
        self.field = api.ClientIDsField()
        self.field.field_name = 'client_ids_field'

    @cases([[1, 2], []])
    def test_field_validate_no_raise(self, args):
        self.field.validate_value(args)

    @cases(['123', [1, '2']])
    def test_field_validate_raise(self, args):
        self.assertRaises(api.ValidationError, self.field.validate_value, args)

    @cases([None, []])
    def test_field_is_null(self, args):
        self.assertTrue(self.field.is_null_value(args))

    def test_field_is_null_false(self):
        self.assertFalse(self.field.is_null_value([1, 2]))


class TestRequestFieldValidation(unittest.TestCase):
    @cases([{'client_ids': [1, 2]}, {'client_ids': [1, 2], 'date': '01.01.1990'}])
    def test_request_field_validation_valid(self, args):
        request = api.ClientsInterestsRequest(args)
        self.assertTrue(request.is_valid())

    @cases([{}, {'client_ids': []}, {'client_ids': [1], 'date': '55.01.2018'}])
    def test_request_field_validation_not_valid(self, args):
        request = api.ClientsInterestsRequest(args)
        self.assertFalse(request.is_valid())

    def test_request_field_validation_return_invalid_code(self):
        class Request:
            def __init__(self, args): self.arguments = args

        request = Request({})
        response, code = api.client_interests_handler(request, None, None)
        self.assertEqual(code, api.INVALID_REQUEST)


class TestMethod(unittest.TestCase):

    def setUp(self):
        self.context = {}
        self.headers = {}
        self.store = StubStore()

    def get_response(self, request):
        return api.method_handler({"body": request, "headers": self.headers},
                                  self.context, self.store)

    def test_empty_request(self):
        _, code = self.get_response({})
        self.assertEqual(api.INVALID_REQUEST, code)

    @cases([
        {"account": "horns&hoofs", "login": "h&f", "method": "online_score", "token": "", "arguments": {}},
        {"account": "horns&hoofs", "login": "h&f", "method": "online_score", "token": "sdd", "arguments": {}}
    ])
    def test_auth_not_valid(self, args):
        request = api.MethodRequest(args)
        self.assertFalse(api.check_auth(request))

    @cases([
        {"account": "horns&hoofs", "login": "h&f", "method": "online_score", "token": "", "arguments": {}},
        {"account": "horns&hoofs", "login": "h&f", "method": "online_score", "token": "sdd", "arguments": {}}
    ])
    def test_auth_valid(self, args):
        set_valid_auth(args)
        request = api.MethodRequest(args)
        self.assertTrue(api.check_auth(request))

    @cases([
        {"account": "horns&hoofs", "login": "admin", "method": "online_score", "token": "", "arguments": {}},
    ])
    def test_auth_admin_not_valid(self, args):
        request = api.MethodRequest(args)
        self.assertFalse(api.check_auth(request))

    @cases([
        {"account": "horns&hoofs", "login": "admin", "method": "online_score", "token": "", "arguments": {}},
    ])
    def test_auth_admin_valid(self, args):
        set_valid_auth(args)
        request = api.MethodRequest(args)
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
        set_valid_auth(request)
        _, code = self.get_response(request)
        self.assertEqual(api.NOT_FOUND, code)


class TestOnlineScore(unittest.TestCase):

    def setUp(self):
        self.context = {}
        self.headers = {}
        self.store = StubStore()

    def get_response(self, request):
        return api.method_handler({"body": request, "headers": self.headers},
                                  self.context, self.store)

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

        args = {'phone': '78889990099', 'email': 'tt@tt',
                'gender': None, 'first_name': ''}
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

        args = {'phone': '78889990099', 'email': 'tt@tt',
                'gender': None, 'first_name': ''}

        with mock.patch('scoring.get_score') as gs:
            gs.return_value = None

            request = Request(args)

            handler_res, _ = api.online_score_handler(request, {}, None)
            self.assertEqual(handler_res['score'], 42)

    @cases([
        (['phone', 'email', 'gender', 'first_name'], 3),
        (['phone', 'email', 'gender', 'first_name', 'last_name'], 3.5)
    ])
    def test_get_score(self, args, result):
        args = {key: '1' for key in args}
        self.assertAlmostEqual(scoring.get_score(self.store, **args), result)

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
        request = {"account": "horns&hoofs", "login": "h&f",
                   "method": "online_score", "arguments": arguments}
        set_valid_auth(request)
        _, code = self.get_response(request)
        self.assertEqual(code, api.OK)

    def test_ok_score_admin_request(self):
        arguments = {"phone": "79995008811", "email": "tt@tt"}
        request = {"account": "horns&hoofs", "login": "admin",
                   "method": "online_score", "arguments": arguments}
        set_valid_auth(request)
        response, code = self.get_response(request)
        self.assertEqual(api.OK, code)
        score = response.get("score")
        self.assertEqual(score, 42)


class TestClientInterests(unittest.TestCase):

    def setUp(self):
        self.context = {}
        self.headers = {}
        self.store = StubStore()

    def get_response(self, request):
        return api.method_handler({"body": request, "headers": self.headers},
                                  self.context, self.store)

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

    def test_get_interests(self):
        d = json.dumps([])
        res = json.dumps(scoring.get_interests(self.store, 1))
        self.assertEqual(res, d)

    @cases([
        {"client_ids": [1, 2, 3], "date": datetime.today().strftime("%d.%m.%Y")},
        {"client_ids": [1, 2], "date": "19.07.2017"},
        {"client_ids": [0]},
    ])
    def test_method_client_interests(self, arguments):
        request = {"account": "horns&hoofs", "login": "h&f",
                   "method": "clients_interests", "arguments": arguments}
        set_valid_auth(request)
        response, code = self.get_response(request)
        self.assertEqual(api.OK, code)


class StoreTestSuite(unittest.TestCase):

    def setUp(self):
        self.store = store.Store()

    def tearDown(self):
        self.store.persistent.flush()
        self.store.cache.flush()

    @cases([
        ('key_1', '1'),
        ('key_2', 2),
        ('key_3', [1, 2, 3, 4, '5'])
    ])
    def test_set_get(self, key, value):
        self.store.set(key, 0)
        self.store.set(key, value)
        self.store.set(key + '1', 0)

        if isinstance(value, list):
            self.assertListEqual(value, self.store.get(key))
        else:
            self.assertEqual(value, self.store.get(key))

    def test_get_failed(self):
        self.assertEqual(self.store.get('non-existing-key-1298'), None)

    def test_update_key(self):
        key = 'key_1'
        value_1 = 88
        value_2 = 'test_value'

        self.store.set(key, value_1)
        self.assertEqual(self.store.get(key), value_1)

        self.store.set(key, value_2)
        self.assertEqual(self.store.get(key), value_2)

    def test_set_get_with_retry(self):
        key = 'key_1'
        value = 'value_1'

        self.store.set(key, value)

        # Test retry attempts
        with mock.patch('redis.StrictRedis.get') as redis_get:
            redis_get.side_effect = [redis.ConnectionError,
                                     redis.TimeoutError,
                                     store.StoreConnection._encode(value).encode('utf-8')]
            self.assertEqual(self.store.get(key), value)

        # Test failed connection
        connection_pool = self.store.persistent.conn.connection_pool
        # get all connections
        connection_pool.max_connections = 1
        con1 = connection_pool.get_connection('NO_CMD')
        # check this
        self.assertRaises(redis.ConnectionError,
                          connection_pool.get_connection, "NO_CMD")
        # check assert
        self.assertRaises(store.StoreConnectionError, self.store.get, key)

        # Test success connection after disconnection
        # release con1
        connection_pool.release(con1)
        connection_pool.disconnect()
        self.assertEqual(self.store.get(key), value)

    def test_set_get_unavailable_store(self):
        key = 'key_1'
        value = 'value_1'
        self.store.set(key, value)

        # Test retry attempts
        with mock.patch('redis.StrictRedis.get') as redis_get:
            redis_get.side_effect = redis.ConnectionError
            self.assertRaises(store.StoreConnectionError, self.store.get, key)

    @cases([
        ('key_1', '1', 30, '1'),
        ('key_2', 2, -30, None),
        ('key_3', [1, '5'], 30,  [1, '5'])
    ])
    def test_cache(self, key, value, time, result):
        self.store.cache_set(key, value, time)
        cache_result = self.store.cache_get(key)

        if isinstance(result, list):
            self.assertListEqual(cache_result, result)
        else:
            self.assertEqual(cache_result, result)

    def test_cache_clear_after_disconnection(self):
        self.store.cache_set('key_1', '1', 60)
        self.store.cache_set('key_2', '2', 60)

        # test disconnection
        with mock.patch('redis.StrictRedis.get') as redis_get:
            redis_get.side_effect = redis.ConnectionError
            self.assertEqual(self.store.cache_get('key_1'), None)

        # test right results
        self.assertEqual(self.store.cache_get('key_1'), '1')

        # test set at disconnection
        with mock.patch('redis.StrictRedis.set') as redis_set:
            redis_set.side_effect = redis.ConnectionError
            self.store.cache_set('key_1', '11', 60)

        self.assertEqual(self.store.cache_get('key_1'), '1')


if __name__ == "__main__":
    unittest.main()
