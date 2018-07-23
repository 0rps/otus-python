import functools
import hashlib
import sys
import logging
from datetime import datetime

import api


def cases(cases):
    def decorator(f):
        @functools.wraps(f)
        def wrapper(*args):
            for c in cases:
                new_args = args + (c if isinstance(c, tuple) else (c,))
                try:
                    f(*new_args)
                except AssertionError as ex:
                    args_string = ', '.join(str(x) for x in new_args[1:])
                    func_with_args = '.\nFunction with arguments: {}({}).\n'.format(f.__name__, args_string)
                    raise AssertionError(str(ex) + func_with_args).with_traceback(ex.__traceback__)
        return wrapper
    return decorator


def set_valid_auth(request):
    if request.get("login") == api.ADMIN_LOGIN:
        msg = (datetime.now().strftime("%Y%m%d%H") +
               api.ADMIN_SALT).encode('utf-8')
        request["token"] = hashlib.sha512(msg).hexdigest()
    else:
        msg = request.get("account", "") + request.get("login", "") + api.SALT
        msg = msg.encode('utf-8')
        request["token"] = hashlib.sha512(msg).hexdigest()
