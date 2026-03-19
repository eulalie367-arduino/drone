import time
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
        assert drone.roll == 128

        websocket.send_text('{"roll": 200, "pitch": 50, "throttle": 10, "yaw": 128}')
        # Allow the server coroutine to process the message
        time.sleep(0.05)

        assert drone.roll == 200
        assert drone.pitch == 50
        assert drone.throttle == 10

    # Reset for other tests
    drone.update_controls(128, 128, 0, 128)
