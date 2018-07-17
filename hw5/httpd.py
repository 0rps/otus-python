import socket
import logging
import sys
import threading

from optparse import OptionParser


DATASIZE = 128


class ParseException(Exception):
    pass


class HttpResponse:

    def __init__(self):
        pass


class HttpRequest:

    def __init__(self, request_type, route, headers, body=None):
        self._type = request_type
        self._route = route
        self._headers = headers
        self._body = body

    @property
    def type(self):
        return self._type

    @property
    def route(self):
        return self._route

    @property
    def headers(self):
        return self._headers

    @property
    def body(self):
        return self._body

    def is_valid(self):
        return True


def handle_get_request(request):
    response = b'HTTP/1.1 400 Bad Request\r\n' \
               b'Date: Sun, 18 Oct 2012 10:36:20 GMT\r\n' \
               b'Server: Apache/2.2.14 (Win32)\r\n' \
               b'Content-Type: text/html; charset=iso-8859-1\r\n' \
               b'Connection: Closed\r\n\r\n'
    return response


def handle_head_request(request):
    response = b'HTTP/1.1 400 Bad Request\r\n' \
               b'Date: Sun, 18 Oct 2012 10:36:20 GMT\r\n' \
               b'Server: Apache/2.2.14 (Win32)\r\n' \
               b'Content-Type: text/html; charset=iso-8859-1\r\n' \
               b'Connection: Closed\r\n\r\n'
    return response


def handle_unknown_request(request):
    response = b'HTTP/1.1 400 Bad Request\r\n' \
               b'Date: Sun, 18 Oct 2012 10:36:20 GMT\r\n' \
               b'Server: Apache/2.2.14 (Win32)\r\n' \
               b'Content-Type: text/html; charset=iso-8859-1\r\n' \
               b'Connection: Closed\r\n\r\n'
    return response


class HttpRequestBuffer:

    def __init__(self):
        self.data = bytearray()

    def add_data(self, bytes_data):
        self.data.extend(bytes_data)

    def pop_request(self):
        if b'\r\n\r\n' in self.data:
            logging.info('Double-n sequence detected')
            return self._parse_request()

    def _parse_request(self):
        data = self.data.decode()
        head, body = data.split('\r\n\r\n')[:2]

        head_lines = head.split('\r\n')
        request_type, route, version = head_lines[0].split(' ')

        headers = {}
        for line in head_lines[1:]:
            key, value = line.split(': ')
            headers[key] = value

        if route.endswith('/'):
            route += 'index.html'

        if 'Content-Length' not in headers:
            return HttpRequest(request_type, route, headers)

        length = int(headers['Content-length'])
        if len(body) > length:
            body = body[:length]
            request_length = len(head) + length + 4
            self.data = self.data[request_length:]
        elif len(body) < length:
            return

        return HttpRequest(request_type, route, headers, body)


class ClientWorker:
    def __init__(self, client_socket):
        self.socket = client_socket
        self._buffer = HttpRequestBuffer()

    def __call__(self, *args, **kwargs):
        handler_map = {
            'GET': handle_get_request,
            'HEAD': handle_head_request,
        }

        # TODO: сделать возможность приема нескольких запросов
        request = self._receive_request()
        handler = handler_map.get(request.type) or handle_unknown_request
        response = handler(request=request)
        self._send_response(response)

    def _receive_request(self):
        request = self._buffer.pop_request()
        while not request:
            chunk = self.socket.recv(DATASIZE)
            if chunk == b'':
                raise RuntimeError("socket connection broken")
            self._buffer.add_data(chunk)
            request = self._buffer.pop_request()
        return request

    def _send_response(self, response):
        total_sent = 0
        length = len(response)

        logging.info('Try to send response')
        while total_sent != length:
            sent_count = min(len(response), DATASIZE)
            sent_bytes = self.socket.send(response, sent_count)
            total_sent += sent_bytes
            response = response[sent_bytes:]

        logging.info('Reponse sent')


class Listener:

    def __init__(self, host, port, backlog):
        self._workers = []

        self._backlog = backlog
        self._server_addr = (host, port)
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    def run(self):
        self.socket.bind(self._server_addr)
        self.socket.listen(self._backlog)

        while True:
            connection, client_addr = self.socket.accept()
            self._create_worker(connection, client_addr)

    def _create_worker(self, connection, client_addr):
        logging.info("New client: {}".format(client_addr))
        worker = ClientWorker(connection)
        worker()
        # thread = threading.Thread(target=worker)
        # thread.start()

        # self._workers.append(thread)


def main(args):
    port = 12222
    host = 'localhost'
    backlog = 10
    listener = Listener(host, port, 10)
    listener.run()


if __name__ == '__main__':

    op = OptionParser()
    # op.add_option("-h", "--host", action="store", type=str, default='*')
    # op.add_option("-p", "--port", action="store", type=int, default=12222)
    op.add_option("-l", "--log", action="store", default=None)
    (opts, args) = op.parse_args()

    logging.basicConfig(filename=opts.log, level=logging.INFO,
                        format='[%(asctime)s] %(levelname).1s %(message)s',
                        datefmt='%Y.%m.%d %H:%M:%S')

    args = []
    try:
        main(args)
    except Exception as ex:
        logging.exception(ex)
        raise
