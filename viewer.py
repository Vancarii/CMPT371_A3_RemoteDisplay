import argparse

from client.client import ClientConfig, receiver_loop
from client.client_ui import run_viewer

# Client entry point, parse CLI args and start the viewer UI with the receiver loop.
def parse_args() -> ClientConfig:
    parser = argparse.ArgumentParser(description="CMPT 371 Remote Display Viewer")
    parser.add_argument("--host", required=True, help="Server IP or hostname")
    parser.add_argument("--port", type=int, default=5001, help="Server port (default: 5001)")
    args = parser.parse_args()
    return ClientConfig(server_host=args.host, server_port=args.port)


def main() -> None:
    config = parse_args()
    try:
        run_viewer(config, receiver_loop)
    except KeyboardInterrupt:
        print("\nViewer stopped by user.")
    except OSError as exc:
        print(f"Connection failed: {exc}")
    except RuntimeError as exc:
        print(exc)


if __name__ == "__main__":
    main()
