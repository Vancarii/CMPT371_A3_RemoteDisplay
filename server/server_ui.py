import tkinter as tk
from tkinter import scrolledtext
import threading

from server.server import run_server, ServerConfig


class ServerUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Remote Display Server")

        self.server_thread = None
        self.stop_event = None

        # Inputs
        tk.Label(root, text="Host:").grid(row=0, column=0)
        self.host_entry = tk.Entry(root)
        self.host_entry.insert(0, "0.0.0.0")
        self.host_entry.grid(row=0, column=1)

        tk.Label(root, text="Port:").grid(row=1, column=0)
        self.port_entry = tk.Entry(root)
        self.port_entry.insert(0, "5001")
        self.port_entry.grid(row=1, column=1)

        # Buttons
        self.start_btn = tk.Button(root, text="Start", command=self.start_server)
        self.start_btn.grid(row=2, column=0)

        self.stop_btn = tk.Button(root, text="Stop", command=self.stop_server, state=tk.DISABLED)
        self.stop_btn.grid(row=2, column=1)

        # Log output
        self.log_box = scrolledtext.ScrolledText(root, width=60, height=15, state='disabled')
        self.log_box.grid(row=3, column=0, columnspan=2, padx=10, pady=10)

        self.root.protocol("WM_DELETE_WINDOW", self.on_exit)

    # Thread-safe log function
    def log(self, message):
        def append():
            self.log_box.config(state='normal')
            self.log_box.insert(tk.END, message + "\n")
            self.log_box.see(tk.END)
            self.log_box.config(state='disabled')

        self.root.after(0, append)  # ensures UI thread safety

    def start_server(self):
        if self.server_thread and self.server_thread.is_alive():
            self.log("[!] Server already running")
            return

        config = ServerConfig(
            self.host_entry.get(),
            int(self.port_entry.get())
        )

        self.stop_event = threading.Event()

        self.server_thread = threading.Thread(
            target=run_server,
            args=(config, self.stop_event, self.log),
            daemon=True
        )
        self.server_thread.start()

        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)

    def stop_server(self):
        if self.stop_event:
            self.stop_event.set()
            self.log("[UI] Stop requested")

        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)

    def on_exit(self):
        self.stop_server()
        self.root.destroy()


def main() -> None:
    root = tk.Tk()
    app = ServerUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()