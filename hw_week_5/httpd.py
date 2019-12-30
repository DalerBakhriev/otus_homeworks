"""
Entry point to my onw server program
"""

import argparse
import logging
import multiprocessing as mp
import os
import select
import socket
import time
from typing import NoReturn, Optional, Tuple

SERVER_ADDRESS = "localhost"
SERVER_PORT = 8080
CONNECTIONS_LIMIT = 100000
FORBIDDEN = 403
NOT_FOUND = 404
METHOD_NOT_ALLOWED = 405
OK = 200

logging.getLogger().setLevel(logging.DEBUG)


class AsyncHTTPServer:

    """
    My own realization of http server
    """

    response_status_codes = {
        OK: "OK",
        FORBIDDEN: "Forbidden",
        NOT_FOUND: "Not Found",
        METHOD_NOT_ALLOWED: "Method Not Allowed"
    }

    response_content_types = {
        ".css": "text/css",
        ".html": "text/html",
        ".js": "application/javascript",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".gif": "image/gif",
        ".swf": "application/x-shockwave-flash"
    }

    address_family = socket.AF_INET
    socket_type = socket.SOCK_STREAM
    allowed_methods = ("get", "head")
    allowed_file_extensions = (".html", ".css", ".js", ".jpg", ".jpeg", ".png", ".gif", ".swf")
    EOL1 = b'\n\n'
    EOL2 = b'\n\r\n'
    SERVER_NAME = "Daler.Bakhriev"

    def __init__(self,
                 server_address: str,
                 server_port: int,
                 connections_limit: int,
                 root_dir: str):

        self.socket = socket.socket(self.address_family, self.socket_type)
        self.server_address = server_address
        self.server_port = server_port
        self.connections_limit = connections_limit
        self.root_dir = root_dir
        self.server_bind()
        self.server_activate()

    def server_bind(self):

        """
        Binds server on host and port
        """

        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        self.socket.bind((self.server_address, self.server_port))

    def server_activate(self):

        """
        Activates server
        :return:
        """

        self.socket.listen(1_000_000)

    @staticmethod
    def _parse_request(request: str) -> Tuple[str, str]:

        """
        Parses request headers
        :param request: request in string format
        :return: parsed request
        """

        method, address = request.split("\r\n")[0].split(" ")[:-1]
        return method, address

    def _method_is_allowed(self, method: str) -> bool:

        """
        Checks if http method is allowed
        :param method:
        :return:
        """
        return method.lower() in self.allowed_methods

    def _get_path_for_server(self, address: str) -> str:

        """
        Checks if path from address exists
        :param address: addres in request url
        :return: path for server is string format
        """

        path_for_server = f"{self.root_dir}{address}"
        if not address.split("/")[-1]:
            path_for_server = f"{path_for_server}index.html"

        return path_for_server

    def _get_content_type(self, address: str) -> Optional[str]:

        """
        Gets content type using address in request
        :param address: path to file in request
        :return: content type based on file extension
        """

        _, file_extension = os.path.splitext(address)
        return self.response_content_types.get(file_extension)

    def generate_response(self, request: str) -> str:

        """
        Generates response based on request
        :param request: method in text representation
        :return:
        """

        method, address = self._parse_request(request)

        if not self._method_is_allowed(method):
            return f"HTTP/1.0 {METHOD_NOT_ALLOWED} " \
                   f"{self.response_status_codes[METHOD_NOT_ALLOWED]}\r\n"

        path_for_server = self._get_path_for_server(address)
        logging.debug("Path for server is %s", path_for_server)
        if not os.path.exists(path_for_server):
            return f"HTTP/1.0 {NOT_FOUND} " \
                   f"{self.response_status_codes[NOT_FOUND]}\r\n"

        date_for_response_header = time.strftime("%a, %d %b %Y %H:%M:%S GMT", time.gmtime())

        content_type = self._get_content_type(address)
        if content_type is None:
            return f"HTTP/1.0 {FORBIDDEN} " \
                   f"{self.response_status_codes[FORBIDDEN]}\r\n"

        with open(path_for_server, "rb") as requested_file:
            response_body = requested_file.read()
        content_length = len(response_body)
        response = f"HTTP/1.0 {OK} " \
                   f"{self.response_status_codes[OK]}\r\n" \
                   f"Date: {date_for_response_header}\r\n" \
                   f"Server: {self.SERVER_NAME}\r\n" \
                   f"Content-Type: {content_type}\r\n" \
                   f"Content-Length: {content_length}\r\n\r\n" \
                   f"{response_body}"

        return response

    def handle_client_connection(self, client_socket: socket.socket):

        """
        Handles client socket connection
        :param client_socket: socket got from client
        :return:
        """

        request = client_socket.recv(1024)
        logging.info('Received %s', request)
        response = self.generate_response(request)
        client_socket.send(response)
        client_socket.close()

    def serve_forever(self):

        """
        Starts server to serve
        :return:
        """

        response = b'HTTP/1.0 200 OK\r\nDate: Mon, 1 Jan 1996 01:01:01 GMT\r\n'
        response += b'Content-Type: text/plain\r\nContent-Length: 13\r\n\r\n'
        response += b'Hello, world!'

        epoll = select.epoll()
        epoll.register(self.socket.fileno(), select.EPOLLIN)
        try:
            connections, requests, responses = dict(), dict(), dict()
            while True:
                events = epoll.poll(10000)
                for fileno, event in events:
                    if fileno == self.socket.fileno():
                        connection, address = self.socket.accept()
                        connection.setblocking(0)
                        epoll.register(connection.fileno(), select.EPOLLIN)
                        connections[connection.fileno()] = connection
                        requests[connection.fileno()] = b''
                        responses[connection.fileno()] = b''
                    elif event & select.EPOLLIN:
                        logging.info("Reading event for %s, process is %s", fileno, os.getpid())
                        requests[fileno] += connections[fileno].recv(1024)
                        if self.EOL1 in requests[fileno] or self.EOL2 in requests[fileno]:
                            epoll.modify(fileno, select.EPOLLOUT)
                            connections[fileno].setsockopt(socket.IPPROTO_TCP, socket.TCP_CORK, 1)
                            logging.info(
                                "%s",
                                self._parse_request(requests[fileno].decode()[:-2])
                            )
                    elif event & select.EPOLLOUT:
                        logging.info(
                            "Writing event for %s. Writing answer: %s, process is %s",
                            fileno,
                            responses[fileno],
                            os.getpid()
                        )
                        response = self.generate_response(request=requests[fileno].decode()[:-2])
                        logging.info("Response is %s", response)
                        responses[fileno] = response.encode(encoding="utf-8")
                        bytes_written = connections[fileno].send(responses[fileno])
                        responses[fileno] = responses[fileno][bytes_written:]
                        if not responses[fileno]:
                            epoll.modify(fileno, 0)
                            connections[fileno].shutdown(socket.SHUT_RDWR)
                    elif event & select.EPOLLHUP:
                        epoll.unregister(fileno)
                        connections[fileno].close()
                        del connections[fileno]
        finally:
            epoll.unregister(self.socket.fileno())
            epoll.close()
            self.socket.close()


