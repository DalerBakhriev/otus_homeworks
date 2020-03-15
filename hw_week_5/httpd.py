"""
Entry point to my own server program
"""

import argparse
import logging
import multiprocessing as mp
import os
import select
import socket
import time
import urllib.parse as url_parse
from typing import (
    Dict,
    Iterable,
    NamedTuple,
    Optional,
    Tuple,
    Union
)

SERVER_ADDRESS = "localhost"
SERVER_PORT = 8080
FORBIDDEN = 403
NOT_FOUND = 404
METHOD_NOT_ALLOWED = 405
OK = 200

CONTENT_TYPES = {
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
RESPONSE_STATUS_CODES = {
    OK: "OK",
    FORBIDDEN: "Forbidden",
    NOT_FOUND: "Not Found",
    METHOD_NOT_ALLOWED: "Method Not Allowed"
}
ALLOWED_METHODS = ("get", "head")
SERVER_NAME = "Daler.Bakhriev"
SERVER_PROTOCOL = "HTTP/1.0"
HEADERS_TERMINATOR = "\r\n\r\n"
HEADERS_SEPARATOR = "\r\n"


class HTTPServerConfig(NamedTuple):

    address: str
    port: Union[int, str]
    connections_limit: int
    root_dir: str
    response_status_codes: Dict[int, str]
    EOL1: bytes
    EOL2: bytes
    response_content_types: Dict[str, str]
    address_family: int
    socket_type: int
    allowed_methods: Iterable[str]
    headers_terminator: str
    headers_separator: str
    server_name: str
    protocol: str


def parse_request(request: str) -> Tuple[str, str]:

    """
    Parses request headers
    :param request: request in string format
    :return: parsed request
    """

    method, raw_path = request.split("\r\n")[0].split(" ")[:-1]
    path = url_parse.unquote(url_parse.urlparse(raw_path).path)

    return method, path


def get_path_for_server(root_dir: str, parsed_path: str) -> str:

    """
    Checks if path from address exists
    :param root_dir: root directory for http server
    :param parsed_path: parsed path from request
    :return: path for server is string format
    """

    path_for_server = f"{root_dir}{parsed_path}"
    if not parsed_path.split("/")[-1]:
        path_for_server = f"{path_for_server}index.html"
    logging.debug("Path for server is %s", path_for_server)

    return path_for_server


def get_response_body(path: str) -> bytes:

    """
    Gets response body from file path
    :param path: path to file in request
    :return: file content in bytes format
    """

    with open(path, "rb") as requested_file:
        response_body = requested_file.read()

    return response_body


def get_content_type(path: str, server_config: HTTPServerConfig) -> Optional[str]:

    """
    Gets content type using address in request
    :param path: path to file in request
    :param server_config: config for http server
    :return: content type based on file extension
    """

    _, file_extension = os.path.splitext(path)

    return server_config.response_content_types.get(file_extension)


def generate_response(response_headers: Dict[str, str],
                      status_code: int,
                      server_config: HTTPServerConfig,
                      response_body: bytes = b"") -> bytes:
    """
    Generates response as bytes format
    :param response_headers: headers for response in dict format
    :param status_code: status code of response to generate
    :param server_config: http server config
    :param response_body: body of response in bytes format
    """

    response_code_line = f"{server_config.protocol} {status_code} " \
                         f"{server_config.response_status_codes[status_code]}{server_config.headers_separator}"
    headers_line = f"{server_config.headers_separator}".join(
        f"{name}: {value}" for name, value in response_headers.items()
    )
    response = f"{response_code_line}{headers_line}{server_config.headers_terminator}".encode("utf-8") + response_body

    return response


def method_is_allowed(server_config: HTTPServerConfig, method: str) -> bool:

    """
    Checks if http method is allowed
    :param server_config: config for http server
    :param method: request method name
    :return: True if method is allowed by server and False otherwise
    """

    return method.lower() in server_config.allowed_methods


def handle_request(server_config: HTTPServerConfig, request: str) -> bytes:

    """
    Generates response based on request
    :param request: method in text representation
    :param server_config: config for http server
    :return: response in string format
    """

    method, address = parse_request(request)
    date_for_response_header = time.strftime("%a, %d %b %Y %H:%M:%S GMT", time.gmtime())

    response_headers = {
        "Date": date_for_response_header,
        "Server": server_config.server_name,
        "Connection": "closed"
    }

    if not method_is_allowed(server_config=server_config, method=method):
        return generate_response(
            server_config=server_config,
            response_headers=response_headers,
            status_code=METHOD_NOT_ALLOWED
        )

    path_for_server = get_path_for_server(
        root_dir=server_config.root_dir,
        parsed_path=address
    )
    if not os.path.exists(path_for_server):
        return generate_response(
            server_config=server_config,
            response_headers=response_headers,
            status_code=NOT_FOUND
        )

    content_type = get_content_type(server_config=server_config, path=path_for_server)
    if content_type is None:
        return generate_response(
            server_config=server_config,
            response_headers=response_headers,
            status_code=FORBIDDEN
        )

    response_body = get_response_body(path_for_server) if method.lower() == "get" else b""
    content_length = os.path.getsize(path_for_server)
    response_headers["Content-Type"] = content_type
    response_headers["Content-Length"] = content_length

    return generate_response(
        server_config=server_config,
        response_headers=response_headers,
        status_code=OK,
        response_body=response_body
    )


class AsyncHTTPServer:

    """
    Asynchronous realization of http server
    on sockets
    """

    def __init__(self, http_server_config: HTTPServerConfig):

        self.server_config = http_server_config
        self.socket = socket.socket(self.server_config.address_family, self.server_config.socket_type)
        self.server_address = self.server_config.address
        self.server_port = self.server_config.port
        self.connections_limit = self.server_config.connections_limit
        self.root_dir = self.server_config.root_dir
        self.server_start()

    def server_start(self):

        """
        Binds server on host and port
        """

        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        self.socket.bind((self.server_address, self.server_port))
        self.socket.listen(self.connections_limit)

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
                        logging.debug(
                            "Request is:\n %s\n Connection is %s\n Process is %s",
                            incoming_request_data,
                            fileno,
                            os.getpid()
                        )
                        if not incoming_request_data:
                            epoll.modify(fileno, select.EPOLLHUP)
                            continue
                        requests[fileno] += incoming_request_data
                        if self.server_config.EOL1 in requests[fileno] or self.server_config.EOL2 in requests[fileno]:
                            epoll.modify(fileno, select.EPOLLOUT)
                    elif event & select.EPOLLOUT:
                        response = handle_request(
                            server_config=self.server_config,
                            request=requests[fileno].decode()[:-2]
                        )
                        logging.debug(
                            "Response is:\n %s\n Connection is %s\n Process is %s",
                            response,
                            fileno,
                            os.getpid()
                        )
                        responses[fileno] = response
                        bytes_written = connections[fileno].send(responses[fileno])
                        responses[fileno] = responses[fileno][bytes_written:]
                        if not responses[fileno]:
                            epoll.modify(fileno, 0)
                            try:
                                connections[fileno].shutdown(socket.SHUT_RDWR)
                            except OSError:
                                pass
                    elif event & select.EPOLLHUP:
                        epoll.unregister(fileno)
                        connections[fileno].close()
                        del connections[fileno]
        finally:
            epoll.unregister(self.socket.fileno())
            epoll.close()
            self.socket.close()


def run_server(server_config: HTTPServerConfig) -> None:

    """
    Starts server to tun
    :param server_config: config for http server
    """

    server = AsyncHTTPServer(http_server_config=server_config)
    server.serve_forever()


if __name__ == "__main__":

    argument_parser = argparse.ArgumentParser(add_help=False)
    argument_parser.add_argument("-h", "--host", type=str, default="localhost")
    argument_parser.add_argument("-p", "--port", type=int, default=8080)
    argument_parser.add_argument("-w", "--workers", type=int, default=4)
    argument_parser.add_argument("-r", "--root", type=str, default="./httptest/dir2/")
    argument_parser.add_argument("-l", "--connections-limit", type=int, default=1000)
    argument_parser.add_argument("-d", "--debug", action="store_true")

    args = argument_parser.parse_args()
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    logging.debug("File root is %s", os.path.abspath(args.root))
    server_configuration = HTTPServerConfig(
        address=args.host,
        port=args.port,
        connections_limit=args.connections_limit,
        root_dir=args.root,
        response_status_codes=RESPONSE_STATUS_CODES,
        EOL1=b"\n\n",
        EOL2=b"\n\r\n",
        response_content_types=CONTENT_TYPES,
        address_family=socket.AF_INET,
        socket_type=socket.SOCK_STREAM,
        allowed_methods=ALLOWED_METHODS,
        headers_terminator=HEADERS_TERMINATOR,
        headers_separator=HEADERS_SEPARATOR,
        server_name=SERVER_NAME,
        protocol=SERVER_PROTOCOL
    )

    worker_processes = list()

    try:
        for _ in range(args.workers):
            worker_process = mp.Process(
                target=run_server,
                args=(server_configuration,)
            )
            worker_process.start()
            worker_processes.append(worker_process)

        for worker_process in worker_processes:
            worker_process.join()
    except KeyboardInterrupt:
        for worker_process in worker_processes:
            worker_process.terminate()
