from __future__ import annotations
import io
import socket
import threading
import time
from dataclasses import dataclass
import mss
from PIL import Image
from protocol import send_frame

DEFAULT_FPS = 60
DEFAULT_JPEG_QUALITY = 90

@dataclass
class ServerConfig:
    host: str
    port: int

# Capture one monitor frame and compress it to JPEG bytes
# Uses mss for fast screen grabbing and Pillow for encoding
# Output bytes are sent directly over the TCP framing protocol
def capture_frame_bytes(sct: mss.mss, monitor: dict, jpeg_quality: int) -> bytes:
    raw = sct.grab(monitor)
    image = Image.frombytes("RGB", raw.size, raw.rgb)

    buffer = io.BytesIO()
    image.save(buffer, format="JPEG", quality=jpeg_quality, optimize=True)
    return buffer.getvalue()

# Handle one connected client in a dedicated thread
# Captures frames, sends them, and throttles by FPS
# Exits naturally when socket operations fail/disconnect
def client_stream_loop(connection, addr, stop_event, log=print):
    log(f"[+] Client connected: {addr[0]}:{addr[1]}")

    interval = 1.0 / DEFAULT_FPS
    with connection:
        with mss.mss() as sct:
            monitor = sct.monitors[1]

            while not stop_event.is_set():
                try:
                    started = time.perf_counter()
                    frame = capture_frame_bytes(sct, monitor, DEFAULT_JPEG_QUALITY)
                    send_frame(connection, frame)

                    elapsed = time.perf_counter() - started
                    sleep_for = interval - elapsed
                    if sleep_for > 0:
                        time.sleep(sleep_for)

                except (BrokenPipeError, OSError):
                    log(f"[-] Client disconnected: {addr[0]}:{addr[1]}")
                    break

    log(f"[!] Closing connection: {addr[0]}:{addr[1]}")

# Create the listening TCP socket
# For each accepted connection, start a thread running client_stream_loop
# This allows multiple viewers to consume the stream concurrently
def run_server(config: ServerConfig, stop_event: threading.Event, log=print) -> None:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listener:
        listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        listener.bind((config.host, config.port))
        listener.listen()
        listener.settimeout(1.0)

        log("=" * 60)
        log("Server started - screen is being shared")
        log(f"Listening on {config.host}:{config.port}")
        log("=" * 60)

        # while the server is running, create and start a thread for each incoming client
        while not stop_event.is_set():
            try:
                connection, addr = listener.accept()
                thread = threading.Thread(
                    target=client_stream_loop,
                    args=(connection, addr, stop_event, log),
                    daemon=True,
                )
                thread.start()
            except socket.timeout:
                continue

        log("[!] Server shutting down...")
        log("[✓] Server stopped.")
