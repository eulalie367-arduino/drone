import asyncio
import time
import pytest
from unittest.mock import MagicMock, AsyncMock, patch

from backend.drone_connection import (
    DroneConnection,
    NEUTRAL_TIMEOUT,
    LAND_TIMEOUT,
)
from backend.drone_protocol import FLAG_NONE, FLAG_LAND, STICK_NEUTRAL


@pytest.mark.asyncio
async def test_drone_connection_loop():
    """Verify that the control loop starts and sends packets."""
    with patch("asyncio.get_event_loop") as mock_loop_getter:
        mock_loop = MagicMock()
        mock_loop_getter.return_value = mock_loop
        mock_loop.sock_sendto = AsyncMock()

        conn = DroneConnection(drone_ip="127.0.0.1")
        await conn.connect()
        await asyncio.sleep(0.15)

        # Once for handshake + several for control
        assert mock_loop.sock_sendto.call_count >= 2
        await conn.disconnect()


@pytest.mark.asyncio
async def test_update_controls():
    """Verify that updating controls reflects in state."""
    conn = DroneConnection()
    conn.update_controls(roll=200, pitch=100, throttle=50, yaw=150, flags=FLAG_NONE)

    assert conn.roll == 200
    assert conn.pitch == 100
    assert conn.throttle == 50
    assert conn.yaw == 150
