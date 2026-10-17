"""Сетевая оболочка; вычисления находятся в protocol.py."""

import argparse
import logging
import socket
import socketserver
import threading
from collections.abc import Callable

from .decorators import log_call, timed
from .protocol import client_commands, decode_response, process_request


def handler_factory(process: Callable) -> type[socketserver.StreamRequestHandler]:
    """Привязать обработку запросов к конкретному серверу без глобального состояния."""

    class Handler(socketserver.StreamRequestHandler):
        """Одна UTF-8 строка запроса и ответа на соединение."""

        def handle(self) -> None:
            """Прочитать ограниченную строку и отправить ответ."""
            self.request.settimeout(5)
            raw = self.rfile.readline(40002)
            try:
                line = raw.decode("utf-8").rstrip("\r\n")
                response = process(line)
            except UnicodeError:
                response = '{"ok":false,"error":"invalid UTF-8"}'
            self.wfile.write((response + "\n").encode("utf-8"))

    return Handler


def send(host: str, port: int, line: str) -> str:
    """Отправить запрос через настоящий TCP-сокет и прочитать полный ответ."""
    with socket.create_connection((host, port), timeout=5) as sock:
        sock.sendall((line + "\n").encode("utf-8"))
        with sock.makefile("rb") as stream:
            return stream.readline(100000).decode("utf-8").rstrip("\n")


def roundtrip_demo() -> dict:
    """Проверить сервер и клиент на свободном локальном TCP-порту."""
    observed = timed(log_call("INFO")(process_request))
    with socketserver.TCPServer(("127.0.0.1", 0), handler_factory(observed)) as server:
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            port = server.server_address[1]
            pairs = tuple(
                (line, send("127.0.0.1", port, line)) for line in client_commands()
            )
        finally:
            server.shutdown()
            thread.join(timeout=5)
    return {
        "transport": "TCP 127.0.0.1",
        "port": port,
        "pairs": pairs,
        "decoded": tuple(repr(decode_response(answer)) for _, answer in pairs),
        "handler_calls": len(observed.history),
        "seconds": observed.history,
    }


def main() -> None:
    """Запустить самостоятельный сервер или клиент."""
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("server", "client", "demo"))
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--request", default="CALC 2 + 3")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    if args.mode == "demo":
        print(roundtrip_demo())
    elif args.mode == "client":
        print(decode_response(send("127.0.0.1", args.port, args.request)))
    else:
        observed = timed(log_call()(process_request))
        with socketserver.TCPServer(
            ("127.0.0.1", args.port), handler_factory(observed)
        ) as server:
            print(f"Сервер слушает 127.0.0.1:{args.port}", flush=True)
            server.serve_forever()


if __name__ == "__main__":
    main()
