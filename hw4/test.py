import unittest

import api


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

    def test_char_field_validate(self):
        field = api.CharField()
        field.field_name = 'field'
        field.validate_value('19.12.2001')

    def test_char_field_is_null(self):
        field = api.CharField()
        field.field_name = 'field'
        self.assertTrue(field.is_null_value(''))
        self.assertTrue(field.is_null_value(None))
        self.assertFalse(field.is_null_value('19.12.2001'))

    def test_args_field_validate(self):
        field = api.ArgumentsField()
        field.field_name = 'field'

    def test_args_field_is_null(self):
        field = api.ArgumentsField()
        field.field_name = 'field'

    def test_email_field_validate(self):
        field = api.EmailField()
        field.field_name = 'field'

    def test_email_field_is_null(self):
        field = api.EmailField()
        field.field_name = 'field'

    def test_phone_field_validate(self):
        field = api.PhoneField()
        field.field_name = 'field'

    def test_phone_field_is_null(self):
        field = api.PhoneField()
        field.field_name = 'field'

    def test_date_field_validate(self):
        field = api.DateField()
        field.field_name = 'field'

        field.validate_value('19.12.2001')

        self.assertRaises(api.ValidationError, field.validate_value, '45.12.2001')
        self.assertRaises(api.ValidationError, field.validate_value, 'asdf.12.2001')

    def test_date_field_is_null(self):
        field = api.DateField()
        field.field_name = 'field'

        self.assertTrue(field.is_null_value(''))
        self.assertTrue(field.is_null_value(None))
        self.assertFalse(field.is_null_value('19.12.2001'))

    def test_birthday_field_validate(self):
        field = api.BirthDayField()
        field.field_name = 'field'

        field.validate_value('19.12.2001')
        self.assertRaises(api.ValidationError, field.validate_value, '19.12.1901')
        self.assertRaises(api.ValidationError, field.validate_value, '45.12.2001')
        self.assertRaises(api.ValidationError, field.validate_value, 'asdf.12.2001')

        self.assertTrue(field.is_null_value(''))
        self.assertTrue(field.is_null_value(None))
        self.assertFalse(field.is_null_value('19.12.2001'))

    def test_birthday_field_is_null(self):
        field = api.BirthDayField()
        field.field_name = 'field'

        field.validate_value('19.12.2001')
        self.assertRaises(api.ValidationError, field.validate_value, '19.12.1901')
        self.assertRaises(api.ValidationError, field.validate_value, '45.12.2001')
        self.assertRaises(api.ValidationError, field.validate_value, 'asdf.12.2001')

        self.assertTrue(field.is_null_value(''))
        self.assertTrue(field.is_null_value(None))
        self.assertFalse(field.is_null_value('19.12.2001'))

    def test_gender_field_validate(self):
        field = api.GenderField()
        field.field_name = 'field'

        field.validate_value(0)
        field.validate_value(1)
        field.validate_value(2)

        self.assertRaises(api.ValidationError, field.validate_value, '12')
        self.assertRaises(api.ValidationError, field.validate_value, 3)

        self.assertTrue(field.is_null_value(None))

    def test_gender_field_is_null(self):
        field = api.GenderField()
        field.field_name = 'field'

        field.validate_value(0)
        field.validate_value(1)
        field.validate_value(2)

        self.assertRaises(api.ValidationError, field.validate_value, '12')
        self.assertRaises(api.ValidationError, field.validate_value, 3)

        self.assertTrue(field.is_null_value(None))

    def test_client_ids_field_validate(self):
        field = api.ClientIDsField()
        field.field_name = 'field'

        field.validate_value([1,2])
        field.validate_value([])

        self.assertRaises(api.ValidationError, field.validate_value, '123')
        self.assertRaises(api.ValidationError, field.validate_value, [1, '2'])

    def test_client_ids_field_is_null(self):
        field = api.ClientIDsField()
        field.field_name = 'field'

        self.assertTrue(field.is_null_value(None))
        self.assertTrue(field.is_null_value([]))
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
