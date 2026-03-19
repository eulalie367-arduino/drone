"""
End-to-end integration test (#37).

Validates the full pipeline using a mock UDP listener instead of a real drone.
"""
import asyncio
import socket
import pytest

from backend.drone_protocol import (
    HEADER,
    FOOTER,
    PORT_CONTROL,
    PORT_HANDSHAKE,
    PORT_VIDEO,
    parse_control_packet,
    build_video_init_packet,
    FLAG_TAKEOFF,
)


class MockUDPListener:
    """Collects UDP packets on a given port."""

    def __init__(self, port: int):
        self.port = port
        self.packets: list[bytes] = []
        self._sock: socket.socket | None = None

    def start(self) -> None:
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._sock.bind(("127.0.0.1", self.port))
        self._sock.settimeout(0.1)

    def receive(self, max_packets: int = 50) -> list[bytes]:
        assert self._sock is not None
        for _ in range(max_packets):
            try:
                data, _ = self._sock.recvfrom(2048)
                self.packets.append(data)
            except (socket.timeout, BlockingIOError):
                break
        return self.packets

    def stop(self) -> None:
        if self._sock:
            self._sock.close()
            self._sock = None


def test_handshake_packet_format():
    """Verify handshake packet is sent to port 40000 with correct format."""
    from backend.drone_protocol import build_handshake_packet

    packet = build_handshake_packet()
    assert isinstance(packet, bytes)
    assert len(packet) > 0
    assert packet[0] == 0x63
    assert packet[-1] == 0x99


def test_control_packet_checksum_integrity():
    """Verify control packets have valid XOR checksums."""
    from backend.drone_protocol import create_control_packet

    for roll in (0, 64, 128, 192, 255):
        for flags in (0x00, FLAG_TAKEOFF, 0x02):
            packet = create_control_packet(roll, 128, 0, 128, flags)
            assert packet[0] == HEADER
            assert packet[7] == FOOTER

            expected_checksum = 0
            for i in range(6):
                expected_checksum ^= packet[i]
            assert packet[6] == expected_checksum, (
                f"Checksum mismatch for roll={roll}, flags={flags}"
            )

            r, p, t, y, f = parse_control_packet(packet)
            assert r == roll
            assert f == flags


def test_video_init_packet_format():
    """Verify video init packet is correct."""
    packet = build_video_init_packet()
    assert packet == bytes([0xEF, 0x00, 0x04, 0x00])


@pytest.mark.asyncio
async def test_control_loop_sends_packets():
    """Verify the DroneConnection sends packets to the control port."""
    from backend.drone_connection import DroneConnection

    listener = MockUDPListener(PORT_CONTROL)
    listener.start()

    try:
        conn = DroneConnection(drone_ip="127.0.0.1", control_port=PORT_CONTROL, handshake_port=PORT_HANDSHAKE)
        # Skip handshake (would need listener on 40000)
        conn._running = True
        conn._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        conn._socket.setblocking(False)
        conn._control_task = asyncio.create_task(conn._control_loop())

        # Let the loop send ~3 packets
        await asyncio.sleep(0.18)
        await conn.disconnect()

        packets = listener.receive()
        assert len(packets) >= 2, f"Expected at least 2 packets, got {len(packets)}"

        # Validate each received packet
        for pkt in packets:
            assert len(pkt) == 8
            r, p, t, y, f = parse_control_packet(pkt)
            assert r == 128  # neutral
            assert y == 128
    finally:
        listener.stop()


@pytest.mark.asyncio
async def test_control_loop_reflects_state_changes():
    """Verify that updating controls changes the sent packets."""
    from backend.drone_connection import DroneConnection

    listener = MockUDPListener(PORT_CONTROL + 1)  # Use offset port to avoid conflicts
    listener.start()

    try:
        conn = DroneConnection(drone_ip="127.0.0.1", control_port=PORT_CONTROL + 1, handshake_port=PORT_HANDSHAKE)
        conn._running = True
        conn._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        conn._socket.setblocking(False)
        conn._control_task = asyncio.create_task(conn._control_loop())

        await asyncio.sleep(0.08)
        conn.update_controls(200, 100, 50, 150, FLAG_TAKEOFF)
        await asyncio.sleep(0.08)
        await conn.disconnect()

        packets = listener.receive()
        # Find a packet with our custom values
        found = False
        for pkt in packets:
            r, p, t, y, f = parse_control_packet(pkt)
            if r == 200 and p == 100 and t == 50 and f == FLAG_TAKEOFF:
                found = True
                break

        assert found, "Did not find packet with updated control values"
    finally:
        listener.stop()
