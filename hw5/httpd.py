import os
import socket
import logging
import sys
import threading

from optparse import OptionParser

from . import http


PACKAGE_SIZE = 128


def handle_get_request(root_dir, request):
    response = handle_head_request(root_dir, request)
    if response.code != 200:
        return response

    file_path = root_dir + request.route
    with open(file_path, 'rb') as f:
        content = f.readall()

    ext = os.path.basename(file_path).split('.')[-1]
    response.file_type = ext
    response.body = content
    return response


def handle_head_request(root_dir, request):
    headers = {
        'Connection': 'Closed'
    }

    file_path = os.path.normpath(root_dir + request.route)

    if not os.path.exists(file_path):
        code = 404
    elif not file_path.startswith(root_dir):
        code = 403
    else:
        try:
            f = open(file_path, 'rb')
            f.close()
            code = 200
        except IOError:
            code = 403

    if code != 200:
        return http.HttpResponse(code, headers)

    headers['Date'] = 'Sun, 18 Oct 2012 10:36:20 GMT'
    headers['Server'] = 'Apache/2.2.14 (Win32)'

    response = http.HttpResponse(code, headers)
    return response


def handle_unknown_request(request):
    headers = {'Connection': 'Closed'}
    response = http.HttpResponse(405, headers)
    return response


class ClientWorker:

    def __init__(self, client_socket):
        self.socket = client_socket
        self._buffer = http.HttpRequestBuffer()

    def __call__(self, *args, **kwargs):
        handler_map = {
            'GET': handle_get_request,
            'HEAD': handle_head_request,
        }

        # TODO: сделать возможность приема нескольких запросов
        request = self._receive_request()
        handler = handler_map.get(request.type) or handle_unknown_request
        response = handler(request=request)
        self._send_response(response.to_bytes())

    def _receive_request(self):
        request = self._buffer.pop_request()
        while not request:
            chunk = self.socket.recv(PACKAGE_SIZE)
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
            sent_count = min(len(response), PACKAGE_SIZE)
            sent_bytes = self.socket.send(response, sent_count)
            total_sent += sent_bytes
            response = response[sent_bytes:]

        logging.info('Response sent')


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
