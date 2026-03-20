# TCP frame protocol:
# 1) 8-byte big-endian payload size
# 2) payload bytes (JPEG frame)

from __future__ import annotations

import struct
from socket import socket

HEADER_STRUCT = struct.Struct("!Q")

# Read exactly `size` bytes from a TCP stream.
# Loops until all requested bytes are received because recv may return partial data.
# Raises ConnectionError when peer closes before payload completion.
def recv_exact(sock: socket, size: int) -> bytes:
    chunks: list[bytes] = []
    remaining = size

    while remaining > 0:
        data = sock.recv(remaining)
        if not data:
            raise ConnectionError("Socket closed while receiving data")
        chunks.append(data)
        remaining -= len(data)

    return b"".join(chunks)

# Send one frame using length-prefix framing.
# Writes an 8-byte big-endian size header followed by raw payload bytes.
# Uses sendall to ensure complete transmission at socket layer.
def send_frame(sock: socket, frame_bytes: bytes) -> None:
    header = HEADER_STRUCT.pack(len(frame_bytes))
    sock.sendall(header)
    sock.sendall(frame_bytes)

# Receive one frame using length-prefix framing.
# Reads fixed header first, unpacks payload size, then reads full payload.
# Returns raw JPEG bytes for caller-side decoding/rendering.
def recv_frame(sock: socket) -> bytes:
    header = recv_exact(sock, HEADER_STRUCT.size)
    (frame_size,) = HEADER_STRUCT.unpack(header)
    return recv_exact(sock, frame_size)
