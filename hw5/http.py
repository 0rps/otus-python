HTTP_VERSION = 'HTTP/1.1'


class HttpRequestError(Exception):
    pass


class UnsupportedHttpVersion(HttpRequestError):
    pass


class HttpResponse:

    content_map = {
        'html': 'text/html; charset=utf-8',
        'css': 'text/css; charset=utf-8',
        'js': 'application/javascript; charser=utf-8',
        'jpeg': 'image/jpeg',
        'jpg': 'image/jpeg',
        'png': 'image/png',
        'gif': 'image/gif',
        'swf': 'application/x-shockwave-flash'
    }

    codes_map = {
        200: 'OK',
        403: 'Forbidden',
        404: 'Not Found',
        405: 'Method Not Allowed',
    }

    def __init__(self, code, headers, file_type=None, body=None):
        self.code = code
        self.headers = headers or {}
        self.body = body
        self.file_type = file_type

    def to_bytes(self):
        head = '{} {} {}'.format(HTTP_VERSION, self.code, self.codes_map[self.code])

        body = None
        if self.body:
            body = self.body.encode('utf-8') if isinstance(self.body, str) else self.body
            mime_type = self.content_map.get(self.file_type) or 'application/octet-stream'
            body_length = len(body)

            self.headers['Content-Length'] = body_length
            self.headers['Content-Type'] = mime_type

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

    @staticmethod
    def from_raw_data(request_line, headers, body):
        method, route, version = request_line.split(' ')
        if version != HTTP_VERSION:
            raise UnsupportedHttpVersion()

        args = None
        if '?' in route:
            route, args = route.split('?')

        if route.endswith('/'):
            route += 'index.html'

        return HttpRequest(method, route, version, args, headers, body)


class HttpRequestBuffer:

    def __init__(self):
        self.data = bytearray()

    def add_data(self, bytes_data):
        self.data.extend(bytes_data)

    def pop_request(self):
        if b'\r\n\r\n' in self.data:
            return self._parse_request()

    def _parse_request(self):
        data = self.data.decode()
        head, body = data.split('\r\n\r\n')[:2]

        head_lines = head.split('\r\n')

        request_line = head_lines[0]
        headers = {}
        for line in head_lines[1:]:
            key, value = line.split(':')
            headers[key] = value.strip()

        if 'Content-Length' not in headers:
            return HttpRequest.from_raw_data(request_line, headers, None)

        length = int(headers['Content-Length'])
        if len(body) > length:
            body = body[:length]
            request_length = len(head) + length + 4
            self.data = self.data[request_length:]
        elif len(body) < length:
            return

        return HttpRequest.from_raw_data(request_line, headers, body)