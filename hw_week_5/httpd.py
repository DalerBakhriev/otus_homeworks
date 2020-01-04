"""
Entry point to my own server program
"""

import argparse
import multiprocessing as mp
import os
import select
import socket
import time
import urllib.parse as url_parse
from typing import Dict, NoReturn, Optional, Tuple


SERVER_ADDRESS = "localhost"
SERVER_PORT = 8080
CONNECTIONS_LIMIT = 100000
FORBIDDEN = 403
NOT_FOUND = 404
METHOD_NOT_ALLOWED = 405
OK = 200

class AsyncHTTPServer:

    """
    Asynchronous realization of http server
    on sockets
    """

    response_status_codes = {
        OK: "OK",
        FORBIDDEN: "Forbidden",
        NOT_FOUND: "Not Found",
        METHOD_NOT_ALLOWED: "Method Not Allowed"
    }
    EOL1 = b"\n\n"
    EOL2 = b"\n\r\n"

    response_content_types = {
        ".txt": "text/plain",
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
    HEADERS_TERMINATOR = "\r\n\r\n"
    HEADERS_SEPARATOR = "\r\n"
    SERVER_NAME = "Daler.Bakhriev"
    PROTOCOL = "HTTP/1.0"
    

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
        self.server_start()

    def server_start(self):

        """
        Binds server on host and port
        """

        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        self.socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        self.socket.bind((self.server_address, self.server_port))
        self.socket.listen(100)

    @staticmethod
    def _parse_request(request: str) -> Tuple[str, str]:

        """
        Parses request headers
        :param request: request in string format
        :return: parsed request
        """

        method, raw_path = request.split("\r\n")[0].split(" ")[:-1]
        path = url_parse.unquote(url_parse.urlparse(raw_path).path)

        return method, path

    def _method_is_allowed(self, method: str) -> bool:

        """
        Checks if http method is allowed
        :param method: request method name
        :return: True if method is allowed by server and False otherwise
        """

        return method.lower() in self.allowed_methods

    def _get_path_for_server(self, parsed_path: str) -> str:

        """
        Checks if path from address exists
        :param address: addres in request url
        :return: path for server is string format
        """

        path_for_server = f"{self.root_dir}{parsed_path}"
        if not parsed_path.split("/")[-1]:
            path_for_server = f"{path_for_server}index.html"

        return path_for_server

    def _get_content_type(self, path: str) -> Optional[str]:

        """
        Gets content type using address in request
        :param path: path to file in request
        :return: content type based on file extension
        """

        _, file_extension = os.path.splitext(path)

        return self.response_content_types.get(file_extension)

    def _get_response_body(self, path: str) -> bytes:

        """
        Gets response body from file path
        :param path: path to file in request
        :return: file content in bytes format
        """

        with open(path, "rb") as requested_file:
            response_body = requested_file.read()
        
        return response_body
    
    def _generate_response(self,
                           response_headers: Dict[str, str],
                           status_code: int,
                           response_body: bytes = b"") -> bytes:

        """
        Generates response as bytes format
        :param response_headers: headers for response in dict format
        :param status_code: status code of response to generate
        :param response_body: body of response in bytes format
        """
        
        response_code_line = f"{self.PROTOCOL} {status_code} " \
                             f"{self.response_status_codes[status_code]}{self.HEADERS_SEPARATOR}"
        headers_line = f"{self.HEADERS_SEPARATOR}".join(
            f"{name}: {value}" for name, value in response_headers.items()
        )
        response = f"{response_code_line}{headers_line}{self.HEADERS_TERMINATOR}".encode("utf-8") + response_body

        return response
    
    def handle_request(self, request: str) -> bytes:

        """
        Generates response based on request
        :param request: method in text representation
        :return: response in string format
        """

        method, address = self._parse_request(request)
        date_for_response_header = time.strftime("%a, %d %b %Y %H:%M:%S GMT", time.gmtime())

        response_headers = {
            "Date": date_for_response_header,
            "Server": self.SERVER_NAME,
            "Connection": "closed"
        }

        if not self._method_is_allowed(method):
            return self._generate_response(
                response_headers=response_headers,
                status_code=METHOD_NOT_ALLOWED
            )

        path_for_server = self._get_path_for_server(address)
        if not os.path.exists(path_for_server):
            return self._generate_response(
                response_headers=response_headers,
                status_code=NOT_FOUND
            )

        content_type = self._get_content_type(path_for_server)
        if content_type is None:
            return self._generate_response(
                response_headers=response_headers,
                status_code=FORBIDDEN
            )
        
        response_body = self._get_response_body(path_for_server) if method.lower() == "get" else b""
        content_length = os.path.getsize(path_for_server)
        response_headers["Content-Type"] = content_type
        response_headers["Content-Length"] = content_length
        
        return self._generate_response(
            response_headers=response_headers,
            status_code=OK,
            response_body=response_body
        )

    def serve_forever(self):

        """
        Starts server
        """

        epoll = select.epoll()
        epoll.register(self.socket.fileno(), select.EPOLLIN)
        try:
            connections, requests, responses = dict(), dict(), dict()
            while True:
                events = epoll.poll(1)
                for fileno, event in events:
                    if fileno == self.socket.fileno():
                        connection, _ = self.socket.accept()
                        connection.setblocking(0)
                        epoll.register(connection.fileno(), select.EPOLLIN)
                        connections[connection.fileno()] = connection
                        requests[connection.fileno()] = b""
                        responses[connection.fileno()] = b""
                    elif event & select.EPOLLIN:
                        incoming_request_data = connections[fileno].recv(1024)
                        if not incoming_request_data:
                            epoll.modify(fileno, select.EPOLLET)
                            connections[fileno].shutdown(socket.SHUT_RDWR)
                            continue
                        requests[fileno] += incoming_request_data
                        if self.EOL1 in requests[fileno] or self.EOL2 in requests[fileno]:
                            epoll.modify(fileno, select.EPOLLOUT)
                    elif event & select.EPOLLOUT:
                        response = self.handle_request(request=requests[fileno].decode()[:-2])
                        responses[fileno] = response
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
        for _ in range(num_workers):
            worker_process = mp.Process(target=server.serve_forever)
            worker_process.start()
            worker_processes.append(worker_process)

        for worker_process in worker_processes:
            worker_process.join()
    except KeyboardInterrupt:
        for worker_process in worker_processes:
            worker_process.terminate()



if __name__ == "__main__":

    argument_parser = argparse.ArgumentParser(add_help=False)
    argument_parser.add_argument("-h", "--host", type=str, default="localhost")
    argument_parser.add_argument("-p", "--port", type=int, default=8080)
    argument_parser.add_argument("-w", "--workers", type=int, default=4)
    argument_parser.add_argument("-r", "--root", type=str, default=".")

    args = argument_parser.parse_args()

    run_server(
        host=args.host,
        port=args.port,
        root_dir=args.root,
        connections_limit=CONNECTIONS_LIMIT,
        num_workers=args.workers
    )

