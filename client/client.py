from __future__ import annotations
import socket
import threading
from dataclasses import dataclass
from queue import Queue
from protocol import MSG_FRAME, MSG_STATUS, QueueMessage, recv_frame


@dataclass
class ClientConfig:
    server_host: str
    server_port: int

# Background network loop for framed JPEG payloads with auto-reconnect
# Pushes status and frame messages to a queue consumed by the Tkinter thread
# Keeps trying to reconnect after disconnect until the app is closed
def receiver_loop(config: ClientConfig, frame_queue: Queue[QueueMessage], stop_event: threading.Event) -> None:
    connected = False

    # Keep trying until the UI quits and signals stop_event
    while not stop_event.is_set():
        sock: socket.socket | None = None
        try:
            # Create a fresh TCP connection attempt
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2.0)
            sock.connect((config.server_host, config.server_port))
            sock.settimeout(None)

            if not connected:
                print(f"Connected to server at {config.server_host}:{config.server_port}")
                frame_queue.put((MSG_STATUS, "Receiving stream..."))
                connected = True

            # Read framed JPEG payloads and push them to the queue for the UI thread to render
            while not stop_event.is_set():
                frame_bytes = recv_frame(sock)
                frame_queue.put((MSG_FRAME, frame_bytes))

        except (ConnectionError, OSError):
            # Any socket error means stream is down, report once, then retry
            if connected:
                frame_queue.put((MSG_STATUS, "Server has stopped sharing."))
                connected = False
            if stop_event.wait(1.0):
                break
        finally:
            # Always close the socket from this attempt before looping again
            if sock is not None:
                try:
                    sock.close()
                except OSError:
                    pass
