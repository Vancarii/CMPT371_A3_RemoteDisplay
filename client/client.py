from __future__ import annotations

import socket
import threading
from dataclasses import dataclass
from queue import Queue
from typing import Literal

from protocol import recv_frame

QueueMessage = tuple[Literal["frame", "status"], bytes | str]

@dataclass
class ClientConfig:
    server_host: str
    server_port: int

# Background network loop for framed JPEG payloads with auto-reconnect
# Pushes status and frame messages to a queue consumed by the Tkinter thread
# Keeps trying to reconnect after disconnect until the app is closed
def receiver_loop(config: ClientConfig, frame_queue: Queue[QueueMessage], stop_event: threading.Event) -> None:
    connected = False

    while not stop_event.is_set():
        sock: socket.socket | None = None
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2.0)
            sock.connect((config.server_host, config.server_port))
            sock.settimeout(None)

            if not connected:
                print(f"Connected to server at {config.server_host}:{config.server_port}")
                frame_queue.put(("status", "Receiving stream..."))
                connected = True

            while not stop_event.is_set():
                frame_bytes = recv_frame(sock)
                frame_queue.put(("frame", frame_bytes))

        except (ConnectionError, OSError):
            if connected:
                frame_queue.put(("status", "Server has stopped sharing."))
                connected = False
            if stop_event.wait(1.0):
                break
        finally:
            if sock is not None:
                try:
                    sock.close()
                except OSError:
                    pass