def run_server(host: str,
               port: int,
               connections_limit: int,
               root_dir: str,
               num_workers: int) -> NoReturn:

    """
    Starts server to tun
    :param host: server host
    :param port: server port
    :param connections_limit: connections limit for server
    :param root_dir: root dir to get files from
    :param num_workers: number of workers for serving
    """

    server = AsyncHTTPServer(
        server_address=host,
        server_port=port,
        connections_limit=connections_limit,
        root_dir=root_dir
    )

    worker_processes = list()

    try:
        for worker_num in range(num_workers):
            worker_process = mp.Process(target=server.serve_forever)
            worker_process.start()
            worker_processes.append(worker_process)

        for worker_process in worker_processes:
            worker_process.join()
    except KeyboardInterrupt:
        for worker_process in worker_processes:
            logging.debug("Terminating process: %s", worker_process.pid)
            worker_process.terminate()


if __name__ == "__main__":

    argument_parser = argparse.ArgumentParser(add_help=False)
    argument_parser.add_argument("-h", "--host", type=str, default="localhost")
    argument_parser.add_argument("-p", "--port", type=int, default=8080)
    argument_parser.add_argument("-w", "--workers", type=int, default=4)
    argument_parser.add_argument("-r", "--root", type=str, default="./http-test-suite/httptest/dir2")

    args = argument_parser.parse_args()
    logging.debug("Root dir is %s", os.path.abspath(args.root))

    run_server(
        host=args.host,
        port=args.port,
        root_dir=args.root,
        connections_limit=CONNECTIONS_LIMIT,
        num_workers=args.workers
    )

