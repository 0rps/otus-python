import unittest
import datetime
import functools
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

    #mock datetime now
    @cases(['19.12.2001'])
    def test_birthday_field_validate_no_raise(self, arg):
        field = api.BirthDayField()
        field.field_name = 'field'
        field.validate_value(arg)

    @cases(['19.12.1901', '45.12.2001', 'asdf.12.2001'])
    def test_birthday_field_validate_raise(self, arg):
        field = api.BirthDayField()
        field.field_name = 'field'
        self.assertRaises(api.ValidationError, field.validate_value, arg)

    @cases(['', None])
    def test_birthday_field_is_null_true(self, arg):
        field = api.BirthDayField()
        field.field_name = 'field'
        self.assertTrue(field.is_null_value(arg))
        self.assertTrue(field.is_null_value(None))

    def test_birthday_field_is_null_false(self):
        field = api.BirthDayField()
        field.field_name = 'field'
        self.assertFalse(field.is_null_value('19.12.2001'))

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

    def test_request_field_validation(self):
        pass

    def test_client_interests_ctx(self):
        pass

    def test_client_interests(self):
        pass

    def test_online_score_validation(self):
        pass

    def test_online_score_ctx(self):
        pass

    def test_online_score_admin(self):
        pass

    def test_online_score(self):
        pass

    def test_method_auth(self):
        pass

    def test_method_routing(self):
        pass


if __name__ == "__main__":
    unittest.main()
