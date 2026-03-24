# Remote display client: receive frames and render them in a Tkinter window.

from __future__ import annotations

import argparse
import io
import socket
import threading
from dataclasses import dataclass
from queue import Empty, Queue

from PIL import Image

from protocol import recv_frame

@dataclass
class ClientConfig:
    server_host: str
    server_port: int

# Parse required server endpoint options from CLI.
# Returns a ClientConfig consumed by the networking/UI startup path.
# Keeps runtime options explicit and easy to demo.
def parse_args() -> ClientConfig:
    parser = argparse.ArgumentParser(description="CMPT 371 Remote Display TCP Client")
    parser.add_argument("--host", required=True, help="Server IP or hostname")
    parser.add_argument("--port", type=int, default=5001, help="Server port (default: 5001)")
    args = parser.parse_args()
    return ClientConfig(server_host=args.host, server_port=args.port)

# Background socket receive loop for framed JPEG payloads.
# Pushes decoded byte payloads into a bounded queue for the Tkinter thread.
# Sends an empty sentinel frame when the connection drops.
def receiver_loop(sock: socket.socket, frame_queue: Queue[bytes]) -> None:
    try:
        while True:
            frame_bytes = recv_frame(sock)
            frame_queue.put(frame_bytes)
    except (ConnectionError, OSError):
        frame_queue.put(b"")

# Create socket connection and start the Tkinter viewer window.
# Runs receiver_loop in a daemon thread to keep UI responsive.
# Handles environments without Tk support with a clear runtime error.
def run_client(config: ClientConfig) -> None:
    try:
        import tkinter as tk
        from PIL import ImageTk
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "Tkinter is not available in this Python build. "
            "Use a Python installation that includes Tk support to run the GUI client."
        ) from exc

    frame_queue: Queue[bytes] = Queue(maxsize=2)

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((config.server_host, config.server_port))
    print(f"Connected to server at {config.server_host}:{config.server_port}")

    receiver = threading.Thread(target=receiver_loop, args=(sock, frame_queue), daemon=True)
    receiver.start()

    root = tk.Tk()
    root.title("CMPT 371 Remote Display Viewer")

    status_label = tk.Label(root, text="Receiving stream...")
    status_label.pack(anchor="w", padx=8, pady=(8, 0))

    image_label = tk.Label(root)
    image_label.pack(padx=8, pady=8)

    # UI refresh callback that drains pending frames from the queue.
    # Converts JPEG bytes to PhotoImage and updates the label widget.
    # Stops scheduling updates after disconnect sentinel is observed.
    def update_frame() -> None:
        try:
            while True:
                frame_bytes = frame_queue.get_nowait()
                if frame_bytes == b"":
                    status_label.config(text="Disconnected from server")
                    return

                image = Image.open(io.BytesIO(frame_bytes))
                tk_image = ImageTk.PhotoImage(image=image)
                image_label.configure(image=tk_image)
                image_label.image = tk_image

        except Empty:
            pass

        root.after(15, update_frame)

    # Window close callback for graceful resource cleanup.
    # Ensures socket is closed before shutting down Tk main loop.
    # Avoids dangling connections when user exits the viewer.
    def on_close() -> None:
        try:
            sock.close()
        finally:
            root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_close)
    root.after(15, update_frame)
    root.mainloop()

# Client entrypoint with top-level error reporting.
# Separates network errors from environment issues (e.g., missing Tk).
def main() -> None:
    config = parse_args()
    try:
        run_client(config)
    except KeyboardInterrupt:
        print("\nClient stopped by user.")
    except OSError as exc:
        print(f"Connection failed: {exc}")
    except RuntimeError as exc:
        print(exc)

if __name__ == "__main__":
    main()
