import redis
import time
import json
from collections import namedtuple
from datetime import datetime, timedelta


CacheRecord = namedtuple('CacheRecord', ['value', 'expire'])
SOCK_TIMEOUT = 1
RECONNECT_ATTEMPTS = 5
RECONNECT_DELAY = 0.1


class StoreConnectionError(Exception):
    pass


class StoreConnection:

    def __init__(self, db_index=0, host='localhost', port=6379,
                 socket_timeout=None,
                 reconnect_delay=None,
                 reconnect_attempts=None):
        self.conn = redis.StrictRedis(host=host, port=port, db=db_index,
                                      socket_connect_timeout=socket_timeout,
                                      socket_timeout=socket_timeout)

        self._reconnect_attempts = reconnect_attempts or 0
        self._reconnect_delay = reconnect_delay

    def get(self, key):
        value = self._reconnect_wrapper(self.conn.get, [key])
        value = value.decode('utf-8')
        return json.loads(value)

    def _reconnect_wrapper(self, func, args):
        attempts = 1 + self._reconnect_attempts
        while attempts:
            attempts -= 1
            try:
                return func(*args)
            except (redis.ConnectionError, redis.TimeoutError):
                if attempts and self._reconnect_delay:
                    time.sleep(self._reconnect_delay)

        raise StoreConnectionError()

    def set(self, key, value):
        value = json.dumps(value)
        self._reconnect_wrapper(self.conn.set, [key, value])

    def service_flush(self):
        pass


class Store:

    def __init__(self, host='localhost', port=6379):
        self.store = StoreConnection(db_index=0, host=host, port=port,
                                     socket_timeout=0.2,
                                     reconnect_delay=0.2,
                                     reconnect_attempts=5)

    def get(self, key):
        return self.store.get(key)

    def set(self, key, value):
        self.store.set(key, value)

    def cache_get(self, key):
        pass

    def cache_set(self, key, value, expiration_time):
        pass

