from argparse import ArgumentParser
import os
import socket
import logging
import json
import threading
import queue

import const
import http_base as http

PACKAGE_SIZE = 1024


class ClientWorker:

    def __init__(self, root_dir: str, common_queue: queue.Queue):
        self.socket = None
        self.addr = None

        self.buffer = http.HttpRequestBuffer()
        self.root_dir = root_dir
        self.queue = common_queue

    def __call__(self, *args, **kwargs):
        logging.info("worker started")
        while True:
            client_socket, client_addr = self.queue.get()
            logging.info("Start handling client: %s", client_addr)
            self.socket = client_socket
            self.buffer.clear()
            try:
                self._handle_request()
            except Exception as ex:
                logging.error("Something went wrong on: %s", client_addr)
                logging.exception(ex)
                # close socket

    def _handle_request(self):
        handler_map = {
            'GET': http.handle_get_request,
            'HEAD': http.handle_head_request,
        }

        # TODO: сделать возможность приема нескольких запросов
        request = self._receive_request()

        logging.info("Request: %s %s from %s", request.method, request.route, self.addr)

        handler = handler_map.get(request.method) or http.handle_unknown_request
        response = handler(root_dir=self.root_dir, request=request)

        logging.info("Response: %s for %s", response.code, self.addr)

        self._send_response(response)
        self.socket.shutdown(socket.SHUT_RDWR)

    def _receive_request(self) -> http.HttpRequest:
        request = self.buffer.pop_request()
        while not request:
            chunk = self.socket.recv(PACKAGE_SIZE)
            if chunk == b'':
                raise RuntimeError("Socket connection broken")
            self.buffer.add_data(chunk)
            request = self.buffer.pop_request()
        return request

    def _send_response(self, response):
        self.socket.sendall(response.to_bytes())


class Listener:

    def __init__(self, common_queue: queue.Queue, port, backlog):

        self.queue = common_queue

        self.backlog = backlog
        self.server_addr = ('localhost', port)
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    def run(self):
        self.socket.bind(self.server_addr)
        self.socket.listen(self.backlog)

        while True:
            connection, client_addr = self.socket.accept()
            self.queue.put((connection, client_addr))


def main(config):
    workers_count = config['workers']
    root_dir = os.path.abspath(config['directory'])
    common_queue = queue.Queue()

    workers = []

    for _ in range(workers_count):
        worker = threading.Thread(target=ClientWorker(root_dir, common_queue))
        workers.append(worker)
        worker.start()

    listener = Listener(common_queue, config['port'], config['backlog'])
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
                        format='[%(asctime)s] (%(threadName)-10s) %(levelname).1s %(message)s',
                        datefmt='%Y.%m.%d %H:%M:%S')

    logging.info("Start configuration %s", config)
    try:
        main(config)
    except Exception as ex:
        logging.exception(ex)
        raise
