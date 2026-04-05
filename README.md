# CMPT 371 A3 Socket Programming `Remote Screen Sharing`

**Course:** CMPT 371 - Data Communications & Networking  
**Instructor:** Mirza Zaeem Baig  
**Semester:** Spring 2026

## Group Members

| Name         | Student ID | Email         |
| :----------- | :--------- | :------------ |
| Yecheng Wang | 301540271  | ywa415@sfu.ca |
| Owen Twa     | 301475435  | ojt@sfu.ca    |

## 1) Project Description/Overview

This project implements a **Remote Desktop Display Viewer** using Python Socket API, allowing one device to share their screen to other devices to be viewed. This can be ran on the same device or across devices on the same network, and we will demonstrate steps to do both. We used TCP instead of UDP to ensure the live-feed data is sent reliably and in-order.

- The **server** captures the screen continuously, compressing each frame to JPEG.
- The server streams frames to one or more **viewer clients** over TCP.
- Each client displays the received frames in a live Tkinter window.
- The client socket stays open to receiving while it is running even if server disconnects.
- The server can initiate starting and stopping screen share in the UI.

## 2) Architecture Decision

We chose **client-server** architecture.

### Why client-server is better here

1. **Single source of truth:** only one machine (host) provides the desktop stream, similar to other applications like Zoom or Slack.
2. **Simpler role separation:** server = capture/stream, client = receive/display.
3. **Easier scaling:** multiple viewers can connect to one host.
4. **Cleaner demo:** one server terminal + one or more client terminals.

## 3) Protocol Details

We created a specific stream protocol over TCP:

1. Capture one frame from the host display.
2. Compress frame to JPEG bytes.
3. Send an **8-byte unsigned big-endian length header**.
4. Send the JPEG payload bytes.
5. Client reads exactly 8 bytes, then exactly payload length bytes, then renders the image.

The header contains the size of the JPEG payload in bytes, which tells the receiver how many bytes to read for the full frame. This is necessary because TCP streams data as a continous byte stream with no message boundaries, and the client would not know where each frame ends.

## 4) Limitations / Edge Cases

Defined limitations for this project scope:

- **No encryption/authentication:** the screen frames are sent as plain TCP data, so they are not protected with end-to-end encryption, meaning any data could be potentially sniffed or leaked.
- **One way screen sharing:** the server only sends its screen to clients. Clients cannot control the server or send input back, so the program is display-only.
- **Open broadcast to any connected client:** anyone who knows the server IP address and port can connect as a viewer. There is no account system, invite link, or access control to limit who can watch the stream.
- **Read-only viewer:** the client shows the screen image only. It does not forward keyboard or mouse events, and the mouse cursor is not drawn into the shared image, so it is not a remote desktop control tool.
- **Multiple Display Selection:** other applications allow sharers to select which display to share from if they have multiple connected, while this program only shares the primary display.
- **Performance trade-off:** smoother updates and higher JPEG quality make the image look better, but they also increase CPU usage and network traffic. On slower machines or weaker networks, this can reduce responsiveness.

## 5) Fresh Environment Setup

### Prerequisites

- Python 3.10+ (with tkinter support)

### Install

1. Clone this repo

2. Activate virtual environment and install requirements. From project root:

Mac/Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Windows:

```bash
python -m venv .venv # or python instead of python3
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

### Option 2: Cross-machine run (same LAN/Wifi)

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

Note: there is a voice over but it is slightly quiet so turn up the volume.

Link to Youtube: [https://youtu.be/VTHJhOgj5vw?si=uno1VkYrN9sGeEm0](https://youtu.be/VTHJhOgj5vw?si=uno1VkYrN9sGeEm0)

<video width="600" src="https://github.com/user-attachments/assets/593be4c8-0825-48d4-a62a-816fa4bfc9c0"></video>

## 9) Project Structure

```text
CMPT371_A3_RemoteDisplay/
├── client/
│   ├── __init__.py
│   ├── client_ui.py
│   └── client.py
├── server/
│   ├── __init__.py
│   ├── server_ui.py
│   └── server.py
├── CMPT371-RemoteDisplay-Demo.mp4
├── sender.py
├── viewer.py
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
