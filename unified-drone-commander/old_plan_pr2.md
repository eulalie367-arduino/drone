# Plan: Gemini Drone Commander

A futuristic, high-performance web-based controller for the X69 drone series. This application provides a seamless bridge between a web browser and the drone's UDP-based control system, wrapped in a high-fidelity "Gemini" aesthetic.

## 1. Project Goal
Create a functional, visually stunning prototype that allows a user to connect their computer to an X69 drone's WiFi and control it via a browser-dashboard.

## 2. Tech Stack
*   **Frontend:** React (TypeScript)
    *   **Styling:** Vanilla CSS with a focus on glassmorphism, glowing gradients, and CSS-based HUD elements.
    *   **Interactivity:** `nipplejs` for virtual joysticks, `socket.io-client` for real-time telemetry and command feedback.
*   **Backend:** Node.js (Express)
    *   **Communication:** `dgram` for raw UDP packet construction (Lewei/WiFi-UAV protocols).
    *   **Real-time:** `socket.io` for low-latency command forwarding from the frontend.
    *   **Video:** Proxy for MJPEG or H.264 stream (port 8080/7060).

## 3. Key Files & Directory Structure
```text
gemini-drone-commander/
├── backend/
│   ├── server.ts         # Express + Socket.io + UDP Controller
│   └── protocol.ts       # Packet builders for X69 (Lewei/WiFi-UAV)
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── HUD.tsx         # Telemetry and status indicators
│   │   │   ├── Joystick.tsx    # NippleJS wrapper
│   │   │   └── VideoFeed.tsx   # Canvas/Image based stream viewer
│   │   ├── App.tsx
│   │   ├── App.css             # Main "Gemini" theme styling
│   │   └── index.tsx
│   └── public/
└── plan.md               # This document
```

## 4. Implementation Steps

### Phase 1: Foundation (Backend)
1.  **UDP Bridging:** Implement a `DroneClient` class in Node.js that handles `dgram` sockets to `192.168.1.1`.
2.  **Command Mapping:** Define the byte arrays for:
    *   `Takeoff`: `[0x63, 0x63, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x10, 0x99]` (Approximate Lewei format).
    *   `Land`, `Emergency Stop`.
    *   `Movement`: 4-channel joystick data (Throttle, Yaw, Pitch, Roll).
3.  **Socket.io Integration:** Set up an event-driven system to receive `{ axis: value }` from the frontend and emit the corresponding UDP packets every 50ms.

### Phase 2: High-Fidelity UI (Frontend)
1.  **Gemini Aesthetic:**
    *   Deep space blues (`#0a0b1e`) and neon cyans (`#00f2ff`).
    *   Animated "scanline" overlays and glassmorphism panels.
    *   CSS-only HUD elements (crosshairs, artificial horizon).
2.  **Control Layout:**
    *   Dual-joystick layout (Left: Throttle/Yaw, Right: Pitch/Roll).
    *   Center-stage video feed with "Initializing Gemini Link..." placeholder.
    *   Sidebar for battery level, WiFi signal, and flight mode.

### Phase 3: Integration & Safety
1.  **Bidirectional Feedback:** Backend confirms packet delivery via Socket.io to update the HUD "Link" status.
2.  **Safety Interlocks:**
    *   "Arm" switch before takeoff.
    *   Heartbeat: If frontend disconnects, backend sends "Land" command automatically.

## 5. Verification
*   **Packet Inspection:** Use `nc -u -l 50000` (or the target port) locally to verify the backend generates correctly formatted hex strings.
*   **UI Stress Test:** Ensure joysticks maintain 60fps responsiveness.
*   **Drone Test:** Connect to `X69DRONE_xxxxxx` WiFi and verify movement without propellers.
