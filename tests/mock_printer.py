"""A fake ESC/POS printer used by the tests and for demos without hardware.

Speaks just enough of the protocol to exercise BonBridge end to end:

* answers ``DLE EOT n`` with plausible real-time status bytes
* answers ``GS I n`` with a model / type / ROM identifier
* records everything else as "printed" data

Run standalone::

    python3 tests/mock_printer.py --port 9200
"""

from __future__ import annotations

import argparse
import socket
import socketserver
import threading
from typing import List, Optional


class MockPrinterState:
    def __init__(self) -> None:
        self.received = bytearray()
        self.jobs: List[bytes] = []
        self.cover_open = False
        self.paper_end = False
        self.paper_near_end = False
        self.error = False
        # Pin 3 of the drawer connector: HIGH means "drawer open or no drawer
        # connected", LOW means "a drawer is connected and closed".
        self.drawer_pin_high = True
        self.lock = threading.Lock()

    # -- status bytes ------------------------------------------------------

    def printer_status(self) -> int:
        # bit1 fixed 1, bit4 fixed 1, bit2 = drawer connector pin 3
        return 0x12 | (0x04 if self.drawer_pin_high else 0x00)

    def offline_status(self) -> int:
        value = 0x12
        if self.cover_open:
            value |= 0x04
        if self.paper_end:
            value |= 0x20
        if self.error:
            value |= 0x40
        return value

    def error_status(self) -> int:
        return 0x12 | (0x20 if self.error else 0x00)

    def paper_status(self) -> int:
        value = 0x12
        if self.paper_near_end:
            value |= 0x0C
        if self.paper_end:
            value |= 0x60
        return value


class _Handler(socketserver.BaseRequestHandler):
    def handle(self) -> None:
        state: MockPrinterState = self.server.state  # type: ignore[attr-defined]
        sock: socket.socket = self.request
        sock.settimeout(30.0)
        self.server.clients.append(sock)  # type: ignore[attr-defined]
        buffer = bytearray()
        while True:
            try:
                chunk = sock.recv(4096)
            except (socket.timeout, OSError):
                break
            if not chunk:
                break
            buffer.extend(chunk)
            replies = bytearray()
            index = 0
            while index < len(buffer):
                # DLE EOT n
                if buffer[index] == 0x10 and index + 2 < len(buffer) and buffer[index + 1] == 0x04:
                    n = buffer[index + 2]
                    mapping = {
                        1: state.printer_status,
                        2: state.offline_status,
                        3: state.error_status,
                        4: state.paper_status,
                    }
                    replies.append(mapping.get(n, state.printer_status)())
                    index += 3
                    continue
                # GS I n
                if buffer[index] == 0x1D and index + 2 < len(buffer) and buffer[index + 1] == 0x49:
                    n = buffer[index + 2]
                    replies.extend({1: b"\x20", 2: b"\x02", 3: b"1.05"}.get(n, b"\x00"))
                    index += 3
                    continue
                index += 1
            with state.lock:
                state.received.extend(buffer)
                state.jobs.append(bytes(buffer))
            buffer.clear()
            if replies:
                try:
                    sock.sendall(bytes(replies))
                except OSError:
                    break
        try:
            sock.close()
        except OSError:
            pass


class MockPrinter(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True

    def __init__(self, host: str = "127.0.0.1", port: int = 9200):
        self.state = MockPrinterState()
        self.clients: List[socket.socket] = []
        super().__init__((host, port), _Handler)
        self._thread: Optional[threading.Thread] = None

    def start(self) -> "MockPrinter":
        self._thread = threading.Thread(target=self.serve_forever, kwargs={"poll_interval": 0.2}, daemon=True)
        self._thread.start()
        return self

    def stop(self) -> None:
        """Stop accepting *and* drop existing connections (simulates power off)."""
        for client in list(self.clients):
            try:
                client.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            try:
                client.close()
            except OSError:
                pass
        self.clients.clear()
        self.shutdown()
        self.server_close()

    @property
    def data(self) -> bytes:
        with self.state.lock:
            return bytes(self.state.received)


def main() -> int:
    parser = argparse.ArgumentParser(description="Mock ESC/POS printer")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=9200)
    args = parser.parse_args()
    server = MockPrinter(args.host, args.port)
    print(f"Mock printer listening on {args.host}:{args.port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
