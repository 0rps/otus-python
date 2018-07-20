import redis
import time
import json
from collections import namedtuple
from functools import wraps
from datetime import datetime, timedelta


CacheRecord = namedtuple('CacheRecord', ['value', 'expire'])
SOCK_TIMEOUT = 1
RECONNECT_ATTEMPTS = 5
RECONNECT_DELAY = 0.1


class StoreConnectionError(Exception):
    pass


def reconnector(func):
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        attempts = 1 + self.reconnect_attempts
        while attempts:
            attempts -= 1
            try:
                return func(self, *args, **kwargs)
            except (redis.ConnectionError, redis.TimeoutError):
                if attempts and self.reconnect_delay:
                    time.sleep(self.reconnect_delay)
        raise StoreConnectionError()
    return wrapper


class StoreConnection:

    def __init__(self, db_index=0, host='localhost', port=6379,
                 socket_timeout=None,
                 reconnect_delay=None,
                 reconnect_attempts=None):
        self.conn = redis.StrictRedis(host=host, port=port, db=db_index,
                                      socket_connect_timeout=socket_timeout,
                                      socket_timeout=socket_timeout)

        self.reconnect_attempts = reconnect_attempts or 0
        self.reconnect_delay = reconnect_delay

    @reconnector
    def get(self, key):
        value = self.conn.get(key)
        return self._decode(value)

    @reconnector
    def set(self, key, value, expire_time=None):
        value = self._encode(value)
        self.conn.set(key, value)
        if expire_time is not None:
            self.conn.expire(key, expire_time)

    def flush(self):
        self.conn.flushdb()

    @staticmethod
    def _encode(value):
        return json.dumps(value)

    @staticmethod
    def _decode(value):
        if value is None:
            return None
        return json.loads(value.decode('utf-8'))


class Store:

    def __init__(self, host='localhost', port=6379):
        self.persistent = StoreConnection(db_index=0, host=host, port=port,
                                          socket_timeout=0.2,
                                          reconnect_delay=0.2,
                                          reconnect_attempts=5)

        self.cache = StoreConnection(db_index=1, host=host, port=port)
        self._is_flush_cache = False

    def get(self, key):
        return self.persistent.get(key)

    def set(self, key, value):
        self.persistent.set(key, value)

    def cache_get(self, key):
        try:
            self._flush_cache()
            value = self.cache.get(key)
            return value
        except StoreConnectionError:
            pass

    def cache_set(self, key, value, expiration_time):
        try:
            self._flush_cache()
            self.cache.set(key, value, expiration_time)
        except StoreConnectionError:
            self._is_flush_cache = True

    def _flush_cache(self):
        if not self._is_flush_cache:
            return

        self.cache.flush()
        self._is_flush_cache = False
