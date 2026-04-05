from __future__ import annotations
import struct
from socket import socket
from typing import Literal

# string constants
MSG_FRAME: Literal["frame"] = "frame"
MSG_STATUS: Literal["status"] = "status"
MessageKind = Literal["frame", "status"]
# QueueMessage is a tuple where kind is either "frame" (bytes) or "status" (str)
QueueMessage = tuple[MessageKind, bytes | str]

# Q means unsigned 8-byte int, ! means big-endian network byte order
# use this to turn frame length into a fixed 8 byte header
HEADER_STRUCT = struct.Struct("!Q")

# Read exactly size bytes from a TCP stream
# Loops until all requested bytes are received
# Raises ConnectionError when peer closes before payload completion
def recv_exact(sock: socket, size: int) -> bytes:
    chunks: list[bytes] = []
    remaining = size

    while remaining > 0:
        data = sock.recv(remaining)
        if not data:
            raise ConnectionError("Socket closed while receiving data")
        chunks.append(data)
        remaining -= len(data)

    # Join all received chunks into a single bytes object
    return b"".join(chunks)

# Send one frame
# Writes an 8-byte big-endian size header followed by raw payload bytes
# Uses sendall to ensure complete transmission at socket layer
def send_frame(sock: socket, frame_bytes: bytes) -> None:
    header = HEADER_STRUCT.pack(len(frame_bytes))
    sock.sendall(header)
    sock.sendall(frame_bytes)

# Receive one frame
# Reads fixed header first, unpacks payload size, then reads full payload
# Returns raw JPEG bytes for caller-side decoding/rendering
def recv_frame(sock: socket) -> bytes:
    header = recv_exact(sock, HEADER_STRUCT.size)
    frame_size = HEADER_STRUCT.unpack(header)[0]
    return recv_exact(sock, frame_size)
