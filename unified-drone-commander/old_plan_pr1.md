# X69 Drone Web Control

## Context
Build a web application to control an X69 WiFi drone from a browser. The drone communicates over WiFi in AP mode (drone creates a hotspot, computer connects to it). Browsers cannot send raw UDP, so a Python/FastAPI backend relays commands between the browser (WebSocket) and the drone (UDP). Includes live MJPEG video feed.

## Architecture

```
[Browser] <--WebSocket--> [FastAPI Backend] <--UDP--> [Drone @ 192.168.0.1]
```

## Project Structure

```
drone/
├── backend/
│   ├── main.py              # FastAPI app, WebSocket endpoints
│   ├── drone_protocol.py    # UDP packet construction, command encoding
│   ├── drone_connection.py  # UDP socket management, send/receive loops
│   ├── video_stream.py      # MJPEG video receiver and WebSocket forwarder
│   └── requirements.txt     # fastapi, uvicorn, websockets
├── frontend/
│   ├── index.html           # Main page with video + controls UI
│   ├── style.css            # Layout and styling
│   └── app.js               # WebSocket client, keyboard handler, video display
└── README.md
```

## Implementation Steps

### Step 1: Backend — Drone Protocol (`drone_protocol.py`)
- Implement the 8-byte UDP control packet format (based on E58/common WiFi drone family):
  - Header `0x66`, Roll, Pitch, Throttle, Yaw, Command flags, XOR checksum, Footer `0x99`
  - Neutral stick values = 128, range 0-254
- Command flag bits: takeoff (0x01), land (0x02), emergency stop (0x04), flip (0x08), headless (0x10), motor unlock (0x40), gyro calibrate (0x80)
- Handshake/init packet for port 40000
- Video init packet (`0xEF 0x00 0x04 0x00`) for port 8800

### Step 2: Backend — Drone Connection (`drone_connection.py`)
- UDP socket to drone at `192.168.0.1`
- Control loop: send command packets at 20 Hz (every 50ms) on port 50000
- Handshake on port 40000 at connection start
- Thread-safe state for current stick positions + command flags
- Safety: if no browser input for 1s, revert to neutral (hover)

### Step 3: Backend — Video Stream (`video_stream.py`)
- Send video init packet to port 8800
- Receive MJPEG frames over UDP port 8800
- Parse custom 56-byte header, extract JPEG data
- Buffer and forward complete frames to connected WebSocket clients

### Step 4: Backend — FastAPI App (`main.py`)
- `GET /` — serve frontend static files
- `WS /ws/control` — receive keyboard commands from browser, update drone state
- `WS /ws/video` — push MJPEG frames to browser
- `POST /api/connect` — initiate drone handshake
- `POST /api/takeoff` / `POST /api/land` / `POST /api/emergency` — one-shot commands
- Startup/shutdown lifecycle: create/destroy UDP loops
- Serve frontend via `StaticFiles` mount

### Step 5: Frontend — HTML/CSS (`index.html`, `style.css`)
- Video feed display (canvas or img element)
- Status panel: connection state, battery (if available), signal
- Control reference overlay showing WASD + other keybinds
- Connect / Takeoff / Land / Emergency Stop buttons

### Step 6: Frontend — JavaScript (`app.js`)
- WebSocket connection to `/ws/control` and `/ws/video`
- Keyboard input handler:
  - W/S = throttle up/down
  - A/D = yaw left/right
  - Arrow keys = pitch/roll
  - Space = takeoff/land toggle
  - Esc = emergency stop
- Send stick state as JSON `{ throttle, yaw, pitch, roll }` at ~20 Hz while keys held
- Render MJPEG frames from video WebSocket onto canvas
- Connection state management and reconnect logic

## Protocol Notes (to be verified)
The exact protocol may vary. The plan assumes the common E58-family protocol. When the drone arrives:
1. Connect to the drone's WiFi
2. Use Wireshark to capture packets from the stock app
3. Adjust `drone_protocol.py` if packet format differs (ports, header bytes, packet size)

## Verification
1. **Without drone**: Run `uvicorn backend.main:app`, open browser, verify UI loads, WebSocket connects, keyboard input sends messages
2. **With drone**: Connect to drone WiFi, hit Connect, verify handshake, test takeoff/land, confirm video feed renders
3. **Safety test**: Disconnect browser mid-flight — drone should receive neutral commands then timeout and auto-land

## Dependencies
- Python 3.10+
- `fastapi`, `uvicorn[standard]`, `websockets`
