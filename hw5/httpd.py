import os
import socket
import logging
import datetime
import json
import sys
import threading

import const

from argparse import ArgumentParser

import http_base as http

PACKAGE_SIZE = 1024


def handle_get_request(root_dir, request) -> http.HttpResponse:
    response = handle_head_request(root_dir, request)
    if response.code != const.STATUS_OK:
        return response

    file_path = root_dir + request.route
    with open(file_path, 'rb') as f:
        response.body = f.read()
    return response


def handle_head_request(root_dir, request) -> http.HttpResponse:

    file_path = os.path.normpath(root_dir + request.route)

    if not file_path.startswith(root_dir):
        code = const.STATUS_FORBIDDEN
    elif not os.path.exists(file_path):
        code = const.STATUS_NOT_FOUND
    elif not os.access(file_path, os.R_OK):
        code = const.STATUS_FORBIDDEN
    else:
        code = const.STATUS_OK

    if code != const.STATUS_OK:
        return http.HttpResponse(code, {})

    date = datetime.datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S UTC")
    headers = {
        'Connection': 'close',
        'Date': date,
        'Server': 'MiniServerForOtus v0.1',
        'Content-Length': os.os.stat(file_path).st_size
    }
    ext = os.path.basename(file_path).split('.')[-1]

    response = http.HttpResponse(code, headers, file_type=ext)
    return response


def handle_unknown_request(*args, **kwargs):
    response = http.HttpResponse(const.STATUS_UNKNOWN_METHOD, {})
    return response


class ClientWorker:

    def __init__(self, client_socket: socket.socket, root_dir: str):
        self.socket = client_socket
        self.root_dir = root_dir
        self._buffer = http.HttpRequestBuffer()

    def __call__(self, *args, **kwargs):
        handler_map = {
            'GET': handle_get_request,
            'HEAD': handle_head_request,
        }

        # TODO: сделать возможность приема нескольких запросов
        request = self._receive_request()
        handler = handler_map.get(request.method) or handle_unknown_request
        response = handler(root_dir=self.root_dir, request=request)
        self._send_response(response.to_bytes())
        self.socket.shutdown(socket.SHUT_RDWR)

    def _receive_request(self) -> http.HttpRequest:
        request = self._buffer.pop_request()
        while not request:
            chunk = self.socket.recv(PACKAGE_SIZE)
            if chunk == b'':
                raise RuntimeError("Socket connection broken")
            self._buffer.add_data(chunk)
            request = self._buffer.pop_request()
        return request

    def _send_response(self, response):
        total_sent = 0
        length = len(response)

        logging.info('Try to send response')
        self.socket.sendall(response)
        # while total_sent != length:
        #     sent_bytes = self.socket.sendall(response)
        #     total_sent += sent_bytes
        #     response = response[sent_bytes:]

        logging.info('Response sent')


class Listener:

    def __init__(self, port, workers, backlog, root_dir):
        root_dir = os.path.abspath(root_dir)

        self._workers_count = workers
        self._workers = []

        self._backlog = backlog
        self._server_addr = ('localhost', port)
        self._root_dir = os.path.abspath(root_dir)
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    def run(self):
        self.socket.bind(self._server_addr)
        self.socket.listen(self._backlog)

        while True:
            connection, client_addr = self.socket.accept()
            try:
                self._create_worker(connection, client_addr)
            except Exception as e:
                print(e)
                pass

    def _create_worker(self, connection, client_addr):
        logging.info("New client: %s", client_addr)
        worker = ClientWorker(connection, self._root_dir)
        worker()
        # thread = threading.Thread(target=worker)
        # thread.start()

        # self._workers.append(thread)


def main(config):
    listener = Listener(config['port'], config['workers'], config['backlog'], config['directory'])
    listener.run()


def read_config(config_file):
    with open(config_file, 'r') as f:
        return json.load(f)


if __name__ == '__main__':
    ap = ArgumentParser()
    ap.add_argument('-d', '--directory', default='.')
    ap.add_argument("-c", "--config", nargs='?', const='config.json', default=None)
    ap.add_argument("-l", "--log", default=None)
    args = ap.parse_args()

    if args.config:
        config = read_config(args.config)
    else:
        config = {
            'directory': args.directory,
            'workers': 5,
            'port': 12222,
            'backlog': 10,
            'log': args.log
        }

    logging.basicConfig(filename=config['log'],
                        level=logging.INFO,
                        format='[%(asctime)s] %(levelname).1s %(message)s',
                        datefmt='%Y.%m.%d %H:%M:%S')

    logging.info("Start configuration %s", config)
    try:
        main(config)
    except Exception as ex:
        logging.exception(ex)
        raise
