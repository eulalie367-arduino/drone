import asyncio
import socket
from unittest.mock import AsyncMock, patch, MagicMock
import pytest
from httpx import AsyncClient, ASGITransport

from .drone_protocol import TelemetryPacket, parse_telemetry_packet
from .telemetry_receiver import TelemetryReceiver


# ---------------------------------------------------------------------------
# parse_telemetry_packet tests
# ---------------------------------------------------------------------------

def test_parse_telemetry_valid_10byte_packet():
    # battery=75, wifi=80, mode=0x02, altitude=(0x00<<8|0x3C)=60 → 6.0m
    data = bytes([0x66, 75, 80, 0x02, 0x00, 0x3C, 0x00, 0x00, 0x00, 0x99])
    pkt = parse_telemetry_packet(data)
    assert pkt.battery == 75
    assert pkt.wifi == 80
    assert pkt.flight_mode == 0x02
    assert pkt.altitude == 6.0


def test_parse_telemetry_minimum_6byte_packet():
    # 6 bytes: wifi field present but altitude partially present
    data = bytes([0x66, 50, 60, 0x01, 0x00, 0x14])
    pkt = parse_telemetry_packet(data)
    assert pkt.battery == 50
    assert pkt.wifi == 60
    assert pkt.flight_mode == 0x01
    assert pkt.altitude == 2.0  # (0x00<<8|0x14)=20 → 2.0m


def test_parse_telemetry_rejects_too_short():
    data = bytes([0x66, 50, 60, 0x01, 0x00])  # only 5 bytes
    with pytest.raises(ValueError, match="too short"):
        parse_telemetry_packet(data)


def test_parse_telemetry_clamps_battery():
    data = bytes([0x66, 255, 255, 0x00, 0x00, 0x00])
    pkt = parse_telemetry_packet(data)
    assert pkt.battery == 100
    assert pkt.wifi == 100


def test_parse_telemetry_altitude_encoding():
    # alt high=0x00, low=0x3C → 60 raw → 6.0 metres
    data = bytes([0x66, 0, 0, 0, 0x00, 0x3C])
    pkt = parse_telemetry_packet(data)
    assert pkt.altitude == 6.0


def test_parse_telemetry_altitude_two_byte_range():
    # high=0x01, low=0x00 → 256 → 25.6 metres
    data = bytes([0x66, 0, 0, 0, 0x01, 0x00])
    pkt = parse_telemetry_packet(data)
    assert pkt.altitude == 25.6


# ---------------------------------------------------------------------------
# TelemetryReceiver tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_telemetry_receiver_ignores_handshake_echo():
    """Packets starting with 0x63 (handshake echo) must be silently dropped."""
    callback = AsyncMock()
    receiver = TelemetryReceiver(port=40099)  # offset port avoids system conflicts

    mock_sock = MagicMock()
    handshake_echo = bytes([0x63, 0x63, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x10, 0x99])
    # Return handshake echo once, then raise CancelledError to stop the loop
    mock_sock.recvfrom = AsyncMock(side_effect=[
        (handshake_echo, ("192.168.0.1", 40000)),
        asyncio.CancelledError(),
    ])

    with patch("backend.telemetry_receiver.socket.socket") as mock_socket_cls:
        mock_socket_cls.return_value = mock_sock
        mock_sock.setsockopt = MagicMock()
        mock_sock.bind = MagicMock()
        mock_sock.setblocking = MagicMock()
        mock_sock.close = MagicMock()

        with patch("asyncio.get_event_loop") as mock_loop:
            mock_loop.return_value.sock_recvfrom = mock_sock.recvfrom
            receiver.on_telemetry = callback
            await receiver.start()
            # Allow the loop to process
            await asyncio.sleep(0)
            await receiver.stop()

    callback.assert_not_called()


@pytest.mark.asyncio
async def test_telemetry_receiver_calls_callback_on_valid_packet():
    """A valid telemetry packet should trigger the on_telemetry callback."""
    received: list[TelemetryPacket] = []

    async def capture(pkt: TelemetryPacket):
        received.append(pkt)

    receiver = TelemetryReceiver(port=40098)

    valid_packet = bytes([0x66, 75, 80, 0x02, 0x00, 0x3C, 0x00, 0x00, 0x00, 0x99])

    mock_sock = MagicMock()
    mock_sock.recvfrom = AsyncMock(side_effect=[
        (valid_packet, ("192.168.0.1", 40000)),
        asyncio.CancelledError(),
    ])

    with patch("backend.telemetry_receiver.socket.socket") as mock_socket_cls:
        mock_socket_cls.return_value = mock_sock
        mock_sock.setsockopt = MagicMock()
        mock_sock.bind = MagicMock()
        mock_sock.setblocking = MagicMock()
        mock_sock.close = MagicMock()

        with patch("asyncio.get_event_loop") as mock_loop:
            mock_loop.return_value.sock_recvfrom = mock_sock.recvfrom
            receiver.on_telemetry = capture
            await receiver.start()
            await asyncio.sleep(0)
            await receiver.stop()

    assert len(received) == 1
    assert received[0].battery == 75
    assert received[0].wifi == 80
    assert received[0].altitude == 6.0


# ---------------------------------------------------------------------------
# API endpoint test
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_api_telemetry_returns_defaults():
    """GET /api/telemetry should return all four keys with zero defaults."""
    from .main import app

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/telemetry")

    assert response.status_code == 200
    data = response.json()
    assert "battery" in data
    assert "wifi" in data
    assert "altitude" in data
    assert "flight_mode" in data
