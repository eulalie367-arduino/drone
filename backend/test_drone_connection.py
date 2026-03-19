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
    conn.update_controls(roll=200, pitch=100, throttle=50, yaw=150)

    assert conn.roll == 200
    assert conn.pitch == 100
    assert conn.throttle == 50
    assert conn.yaw == 150


def test_update_controls_resets_safety():
    """update_controls should reset the safety timer and state."""
    conn = DroneConnection()
    conn._safety_state = "neutral"
    conn._last_input_time = time.monotonic() - 10.0

    conn.update_controls(128, 128, 50, 128)

    assert conn.safety_state == "ok"
    assert time.monotonic() - conn._last_input_time < 0.1


def test_safety_neutral_after_timeout():
    """After NEUTRAL_TIMEOUT with no input, state should go to neutral."""
    conn = DroneConnection()
    conn.update_controls(200, 200, 100, 200, flags=0x01)
    conn._last_input_time = time.monotonic() - (NEUTRAL_TIMEOUT + 0.1)

    conn._check_safety()

    assert conn.safety_state == "neutral"
    assert conn.roll == STICK_NEUTRAL
    assert conn.pitch == STICK_NEUTRAL
    assert conn.throttle == 0
    assert conn.yaw == STICK_NEUTRAL
    assert conn.flags == FLAG_NONE


def test_safety_land_after_timeout():
    """After LAND_TIMEOUT with no input, state should go to landing."""
    conn = DroneConnection()
    conn.update_controls(200, 200, 100, 200)
    conn._last_input_time = time.monotonic() - (LAND_TIMEOUT + 0.1)

    conn._check_safety()

    assert conn.safety_state == "landing"
    assert conn.flags == FLAG_LAND
    assert conn.throttle == 0


def test_safety_no_trigger_within_timeout():
    """Within timeout, safety should remain ok."""
    conn = DroneConnection()
    conn.update_controls(200, 200, 100, 200)

    conn._check_safety()

    assert conn.safety_state == "ok"
    assert conn.roll == 200
    assert conn.throttle == 100


def test_safety_neutral_does_not_regress_to_ok():
    """Once in neutral state, _check_safety should not reset to ok."""
    conn = DroneConnection()
    conn._last_input_time = time.monotonic() - (NEUTRAL_TIMEOUT + 0.5)
    conn._safety_state = "neutral"

    conn._check_safety()

    assert conn.safety_state in ("neutral", "landing")


def test_safety_landing_stays_landing():
    """Once landing, should remain landing even after more time."""
    conn = DroneConnection()
    conn._last_input_time = time.monotonic() - 10.0
    conn._safety_state = "landing"

    conn._check_safety()

    assert conn.safety_state == "landing"
    assert conn.flags == FLAG_LAND
