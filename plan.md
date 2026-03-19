# Unified Gemini Drone Commander (X69)

A futuristic, high-performance web-based controller for the X69 drone series. This application combines a robust Python-based relay backend with a high-fidelity "Gemini" aesthetic React frontend.

## 1. Project Goal
Create a functional, visually stunning prototype that allows a user to connect to an X69 drone's WiFi and control it via a browser-based dashboard with real-time video and telemetry.

## 2. Tech Stack
*   **Backend:** Python 3.10+ (FastAPI)
    *   **Communication:** `asyncio` UDP sockets for drone commands (Lewei/E58 protocols).
    *   **Real-time:** WebSockets for low-latency browser-to-backend communication.
    *   **Dependencies:** `fastapi`, `uvicorn[standard]`, `websockets`.
*   **Frontend:** React (TypeScript)
    *   **Styling:** Vanilla CSS with "Gemini" aesthetic (glassmorphism, neon HUD, scanlines).
    *   **Interactivity:** `nipplejs` for virtual joysticks, custom HUD components.
    *   **Video:** Canvas-based MJPEG stream viewer with custom 56-byte header parsing.

## 3. Key Files & Directory Structure
```text
unified-drone-commander/
├── backend/
│   ├── main.py              # FastAPI app & WebSocket handlers
│   ├── drone_protocol.py    # UDP packet construction (E58/Lewei format)
│   ├── drone_connection.py  # UDP socket management & control loops
│   └── video_stream.py      # MJPEG receiver and header parser
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── HUD.tsx         # Telemetry, battery, and status indicators
│   │   │   ├── Joystick.tsx    # NippleJS virtual joystick wrapper
│   │   │   └── VideoFeed.tsx   # MJPEG stream renderer
│   │   ├── App.tsx             # Layout and "Gemini" theme
│   │   └── App.css             # Neon/Glassmorphism styles
│   └── public/
└── plan.md                  # This document
```

## 4. Implementation Steps

### Phase 1: Backend (Python/FastAPI)
1.  **Protocol Core:** Implement 8-byte UDP control packets in `drone_protocol.py`:
    *   Header (`0x66`), Roll, Pitch, Throttle, Yaw, Flags, Checksum, Footer (`0x99`).
    *   Support for Takeoff, Land, Emergency Stop, and Gyro Calibrate.
2.  **UDP Relay:** Implement `DroneConnection` to send packets at 20Hz on port 50000 and handle handshakes on port 40000.
3.  **Video Stream:** In `video_stream.py`, receive port 8800 MJPEG packets, strip the 56-byte custom headers, and buffer JPEG frames.
4.  **WebSocket Bridge:** Set up FastAPI endpoints (`/ws/control`, `/ws/video`) to relay browser inputs to the drone and video frames to the browser.

### Phase 2: High-Fidelity Frontend (React/TS)
1.  **Gemini Aesthetic:**
    *   Deep space blues (`#0a0b1e`) and neon cyans (`#00f2ff`).
    *   Animated scanline overlays and glassmorphism panels.
    *   CSS-only HUD elements (artificial horizon, crosshairs).
2.  **Control Layout:**
    *   Dual virtual joysticks (Left: Throttle/Yaw, Right: Pitch/Roll).
    *   Center-stage video feed with "Link Initializing..." overlay.
3.  **Input Handling:** Support both virtual joysticks and WASD/Arrow key mappings for desktop users.

### Phase 3: Safety & Verification
1.  **Heartbeat Safety:** If the WebSocket connection drops, the backend automatically sends a "Land" or "Neutral" command sequence.
2.  **Verification (No Drone):** Run mock UDP listener (`nc -u -l 50000`) and verify packet structure.
3.  **Verification (With Drone):** Connect to `X69DRONE_xxxxxx`, test motor unlock/takeoff, and verify video latency.

## 5. Verification Checklist
- [x] Backend generates valid XOR checksums for UDP packets.
- [x] MJPEG header parsing correctly extracts JPEG start of image (`0xFFD8`).
- [x] UI maintains 60fps while rendering video and joystick state.
- [x] Safety timeout triggers "Land" after 1s of lost communication.
