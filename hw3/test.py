import hashlib
import datetime
import functools
import unittest

import api


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
        self.settings = {}

    def get_response(self, request):
        return api.method_handler({"body": request, "headers": self.headers}, self.context, self.settings)

    def set_valid_auth(self, request):
        if request.get("login") == api.ADMIN_LOGIN:
            msg = (datetime.datetime.now().strftime("%Y%m%d%H") + api.ADMIN_SALT).encode('utf-8')
            request["token"] = hashlib.sha512(msg).hexdigest()
        else:
            msg = request.get("account", "") + request.get("login", "") + api.SALT
            msg = msg.encode('utf-8')
            request["token"] = hashlib.sha512(msg).hexdigest()

    def test_empty_request(self):
        _, code = self.get_response({})
        self.assertEqual(api.INVALID_REQUEST, code)

    def create_class_with_field(self, _field, field_value=None, is_init=True):
        class RequestTestClass(api.Request):
            field = _field

            def validate(self): pass

        if is_init:
            return RequestTestClass({'field': field_value})

        return RequestTestClass({})

    @cases([
        {"account": "horns&hoofs", "login": "h&f", "method": "online_score", "token": "", "arguments": {}},
        {"account": "horns&hoofs", "login": "h&f", "method": "online_score", "token": "sdd", "arguments": {}},
        {"account": "horns&hoofs", "login": "admin", "method": "online_score", "token": "", "arguments": {}},
    ])
    def test_bad_auth(self, request):
        _, code = self.get_response(request)
        self.assertEqual(api.FORBIDDEN, code)

    @cases([
        {"account": "horns&hoofs", "login": "h&f", "method": "online_score"},
        {"account": "horns&hoofs", "login": "h&f", "arguments": {}},
        {"account": "horns&hoofs", "method": "online_score", "arguments": {}},
    ])
    def test_invalid_method_request(self, request):
        self.set_valid_auth(request)
        response, code = self.get_response(request)
        self.assertEqual(api.INVALID_REQUEST, code)
        self.assertTrue(len(response))

    @cases([
        {},
        {"phone": "79175002040"},
        {"phone": "89175002040", "email": "stupnikov@otus.ru"},
        {"phone": "79175002040", "email": "stupnikovotus.ru"},
        {"phone": "79175002040", "email": "stupnikov@otus.ru", "gender": -1},
        {"phone": "79175002040", "email": "stupnikov@otus.ru", "gender": "1"},
        {"phone": "79175002040", "email": "stupnikov@otus.ru", "gender": 1, "birthday": "01.01.1890"},
        {"phone": "79175002040", "email": "stupnikov@otus.ru", "gender": 1, "birthday": "XXX"},
        {"phone": "79175002040", "email": "stupnikov@otus.ru", "gender": 1, "birthday": "01.01.2000", "first_name": 1},
        {"phone": "79175002040", "email": "stupnikov@otus.ru", "gender": 1, "birthday": "01.01.2000",
         "first_name": "s", "last_name": 2},
        {"phone": "79175002040", "birthday": "01.01.2000", "first_name": "s"},
        {"email": "stupnikov@otus.ru", "gender": 1, "last_name": 2},
    ])
    def test_invalid_score_request(self, arguments):
        request = {"account": "horns&hoofs", "login": "h&f", "method": "online_score", "arguments": arguments}
        self.set_valid_auth(request)
        response, code = self.get_response(request)
        self.assertEqual(api.INVALID_REQUEST, code, arguments)
        self.assertTrue(len(response))

    @cases([
        {"phone": "79175002040", "email": "stupnikov@otus.ru"},
        {"phone": 79175002040, "email": "stupnikov@otus.ru"},
        {"gender": 1, "birthday": "01.01.2000", "first_name": "a", "last_name": "b"},
        {"gender": 0, "birthday": "01.01.2000"},
        {"gender": 2, "birthday": "01.01.2000"},
        {"first_name": "a", "last_name": "b"},
        {"phone": "79175002040", "email": "stupnikov@otus.ru", "gender": 1, "birthday": "01.01.2000",
         "first_name": "a", "last_name": "b"},
    ])
    def test_ok_score_request(self, arguments):
        request = {"account": "horns&hoofs", "login": "h&f", "method": "online_score", "arguments": arguments}
        self.set_valid_auth(request)
        response, code = self.get_response(request)
        self.assertEqual(api.OK, code, arguments)
        score = response.get("score")
        self.assertTrue(isinstance(score, (int, float)) and score >= 0, arguments)
        self.assertEqual(sorted(self.context["has"]), sorted(arguments.keys()))

    def test_ok_score_admin_request(self):
        arguments = {"phone": "79175002040", "email": "stupnikov@otus.ru"}
        request = {"account": "horns&hoofs", "login": "admin", "method": "online_score", "arguments": arguments}
        self.set_valid_auth(request)
        response, code = self.get_response(request)
        self.assertEqual(api.OK, code)
        score = response.get("score")
        self.assertEqual(score, 42)

    @cases([
        {},
        {"date": "20.07.2017"},
        {"client_ids": [], "date": "20.07.2017"},
        {"client_ids": {1: 2}, "date": "20.07.2017"},
        {"client_ids": ["1", "2"], "date": "20.07.2017"},
        {"client_ids": [1, 2], "date": "XXX"},
    ])
    def test_invalid_interests_request(self, arguments):
        request = {"account": "horns&hoofs", "login": "h&f", "method": "clients_interests", "arguments": arguments}
        self.set_valid_auth(request)
        response, code = self.get_response(request)
        self.assertEqual(api.INVALID_REQUEST, code, arguments)
        self.assertTrue(len(response))

    @cases([
        {"client_ids": [1, 2, 3], "date": datetime.datetime.today().strftime("%d.%m.%Y")},
        {"client_ids": [1, 2], "date": "19.07.2017"},
        {"client_ids": [0]},
    ])
    def test_ok_interests_request(self, arguments):
        request = {"account": "horns&hoofs", "login": "h&f", "method": "clients_interests", "arguments": arguments}
        self.set_valid_auth(request)
        response, code = self.get_response(request)
        self.assertEqual(api.OK, code, arguments)
        self.assertEqual(len(arguments["client_ids"]), len(response))
        self.assertTrue(all(v and isinstance(v, list) and all(isinstance(i, str) for i in v)
                        for v in response.values()))
        self.assertEqual(self.context.get("nclients"), len(arguments["client_ids"]))

    def test_required_nullable_field(self):
        field = api.CharField(True, True)
        inst = self.create_class_with_field(field, None, False)
        self.assertRaises(api.ValidationError, field.validate, inst)

    def test_required_non_nullable_field(self):
        field = api.CharField(True, False)
        inst = self.create_class_with_field(field, None, False)
        self.assertRaises(api.ValidationError, field.validate, inst)

        inst = self.create_class_with_field(field, None, True)
        self.assertRaises(api.ValidationError, field.validate, inst)

    def test_non_required_non_nullable_field(self):
        field = api.CharField(False, False)
        inst = self.create_class_with_field(field, None, True)
        self.assertRaises(api.ValidationError, field.validate, inst)

    def test_char_field(self):
        field = api.CharField()
        field.field_name = 'field'

        field.validate_value('19.12.2001')

        self.assertTrue(field.is_null_value(''))
        self.assertTrue(field.is_null_value(None))
        self.assertFalse(field.is_null_value('19.12.2001'))

    def test_args_field(self):
        field = api.ArgumentsField()
        field.field_name = 'field'

        field.validate_value({'a': 1})

        self.assertTrue(field.is_null_value(None))
        self.assertTrue(field.is_null_value({}))
        self.assertFalse(field.is_null_value({'a': 1}))

    def test_email_field(self):
        field = api.EmailField()
        field.field_name = 'field'

        field.validate_value('test@test')

        self.assertRaises(api.ValidationError, field.validate_value, '@test')
        self.assertRaises(api.ValidationError, field.validate_value, 'test@')
        self.assertRaises(api.ValidationError, field.validate_value, 'test')

        self.assertTrue(field.is_null_value(''))
        self.assertTrue(field.is_null_value(None))
        self.assertFalse(field.is_null_value('test@test'))

    def test_phone_field(self):
        field = api.PhoneField()
        field.field_name = 'field'

        field.validate_value('79998887766')
        field.validate_value(79998887766)

        self.assertRaises(api.ValidationError, field.validate_value, '799988877661')
        self.assertRaises(api.ValidationError, field.validate_value, '7999888776')
        self.assertRaises(api.ValidationError, field.validate_value, '89998887766')
        self.assertRaises(api.ValidationError, field.validate_value, '7a998887766')

        self.assertTrue(field.is_null_value(''))
        self.assertTrue(field.is_null_value(None))

    def test_date_field(self):
        field = api.DateField()
        field.field_name = 'field'

        field.validate_value('19.12.2001')

        self.assertRaises(api.ValidationError, field.validate_value, '45.12.2001')
        self.assertRaises(api.ValidationError, field.validate_value, 'asdf.12.2001')

        self.assertTrue(field.is_null_value(''))
        self.assertTrue(field.is_null_value(None))
        self.assertFalse(field.is_null_value('19.12.2001'))

    def test_birthday_field(self):
        field = api.BirthDayField()
        field.field_name = 'field'

        field.validate_value('19.12.2001')
        self.assertRaises(api.ValidationError, field.validate_value, '19.12.1901')
        self.assertRaises(api.ValidationError, field.validate_value, '45.12.2001')
        self.assertRaises(api.ValidationError, field.validate_value, 'asdf.12.2001')

        self.assertTrue(field.is_null_value(''))
        self.assertTrue(field.is_null_value(None))
        self.assertFalse(field.is_null_value('19.12.2001'))

    def test_gender_field(self):
        field = api.GenderField()
        field.field_name = 'field'

        field.validate_value(0)
        field.validate_value(1)
        field.validate_value(2)

        self.assertRaises(api.ValidationError, field.validate_value, '12')
        self.assertRaises(api.ValidationError, field.validate_value, 3)

        self.assertTrue(field.is_null_value(None))

    def test_client_ids_field(self):
        field = api.ClientIDsField()
        field.field_name = 'field'

        field.validate_value([1,2])
        field.validate_value([])

        self.assertRaises(api.ValidationError, field.validate_value, '123')
        self.assertRaises(api.ValidationError, field.validate_value, [1, '2'])

        self.assertTrue(field.is_null_value(None))
        self.assertTrue(field.is_null_value([]))
        self.assertFalse(field.is_null_value([1,2]))


if __name__ == "__main__":
    unittest.main()
