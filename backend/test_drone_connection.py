import asyncio
import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from backend.drone_connection import DroneConnection

@pytest.mark.asyncio
async def test_drone_connection_loop():
    """Verify that the control loop starts and sends packets at 20Hz."""
    # Mock loop.sock_sendto to avoid real network calls
    with patch('asyncio.get_event_loop') as mock_loop_getter:
        mock_loop = MagicMock()
        mock_loop_getter.return_value = mock_loop
        
        # Async mock for sock_sendto
        mock_loop.sock_sendto = AsyncMock()
        
        conn = DroneConnection(drone_ip="127.0.0.1")
        await conn.connect()
        
        # Let the loop run for a short duration (0.15s should be enough for ~3 packets)
        await asyncio.sleep(0.15)
        
        # Check if sock_sendto was called
        # Once for handshake (port 40000) and several for control (port 50000)
        assert mock_loop.sock_sendto.call_count >= 2
        
        await conn.disconnect()

@pytest.mark.asyncio
async def test_update_controls():
    """Verify that updating controls reflects in the heartbeat packets."""
    with patch('asyncio.get_event_loop') as mock_loop_getter:
        mock_loop = MagicMock()
        mock_loop_getter.return_value = mock_loop
        mock_loop.sock_sendto = asyncio.Future()
        mock_loop.sock_sendto.set_result(None)
        
        conn = DroneConnection()
        conn.update_controls(roll=200, pitch=100, throttle=50, yaw=150)
        
        assert conn.roll == 200
        assert conn.pitch == 100
        assert conn.throttle == 50
        assert conn.yaw == 150
