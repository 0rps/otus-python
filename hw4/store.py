import tarantool
from collections import namedtuple
from datetime import datetime, timedelta


CacheRecord = namedtuple('CacheRecord', ['value', 'expire'])
SOCK_TIMEOUT = 1
RECONNECT_ATTEMPTS = 5
RECONNECT_DELAY = 0.1


class Store:

    def __init__(self, host='localhost', port=3301):
        self._store_conn = tarantool.Connection(host, port,
                                                socket_timeout=SOCK_TIMEOUT,
                                                reconnect_max_attempts=RECONNECT_ATTEMPTS,
                                                reconnect_delay=RECONNECT_DELAY,
                                                connect_now=False)
        self._cache_conn = tarantool.Connection(host, port,
                                                socket_timeout=SOCK_TIMEOUT,
                                                connect_now=False)
        self._cache_space_name = 'cache'
        self._store_space_name = 'store'
        self._store = None
        self._cache = None

    def get(self, key):
        return self._get(key, True)

    def set(self, key, value):
        self._set(key, value, True)

    def cache_get(self, key):
        try:
            response = self._cache.select(key)
        except tarantool.Error:
            return None

        value, time = response
        if time >= datetime.utcnow():
            return value

        self._cache.delete(key)

    def cache_set(self, key, value, seconds):
        self._cache_connect()
        if self._cache is None:
            return

        expiration_time = datetime.now() + timedelta(seconds=seconds)
        try:
            self._cache.upsert(key, (value, expiration_time))
        except tarantool.Error:
            self._cache = None

    def _set(self, key, value, another_try):
        self._store_connect()

        try:
            response = self._store.upsert(key, value)
        except tarantool.NetworkError:
            if not another_try:
                raise

            self._store = None
            return self._set(key, value, False)
        return response

    def _get(self, key, another_try):
        self._store_connect()

        try:
            response = self._store.select(key)
        except tarantool.NetworkError:
            if not another_try:
                raise

            self._store = None
            return self._get(key, False)

        return response

    def _store_connect(self):
        if self._store is not None:
            return

        self._store_conn.connect()
        self._store = self._store_conn.space(self._cache_space_name)

    def _cache_connect(self):
        if self._cache is not None:
            return

        try:
            self._cache_conn.connect()
        except tarantool.NetworkError:
            return

        try:
            self._cache = self._cache_conn.space(self._cache_space_name)
        except tarantool.NetworkError:
            return
