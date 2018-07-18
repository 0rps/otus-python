import unittest
from unittest import mock
import store
import api
import json
import redis

from test_utils import cases, set_valid_auth


class IntergationTestsMethodsWithStore(unittest.TestCase):

    def setUp(self):
        self.context = {}
        self.headers = {}

        self.store = store.Store()

    def tearDown(self):
        self.store.persistent.flush()
        self.store.cache.flush()

    @cases([
        {"phone": "79175002040", "email": "tt@tt"},
        {"gender": 1, "birthday": "01.01.2000", "first_name": "a", "last_name": "b"},
    ])
    def test_method_online_score(self, arguments):
        request = {"account": "horns&hoofs", "login": "h&f",
                   "method": "online_score", "arguments": arguments}
        set_valid_auth(request)
        _, code = api.method_handler({"body": request, "headers": self.headers},
                                     self.context,
                                     self.store)

        self.assertEqual(code, api.OK)

    @cases([
        {"phone": "79175002040", "email": "tt@tt"},
        {"gender": 1, "birthday": "01.01.2000", "first_name": "a", "last_name": "b"},
    ])
    def test_online_score_store_unavailable(self, arguments):
        request = {"account": "horns&hoofs", "login": "h&f",
                   "method": "online_score", "arguments": arguments}
        set_valid_auth(request)

        with mock.patch('redis.StrictRedis.get') as redis_get:
            redis_get.side_effect = redis.ConnectionError
            _, code = api.method_handler({"body": request,
                                          "headers": self.headers},
                                         self.context,
                                         self.store)

            self.assertEqual(code, api.OK)

    def test_client_interests(self):
        interests = {
            1: ['football', 'baseball'],
            2: ['gym']
        }
        for key, value in interests.items():
            self.store.set('i:{}'.format(key), json.dumps(value))

        ids = list(interests.keys())
        arguments = {"client_ids": ids, "date": "19.07.2017"}
        request = {"account": "horns&hoofs", "login": "h&f",
                   "method": "clients_interests", "arguments": arguments}
        set_valid_auth(request)
        response, code = api.method_handler({"body": request, "headers": self.headers},
                                            self.context,
                                            self.store)

        self.assertEqual(code, api.OK)
        self.assertDictEqual(response, interests)

    def test_client_interests_store_unavailable(self):
        interests = {
            1: ['football', 'baseball'],
            2: ['gym']
        }
        for key, value in interests.items():
            self.store.set('i:{}'.format(key), json.dumps(value))

        ids = list(interests.keys())
        arguments = {"client_ids": ids, "date": "19.07.2017"}
        request = {"account": "horns&hoofs", "login": "h&f",
                   "method": "clients_interests", "arguments": arguments}
        set_valid_auth(request)

        with mock.patch('redis.StrictRedis.get') as redis_get:
            redis_get.side_effect = redis.ConnectionError
            self.assertRaises(store.StoreConnectionError,
                              api.method_handler,
                              {"body": request, "headers": self.headers},
                              self.context, self.store)