from __future__ import annotations

import io
import threading
from queue import Empty, Queue
from typing import Callable

from PIL import Image
from protocol import MSG_FRAME, MSG_STATUS, MessageKind, QueueMessage

# Main entry point for the client viewer UI
# This function creates the window, starts a background receiver thread,
# and keeps the screen updated with status text and incoming image frames
# It also handles clean shutdown when the user closes the window
def run_viewer(config: object, receiver_loop: Callable) -> None:
    # catch missing tkinter incase python was built without it
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

    _, content_frame, image_label, status_label = _setup_ui(root)
    tk_image_holder = {"image": None}

    # Handle text status updates from the receiver thread.
    # This updates the status bar and also changes the center message
    # so users can clearly see if the stream is loading or has stopped.
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

    # Convert raw frame bytes into an image and show it in the UI.
    # The frame is resized to fit inside the display panel while
    # keeping the original aspect ratio for better visual quality.
    def _render_frame(frame_bytes: bytes) -> None:
        image = Image.open(io.BytesIO(frame_bytes))
        max_width = content_frame.winfo_width() - 16
        max_height = content_frame.winfo_height() - 16

        if max_width > 1 and max_height > 1:
            image.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)

        tk_image = ImageTk.PhotoImage(image=image)
        tk_image_holder["image"] = tk_image
        image_label.configure(image=tk_image, text="", fg="black")

    # Decide how to process one message from the queue.
    # Status messages update text labels, and frame messages
    # are drawn into the main image area.
    def _process_queue_message(kind: MessageKind, payload: bytes | str) -> None:
        if kind == MSG_STATUS:
            _handle_status_message(str(payload))
        elif kind == MSG_FRAME and isinstance(payload, bytes):
            _render_frame(payload)

    # Repeatedly check for new messages without freezing the window
    # Process only a few items per tick, so Tk always has time to
    # handle user actions like resize and close button clicks
    def update_frame() -> None:
        for _ in range(3):
            try:
                kind, payload = frame_queue.get_nowait()
                _process_queue_message(kind, payload)
            except Empty:
                break

        root.after(15, update_frame)

    # Clean shutdown handler for the window close button
    # It signals the background thread to stop first,
    # then safely destroys the Tk window
    def on_close() -> None:
        stop_event.set()
        if root.winfo_exists():
            root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_close)
    root.after(15, update_frame)
    root.mainloop()


# Build the main set of UI widgets used by the viewer
# This keeps layout code in one place and returns references
# needed later to update the image and status text
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
