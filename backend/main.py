import asyncio
import json
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from contextlib import asynccontextmanager

from .drone_connection import DroneConnection
from .video_stream import VideoStream
from .drone_protocol import FLAG_LAND

# Shared drone instances
drone = DroneConnection()
video = VideoStream()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Connect to drone and start video listener
    await drone.connect()
    await video.start()
    yield
    # Shutdown: Clean up resources
    await drone.disconnect()
    await video.stop()

app = FastAPI(lifespan=lifespan)

@app.get("/status")
async def get_status():
    return {"status": "online", "drone_ip": drone.drone_ip}

@app.websocket("/ws/control")
async def websocket_control(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            # Expecting JSON: {"roll": 128, "pitch": 128, "throttle": 0, "yaw": 128, "flags": 0}
            data = await websocket.receive_text()
            cmd = json.loads(data)
            
            drone.update_controls(
                roll=cmd.get("roll", 128),
                pitch=cmd.get("pitch", 128),
                throttle=cmd.get("throttle", 0),
                yaw=cmd.get("yaw", 128),
                flags=cmd.get("flags", 0)
            )
    except WebSocketDisconnect:
        # Safety: Neutralize on disconnect
        drone.update_controls(128, 128, 0, 128, FLAG_LAND)
    except Exception as e:
        print(f"Control WS Error: {e}")

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
