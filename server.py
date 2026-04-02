# Remote display server: capture local screen and stream frames to clients.

from __future__ import annotations

import argparse
import io
import socket
import threading
import time
from dataclasses import dataclass

import mss
from PIL import Image

from protocol import send_frame

DEFAULT_FPS = 60
DEFAULT_JPEG_QUALITY = 240

@dataclass
class ServerConfig:
    host: str
    port: int

# Parse CLI options for server endpoint only.
# Returns a ServerConfig used by the runtime loop.
# Stream quality/performance settings are fixed in code for simpler usage.
def parse_args() -> ServerConfig:
    parser = argparse.ArgumentParser(description="CMPT 371 Remote Display TCP Server")
    parser.add_argument("--host", default="0.0.0.0", help="Bind host (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=5001, help="Bind port (default: 5001)")
    args = parser.parse_args()
    return ServerConfig(host=args.host, port=args.port)

# Capture one monitor frame and compress it to JPEG bytes.
# Uses mss for fast screen grabbing and Pillow for encoding.
# Output bytes are sent directly over the TCP framing protocol.
def capture_frame_bytes(sct: mss.mss, monitor: dict, jpeg_quality: int) -> bytes:
    raw = sct.grab(monitor)
    image = Image.frombytes("RGB", raw.size, raw.rgb)

    buffer = io.BytesIO()
    image.save(buffer, format="JPEG", quality=jpeg_quality, optimize=True)
    return buffer.getvalue()

# Handle one connected client in a dedicated thread.
# Captures frames, sends them with length-prefix framing, and throttles by FPS.
# Exits naturally when socket operations fail/disconnect.
def client_stream_loop(conn, addr, config, log=print):
    log(f"[+] Client connected: {addr[0]}:{addr[1]}")

    interval = 1.0 / DEFAULT_FPS
    with conn:
        with mss.mss() as sct:
            monitor = sct.monitors[1]
            while True:
                try:
                    started = time.perf_counter()
                    frame = capture_frame_bytes(sct, monitor, DEFAULT_JPEG_QUALITY)
                    send_frame(conn, frame)

                    elapsed = time.perf_counter() - started
                    sleep_for = interval - elapsed
                    if sleep_for > 0:
                        time.sleep(sleep_for)
                except (BrokenPipeError, OSError):
                    log(f"[-] Client disconnected: {addr[0]}:{addr[1]}")
                    break

# Create the listening TCP socket and accept clients forever.
# For each accepted connection, start a daemon thread running client_stream_loop.
# This allows multiple viewers to consume the stream concurrently.
def run_server(config: ServerConfig, stop_event: threading.Event, log=print) -> None:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listener:
        listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        listener.bind((config.host, config.port))
        listener.listen()
        listener.settimeout(1.0)

        log("=" * 60)
        log("CMPT 371 - Remote Display TCP Server")
        log(f"Listening on {config.host}:{config.port}")
        log("=" * 60)

        while not stop_event.is_set():
            try:
                conn, addr = listener.accept()
                thread = threading.Thread(
                    target=client_stream_loop,
                    args=(conn, addr, config, log),
                    daemon=True,
                )
                thread.start()
            except socket.timeout:
                continue

        log("[!] Server shutting down...")
        log("[✓] Server stopped.")

# Server entrypoint for startup and top-level exception handling.
# Maps keyboard interrupt and connection-level failures to readable logs.
# Keeps CLI behavior predictable for demo and grading.
def main() -> None:
    config = parse_args()
    try:
        run_server(config)
    except KeyboardInterrupt:
        print("\n[!] Server stopped by user.")
    except (BrokenPipeError, ConnectionError, OSError) as exc:
        print(f"\n[!] Connection error: {exc}")

if __name__ == "__main__":
    main()
