HTTP_VERSION = 'HTTP/1.1'


class HttpRequestError(Exception):
    pass


class UnsupportedHttpVersion(HttpRequestError):
    pass


class HttpResponse:

    def __init__(self, code, status, headers, body=None):
        self.code = code
        self.status = status
        self.headers = headers
        self.body = body

    def to_bytearray(self):
        pass


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
            key, value = line.split(': ')
            headers[key] = value

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