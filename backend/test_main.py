import pytest
import time
from fastapi.testclient import TestClient
from .main import app, drone
from .drone_protocol import FLAG_LAND

def test_get_status():
    client = TestClient(app)
    response = client.get("/status")
    assert response.status_code == 200
    assert response.json()["status"] == "online"

def test_control_update():
    client = TestClient(app)
    with client.websocket_connect("/ws/control") as websocket:
        drone.update_controls(128, 128, 0, 128) # Reset state
        websocket.send_text('{"roll": 200, "pitch": 50, "throttle": 10, "yaw": 128}')
        time.sleep(0.1) # Allow time for server to process
        assert drone.roll == 200
        assert drone.pitch == 50

def test_heartbeat_safety_timeout():
    drone.update_controls(128, 128, 0, 128) # Reset state
    client = TestClient(app)
    with client.websocket_connect("/ws/control") as websocket:
        websocket.send_text('{"roll": 150}')
        time.sleep(0.1)
        assert drone.roll == 150
        
        # Wait for timeout
        time.sleep(1.2)
        
        assert drone.flags == FLAG_LAND
