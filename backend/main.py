import asyncio
import json
import time
from dataclasses import dataclass, asdict
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from contextlib import asynccontextmanager

from .drone_connection import DroneConnection
from .video_stream import VideoStream
from .telemetry_receiver import TelemetryReceiver
from .drone_protocol import (
    FLAG_EMERGENCY,
    FLAG_LAND,
    FLAG_NONE,
    FLAG_TAKEOFF,
    STICK_NEUTRAL,
    TelemetryPacket,
)


@dataclass
class TelemetryState:
    battery: int = 0
    wifi: int = 0
    altitude: float = 0.0
    flight_mode: int = 0


# Shared drone instances
drone = DroneConnection()
video = VideoStream()
telemetry = TelemetryReceiver()
telemetry_state = TelemetryState()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await drone.connect()
    await video.start()

    async def _on_telemetry(packet: TelemetryPacket) -> None:
        telemetry_state.battery = packet.battery
        telemetry_state.wifi = packet.wifi
        telemetry_state.altitude = packet.altitude
        telemetry_state.flight_mode = packet.flight_mode

    telemetry.on_telemetry = _on_telemetry
    await telemetry.start()

    yield

    await drone.disconnect()
    await video.stop()
    await telemetry.stop()

app = FastAPI(lifespan=lifespan)


@app.get("/status")
async def get_status():
    return {"status": "online", "drone_ip": drone.drone_ip}


@app.get("/api/telemetry")
async def get_telemetry():
    return asdict(telemetry_state)


@app.post("/api/connect")
async def api_connect():
    await drone.connect()
    return {"status": "connected", "drone_ip": drone.drone_ip}


@app.post("/api/takeoff")
async def api_takeoff():
    drone.update_controls(STICK_NEUTRAL, STICK_NEUTRAL, 0, STICK_NEUTRAL, FLAG_TAKEOFF)
    return {"status": "takeoff"}


@app.post("/api/land")
async def api_land():
    drone.update_controls(STICK_NEUTRAL, STICK_NEUTRAL, 0, STICK_NEUTRAL, FLAG_LAND)
    return {"status": "landing"}


@app.post("/api/emergency")
async def api_emergency():
    drone.update_controls(STICK_NEUTRAL, STICK_NEUTRAL, 0, STICK_NEUTRAL, FLAG_EMERGENCY)
    return {"status": "emergency_stop"}

@app.websocket("/ws/control")
async def websocket_control(websocket: WebSocket):
    await websocket.accept()
    last_heartbeat = time.time()

    async def monitor_heartbeat():
        nonlocal last_heartbeat
        while True:
            await asyncio.sleep(0.5)
            if time.time() - last_heartbeat > 1.0:
                print("Safety Timeout: No client heartbeat. Landing drone.")
                drone.update_controls(128, 128, 0, 128, FLAG_LAND)
                break

    monitor_task = asyncio.create_task(monitor_heartbeat())

    try:
        while True:
            data = await websocket.receive_text()
            last_heartbeat = time.time()
            cmd = json.loads(data)
            
            drone.update_controls(
                roll=cmd.get("roll", 128),
                pitch=cmd.get("pitch", 128),
                throttle=cmd.get("throttle", 0),
                yaw=cmd.get("yaw", 128),
                flags=cmd.get("flags", FLAG_NONE)
            )
    except WebSocketDisconnect:
        drone.update_controls(128, 128, 0, 128, FLAG_LAND)
        print("Client disconnected. Landing drone.")
    except Exception as e:
        print(f"Control WS Error: {e}")
    finally:
        monitor_task.cancel()

@app.websocket("/ws/telemetry")
async def websocket_telemetry(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            await asyncio.sleep(0.5)  # 2Hz push
            await websocket.send_json(asdict(telemetry_state))
    except WebSocketDisconnect:
        pass
    except Exception as e:
        print(f"Telemetry WS Error: {e}")


@app.websocket("/ws/video")
async def websocket_video(websocket: WebSocket):
    await websocket.accept()
    
    # Callback to send frame to this specific client
    async def send_frame(frame: bytes):
        try:
            # Send as binary message
            await websocket.send_bytes(frame)
        except Exception:
            # Handle client disconnect during send
            pass

    # Register callback
    video.on_frame = send_frame
    
    try:
        while True:
            # Keep connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        video.on_frame = None
    except Exception as e:
        print(f"Video WS Error: {e}")
        video.on_frame = None
