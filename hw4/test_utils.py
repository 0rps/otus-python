import functools
import api
import hashlib
from datetime import datetime


def cases(cases):
    def decorator(f):
        @functools.wraps(f)
        def wrapper(*args):
            for c in cases:
                new_args = args + (c if isinstance(c, tuple) else (c,))
                try:
                    f(*new_args)
                except Exception as ex:
                    args_string = ', '.join(str(x) for x in new_args[1:])
                    raise Exception('Error in : {}({})'.format(f.__name__, args_string)) from ex
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
