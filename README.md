# CMPT 371 A3 Socket Programming `Remote Screen Sharing`

**Course:** CMPT 371 - Data Communications & Networking  
**Instructor:** Mirza Zaeem Baig  
**Semester:** Spring 2026

## Group Members

| Name         | Student ID | Email         |
| :----------- | :--------- | :------------ |
| Yecheng Wang | 301540271  | ywa415@sfu.ca |
| Owen Twa     | 301475435  | ojt@sfu.ca    |

## 1) Project Overview

This project implements a **Remote Desktop Display Viewer** using Python Socket API.

- The **server** captures its screen continuously.
- The server compresses each frame to JPEG.
- The server streams frames to one or more **viewer clients** over TCP.
- Each client displays the received frames in a live Tkinter window.
- The client socket stays open to receiving while it is running even if server disconnects.
- The server can initiate starting and stopping screen share in the UI.

## 2) Architecture Decision

We chose **client-server** architecture.

### Why client-server is better here

1. **Single source of truth:** only one machine (host) provides the desktop stream.
2. **Simpler role separation:** server = capture/stream, client = receive/display.
3. **Easier scaling:** multiple viewers can connect to one host.
4. **Cleaner demo/testing:** one server terminal + one or more client terminals.

## 3) Protocol Details

The stream protocol is binary over TCP:

1. Capture one frame from the host display.
2. Compress frame to JPEG bytes.
3. Send an **8-byte unsigned big-endian length header**.
4. Send the JPEG payload bytes.
5. Client reads exactly 8 bytes, then exactly payload length bytes, then renders the image.

This avoids TCP message-boundary problems.

## 4) Limitations / Edge Cases

Defined limitations for this project scope:

- **No encryption/authentication:** stream is not end-to-end encrypted.
- **One way screen sharing:** screen sharing only from server to clients and cannot be reversed unless the program is stopped and re-ran.
- **Open broadcast to any connected client:** without a proper GUI application with user accounts or link sharing, anyone with the port number can join as a client viewer.
- **Read-only viewer:** no keyboard/mouse remote control, and mouse is not displayed on the screen viewer.
- **Performance trade-off:** higher FPS and JPEG quality increase CPU/network usage.

## 5) Fresh Environment Setup

### Prerequisites

- Python 3.10+

### Install

1. Clone this repo

2. From project root:

Mac/Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Windows:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## 6) Step-by-Step Run Guide

Before starting, ensure any terminals running this program first activates the virtual environment if not activated yet:

```bash
# mac/linux
source .venv/bin/activate
# windows
.venv\Scripts\activate
```

We have 2 options to run the program. Option 1 is to run the screen sharer and viewer on the same device locally. Option 2 is to share screen between 2 separate devices.

### Option 1: Running locally

Open two terminals in the project root.

#### Terminal A - Start server (host machine)

```bash
# ensure venv is activated
python sender.py
```

#### Terminal B - Start viewer client (same machine)

```bash
# ensure venv is activated
python viewer.py --host 127.0.0.1
```

### Cross-machine run (same LAN/Wifi)

Before beginning, ensure both client and server devices are on the same wifi.

1. If server and client are on different machines, first get the server device ip address:

```bash
# mac / linux
ipconfig getifaddr en0
# windows
ipconfig
# then look for the IPv4 Address
```

note down the result to be entered on the client device, this is the `<SERVER_IP>`

2. start the server on that same device:

```bash
# ensure venv is activated
python sender.py
```

3. next, run this on client machine where `<SERVER_IP>` is the value retrieved from step 1:

```bash
# ensure venv is activated
python viewer.py --host <SERVER_IP> --port 5001

# Example:
# python viewer.py --host 172.16.108.98 --port 5001
```

## 7) Troubleshooting Run Errors

### A) Tkinter missing (`Tkinter is not available in this Python build.`)

- macOS (Homebrew Python):

```bash
brew install python-tk
```

- Ubuntu/Debian:

```bash
sudo apt update
sudo apt install python3-tk
```

- Windows (PowerShell):

You must either repair your downloaded python or reinstall it, tkinter should already be installed

### B) Port already in use (`Address already in use`)

Use another port, and keep server/client ports the same:

```bash
# ensure venv activated
python sender.py
```

In the server UI, set the port field to `5002` (or another free port), then start sharing.

Then make sure the viewer port matches:

```bash
# ensure venv activated
python viewer.py --host 127.0.0.1 --port 5002
```

## 8) Video Demo

2-minute demo link: **(add your final link here)**

## 9) Project Structure

```text
CMPT371_A3_RemoteDisplay/
├── sender.py
├── viewer.py
├── client/
│   ├── __init__.py
│   ├── client.py
│   └── viewer_ui.py
├── server/
│   ├── __init__.py
│   ├── server.py
│   └── ui.py
├── protocol.py
├── requirements.txt
└── README.md
```

## 10) Academic Integrity & References

- **GenAI Usage:** GitHub Copilot used for UI help.
- **References:**
  - https://docs.python.org/3/howto/sockets.html
  - https://pypi.org/project/mss/
  - https://pillow.readthedocs.io/
