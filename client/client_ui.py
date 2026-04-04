from __future__ import annotations

import io
import threading
from queue import Empty, Queue
from typing import Callable, Literal

from PIL import Image

QueueMessage = tuple[Literal["frame", "status"], bytes | str]


# Build and run the viewer window, then process incoming frames and status updates
def run_viewer(config: object, receiver_loop: Callable) -> None:
    try:
        import tkinter as tk
        from PIL import ImageTk
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "Tkinter is not available in this Python build. "
            "Use a Python installation that includes Tk support to run the GUI client."
        ) from exc

    frame_queue: Queue[QueueMessage] = Queue(maxsize=2)
    stop_event = threading.Event()

    receiver = threading.Thread(target=receiver_loop, args=(config, frame_queue, stop_event), daemon=True)
    receiver.start()

    root = tk.Tk()
    root.title("CMPT 371 Remote Display Viewer")
    root.geometry("1024x768")
    root.configure(bg="#f0f0f0")

    title_label, content_frame, image_label, status_label = _setup_ui(root)
    tk_image_holder = {"image": None}

    # Update labels when connection/stream status changes
    def _handle_status_message(status_text: str) -> None:
        status_label.config(text=status_text)
        if status_text.startswith("Server has stopped sharing"):
            image_label.configure(
                image="",
                text="Server has stopped sharing\nWaiting for server to resume...",
                fg="#999",
            )
            image_label.image = None
        elif "Receiving" in status_text:
            image_label.configure(text="Loading frames...", fg="#666")

    # Decode one frame, scale it to fit the panel, and render it
    def _render_frame(frame_bytes: bytes) -> None:
        image = Image.open(io.BytesIO(frame_bytes))
        root.update_idletasks()
        max_width = content_frame.winfo_width() - 16
        max_height = content_frame.winfo_height() - 16

        if max_width > 1 and max_height > 1:
            image.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)

        tk_image = ImageTk.PhotoImage(image=image)
        tk_image_holder["image"] = tk_image
        image_label.configure(image=tk_image, text="", fg="black")

    # Route each queue message to either status handling or frame rendering
    def _process_queue_message(kind: str, payload: bytes | str) -> None:
        if kind == "status":
            _handle_status_message(str(payload))
        elif kind == "frame" and isinstance(payload, bytes):
            _render_frame(payload)

    # Poll queued messages and reschedule itself for continuous UI updates
    def update_frame() -> None:
        try:
            while True:
                kind, payload = frame_queue.get_nowait()
                _process_queue_message(kind, payload)
        except Empty:
            pass

        root.after(15, update_frame)

    # Stop the receiver thread and close the window cleanly
    def on_close() -> None:
        stop_event.set()
        if root.winfo_exists():
            root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_close)
    root.after(15, update_frame)
    root.mainloop()


# Create and return the core UI widgets used by the viewer
def _setup_ui(root) -> tuple:
    import tkinter as tk

    title_label = tk.Label(root, text="Screen Share", font=("Helvetica", 14, "bold"))
    title_label.pack(side="top", pady=8)

    content_frame = tk.Frame(root, bg="white", relief="solid", borderwidth=1)
    content_frame.pack(fill="both", expand=True, padx=12, pady=8)

    image_label = tk.Label(
        content_frame,
        text="Connecting to server...",
        font=("Helvetica", 12),
        bg="white",
        fg="#666",
        wraplength=400,
    )
    image_label.pack(fill="both", expand=True, padx=8, pady=8)

    status_label = tk.Label(root, text="", font=("Helvetica", 9), bg="#f0f0f0", fg="#333")
    status_label.pack(side="bottom", fill="x", padx=8, pady=4)

    return title_label, content_frame, image_label, status_label
