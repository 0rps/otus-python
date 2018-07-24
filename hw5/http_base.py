import os
import datetime
import urllib.parse
import mimetypes

HTTP_VERSION = 'HTTP/1.1'
STATUS_OK = 200
STATUS_INVALID = 400
STATUS_FORBIDDEN = 403
STATUS_NOT_FOUND = 404
STATUS_UNKNOWN_METHOD = 405

STATUS_MAP = {
    STATUS_OK: 'OK',
    STATUS_INVALID: 'Invalid Request',
    STATUS_FORBIDDEN: 'Forbidden',
    STATUS_NOT_FOUND: 'Not Found',
    STATUS_UNKNOWN_METHOD: 'Unknown Method'
}


MAX_REQUEST_LENGTH = 3072


class HttpRequestError(Exception):
    pass


class HttpResponse:

    # TODO: использовать модуль mimetypes
    content_map = {
        'html': 'text/html',
        'css': 'text/css',
        'js': 'application/javascript',
        'jpeg': 'image/jpeg',
        'jpg': 'image/jpeg',
        'png': 'image/png',
        'gif': 'image/gif',
        'swf': 'application/x-shockwave-flash'
    }

    def __init__(self, code, headers=None, mimetype=None, body=None):
        self.code = code
        self.headers = headers or {}
        self.body = body
        self.mimetype = mimetype

    def to_bytes(self):
        head = '{} {} {}'.format(HTTP_VERSION, self.code, STATUS_MAP[self.code])

        body = None
        if self.body:
            body = self.body.encode('utf-8') if isinstance(self.body, str) else self.body
            body_length = len(body)

            self.headers['Content-Length'] = body_length
            self.headers['Content-Type'] = self.mimetype

        headers = ['{}: {}'.format(k, v) for k, v in self.headers.items()]

        response = '\r\n'.join([head, *headers]) + '\r\n\r\n'
        if body:
            response = response.encode('utf-8') + body
        else:
            response = response.encode('utf-8')
        return response


class HttpRequest:

    def __init__(self, method, route, params, version, headers, body):
        self.method = method
        self.route = route
        self.params = params
        self.version = version
        self.headers = headers
        self.body = body

    @classmethod
    def from_raw_data(cls, request_line, headers, body):
        try:
            method, route, version = request_line.split(' ')
        except ValueError:
            raise HttpRequestError('Invalid format of request line: "{}"'.format(request_line))

        if not version.startswith('HTTP/'):
            raise HttpRequestError("Invalid http version")

        args = None
        if '?' in route:
            route, args = route.split('?')

        if route.endswith('/'):
            route += 'index.html'

        route = urllib.parse.unquote(route)
        return cls(method, route, version, args, headers, body)


def handle_get_request(root_dir, request) -> HttpResponse:
    response = handle_head_request(root_dir, request)
    if response.code != STATUS_OK:
        return response

    file_path = root_dir + request.route
    with open(file_path, 'rb') as f:
        response.body = f.read()
    return response


def handle_head_request(root_dir, request) -> HttpResponse:
    route = request.route.lstrip('/')
    file_path = os.path.normpath(os.path.join(root_dir, route))

    if not file_path.startswith(root_dir):
        code = STATUS_FORBIDDEN
    elif not os.path.exists(file_path):
        code = STATUS_NOT_FOUND
    elif not os.access(file_path, os.R_OK):
        code = STATUS_FORBIDDEN
    else:
        code = STATUS_OK

    if code != STATUS_OK:
        return HttpResponse(code, {})

    date = datetime.datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S UTC")
    headers = {
        'Connection': 'close',
        'Date': date,
        'Server': 'MiniServerForOtus v0.1',
        'Content-Length': os.stat(file_path).st_size
    }
    mimetype, _ = mimetypes.guess_type(file_path)
    response = HttpResponse(code, headers, mimetype=mimetype)
    return response


def handle_unknown_request(*args, **kwargs):
    response = HttpResponse(STATUS_UNKNOWN_METHOD, {})
    return response


class HttpRequestBuffer:

    def __init__(self):
        self.data = bytearray()

    def add_data(self, bytes_data):
        self.data.extend(bytes_data)

    def pop_request(self):

        if b'\r\n\r\n' in self.data:
            return self._parse_request()

        if len(self.data) > MAX_REQUEST_LENGTH:
            raise HttpRequestError("Length of request is exceeded")

    def clear(self):
        self.data = bytearray()

    def _parse_request(self):
        head, body = self.data.split(b'\r\n\r\n')[:2]

        try:
            head = head.decode()
        except UnicodeDecodeError:
            raise HttpRequestError('Wrong head encoding')

        head_lines = head.split('\r\n')
        request_line = head_lines[0]
        headers = {}
        for line in head_lines[1:]:
            index = line.find(':')
            if index < 1:
                raise HttpRequestError('Wrong header: "{}"'.format(line))
            key, value = line[:index], line[index+1:]
            headers[key] = value.strip()

        if 'Content-Length' not in headers:
            return HttpRequest.from_raw_data(request_line, headers, None)

        try:
            length = int(headers['Content-Length'])
        except ValueError:
            raise HttpRequestError('Wrong format of Content-Length value: "{}"'.format(headers['Content-Length']))

        if len(body) > length:
            body = body[:length]
            try:
                body = body.decode()
            except UnicodeDecodeError:
                raise HttpRequestError('Wrong body encoding')
            request_length = len(head) + length + 4
            self.data = self.data[request_length:]
        elif len(body) < length:
            return

        return HttpRequest.from_raw_data(request_line, headers, body)
