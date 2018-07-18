import unittest
import subprocess
import redis
import time
import os
import json
from http.client import HTTPConnection

import api
import store

from test_utils import set_valid_auth


class TestSuite(unittest.TestCase):

    api_server_host = '127.0.0.1'
    api_server_port = '8080'
    redis_server_host = '127.0.0.1'
    redis_server_port = '6379'

    time_wait = 0.2

    def setUp(self):
        self.redis = self.start_redis()
        self.server = self.start_api_server()

        self.store = store.Store(self.redis_server_host,
                                 self.redis_server_port)

        # flush store
        self.store.persistent.flush()
        self.store.cache.flush()

    def tearDown(self):
        self.redis.kill()
        self.server.kill()

    def restart_redis(self):
        self.redis.kill()
        self.redis = self.start_redis()

    def start_redis(self):
        redis_proc = subprocess.Popen(['redis-server', '--port', str(self.redis_server_port)],
                                      stdout=subprocess.DEVNULL)

        counter = 0
        while True:
            sr = redis.StrictRedis(host=self.redis_server_host, port=self.redis_server_port)
            try:
                sr.ping()
                break
            except (redis.ConnectionError, redis.TimeoutError) as ex:
                if counter == 5:
                    raise ex
                time.sleep(self.time_wait)
                counter += 1

        try:
            redis_proc.wait(self.time_wait)
            raise Exception('Redis is not started')
        except subprocess.TimeoutExpired:
            pass

        return redis_proc

    def start_api_server(self):
        dir_path = os.path.dirname(os.path.abspath(__file__))
        api_path = os.path.join(dir_path, 'api.py')

        redis_config = '{}:{}'.format(self.redis_server_host,
                                      self.redis_server_port)

        server_cmd_start = ['python3', api_path,
                            '-p', str(self.api_server_port),
                            '-s', redis_config]
        server_proc = subprocess.Popen(server_cmd_start)

        counter = 0
        while True:
            conn = HTTPConnection(self.api_server_host,
                                  port=self.api_server_port)
            try:
                conn.connect()
                conn.request('GET', '/')
            except (TimeoutError, ConnectionRefusedError) as ex:
                if counter == 5:
                    raise ex
                time.sleep(self.time_wait)
                counter += 1
            else:
                break

        try:
            server_proc.wait(self.time_wait)
            raise Exception('API server is not started')
        except subprocess.TimeoutExpired:
            pass

        return server_proc

    def test_nothing(self):
        pass

    def make_request(self, data, to_json=True, method=None):
        url = method or 'method'
        url = '/' + url

        headers = {}
        if to_json:
            headers['Content-Type'] = 'application/json'
            data = json.dumps(data)
        conn = HTTPConnection(self.api_server_host, self.api_server_port)
        conn.request(method='POST', url=url, body=data, headers=headers)

        response = conn.getresponse()
        status, response = response.status, response.read()

        try:
            response = json.loads(response.decode('utf-8'))
        except Exception as e:
            pass

        conn.close()

        return status, response

    def test_wrond_data(self):
        code, _ = self.make_request("1'2 {]", to_json=False)
        self.assertEqual(code, api.BAD_REQUEST)

    def test_wrong_url(self):
        code, _ = self.make_request({'data': '1'}, method='unknown_method')
        self.assertEqual(code, api.NOT_FOUND)

    def test_online_score_valid(self):
        arguments = {"gender": 1, "birthday": "01.01.2000",
                     "first_name": "a", "last_name": "b"}
        request = {"account": "horns&hoofs", "login": "h&f",
                   "method": "online_score", "arguments": arguments}
        set_valid_auth(request)

        code, response = self.make_request(request)
        self.assertEqual(code, api.OK)
        score_1 = response['response']['score']

        # with cache
        code, response = self.make_request(request)
        self.assertEqual(code, api.OK)
        score_2 = response['response']['score']
        self.assertAlmostEqual(score_1, score_2)

    def test_online_score_valid_with_trouble_cache(self):
        arguments = {"gender": 1, "birthday": "01.01.2000",
                     "first_name": "a", "last_name": "b"}
        request = {"account": "horns&hoofs", "login": "h&f",
                   "method": "online_score", "arguments": arguments}
        set_valid_auth(request)

        code, response = self.make_request(request)
        self.assertEqual(code, api.OK)
        score_1 = response['response']['score']

        # stop cache
        self.redis.kill()
        code, response = self.make_request(request)
        self.assertEqual(code, api.OK)
        score_2 = response['response']['score']
        self.assertAlmostEqual(score_1, score_2)

        # start cache
        self.restart_redis()
        code, response = self.make_request(request)
        self.assertEqual(code, api.OK)
        score_3 = response['response']['score']
        self.assertAlmostEqual(score_2, score_3)

    def test_online_score_validation_error(self):
        arguments = {"gender": 1, "birthday": "01.01.2000",
                     "first_name": "a", "last_name": "b"}
        request = {"account": "horns&hoofs", "login": "h&f",
                   "method": "online_score", "arguments": arguments}

        arguments['gender'] = 4
        arguments['birthday'] = '01.01.1910'
        set_valid_auth(request)

        code, _ = self.make_request(request)
        self.assertEqual(code, api.INVALID_REQUEST)

    def test_online_score_auth_error(self):
        arguments = {"gender": 1, "birthday": "01.01.2000",
                     "first_name": "a", "last_name": "b"}
        request = {'token': '123456', "account": "horns&hoofs",
                   "login": "h&f", "method": "online_score",
                   "arguments": arguments}

        code, response = self.make_request(request)
        self.assertEqual(code, api.FORBIDDEN)

    def test_client_interests_valid(self):
        interests = {1: ['ball', 'uveball', 'noneball'],
                     2: ['teststring']}
        for key, value in interests.items():
            self.store.set('i:{}'.format(key), json.dumps(value))

        ids = list(interests.keys())
        arguments = {"client_ids": ids, "date": "19.07.2017"}
        request = {"account": "horns&hoofs", "login": "h&f",
                   "method": "clients_interests",
                   "arguments": arguments}
        set_valid_auth(request)

        code, response = self.make_request(request)
        self.assertEqual(api.OK, code)

    def test_client_interests_trouble_store(self):
        interests = {1: ['ball', 'uveball', 'noneball'],
                     2: ['teststring']}
        for key, value in interests.items():
            self.store.set('i:{}'.format(key), json.dumps(value))

        ids = list(interests.keys())
        arguments = {"client_ids": ids, "date": "19.07.2017"}
        request = {"account": "horns&hoofs", "login": "h&f",
                   "method": "clients_interests",
                   "arguments": arguments}
        set_valid_auth(request)

        self.redis.kill()
        code, response = self.make_request(request)
        self.assertEqual(api.INTERNAL_ERROR, code)

        self.restart_redis()
        code, response = self.make_request(request)
        self.assertEqual(api.OK, code)


if __name__ == "__main__":
    unittest.main()
