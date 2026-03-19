import pytest
from fastapi.testclient import TestClient
from .main import app, drone

def test_get_status():
    client = TestClient(app)
    response = client.get("/status")
    assert response.status_code == 200
    assert response.json()["status"] == "online"

def test_control_update():
    client = TestClient(app)
    with client.websocket_connect("/ws/control") as websocket:
        # Initial state (set in main.py)
        assert drone.roll == 128
        
        # Send update
        websocket.send_text('{"roll": 200, "pitch": 50, "throttle": 10, "yaw": 128}')
        
        # Give it a tiny bit of time
        assert drone.roll == 200
        assert drone.pitch == 50
        assert drone.throttle == 10
