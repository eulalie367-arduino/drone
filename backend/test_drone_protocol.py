import pytest
from backend.drone_protocol import (
    create_control_packet,
    parse_control_packet,
    takeoff_packet,
    land_packet,
    emergency_packet,
    gyro_cal_packet,
    build_handshake_packet,
    build_video_init_packet,
    HEADER,
    FOOTER,
    FLAG_TAKEOFF,
    FLAG_LAND,
    FLAG_EMERGENCY,
    FLAG_FLIP,
    FLAG_HEADLESS,
    FLAG_MOTOR_UNLOCK,
    FLAG_GYRO_CALIBRATE,
    FLAG_NONE,
    STICK_NEUTRAL,
    PORT_HANDSHAKE,
    PORT_CONTROL,
    PORT_VIDEO,
)


def test_create_packet_neutral():
    packet = create_control_packet(128, 128, 0, 128, FLAG_NONE)
    assert len(packet) == 8
    assert packet[0] == HEADER
    assert packet[1] == 128
    assert packet[2] == 128
    assert packet[3] == 0
    assert packet[4] == 128
    assert packet[5] == FLAG_NONE
    assert packet[7] == FOOTER
    assert packet[6] == 0x66 ^ 128 ^ 128 ^ 0 ^ 128 ^ 0


def test_create_packet_takeoff():
    packet = create_control_packet(128, 128, 0, 128, FLAG_TAKEOFF)
    assert packet[5] == FLAG_TAKEOFF
    roll, pitch, throttle, yaw, flags = parse_control_packet(packet)
    assert roll == 128
    assert flags == FLAG_TAKEOFF


def test_invalid_packets():
    with pytest.raises(ValueError, match="Invalid packet length"):
        parse_control_packet(bytes([HEADER, 128, 128, 0, 128, 0, 230]))

    with pytest.raises(ValueError, match="Invalid header or footer"):
        parse_control_packet(bytes([0x00, 128, 128, 0, 128, 0, 230, FOOTER]))

    # Checksum mismatch
    packet = create_control_packet(128, 128, 0, 128, FLAG_NONE)
    corrupt = bytearray(packet)
    corrupt[6] = 0x00
    with pytest.raises(ValueError, match="Checksum mismatch"):
        parse_control_packet(bytes(corrupt))


def test_clipping():
    packet = create_control_packet(300, -10, 500, 128)
    roll, pitch, throttle, yaw, flags = parse_control_packet(packet)
    assert roll == 255
    assert pitch == 0
    assert throttle == 255


# --- Issue #22: Command flag encoding ---

def test_flag_constants():
    assert FLAG_NONE == 0x00
    assert FLAG_TAKEOFF == 0x01
    assert FLAG_LAND == 0x02
    assert FLAG_EMERGENCY == 0x04
    assert FLAG_FLIP == 0x08
    assert FLAG_HEADLESS == 0x10
    assert FLAG_MOTOR_UNLOCK == 0x40
    assert FLAG_GYRO_CALIBRATE == 0x80


def test_flags_can_be_combined():
    combined = FLAG_TAKEOFF | FLAG_HEADLESS
    packet = create_control_packet(128, 128, 0, 128, combined)
    _, _, _, _, flags = parse_control_packet(packet)
    assert flags & FLAG_TAKEOFF
    assert flags & FLAG_HEADLESS
    assert not (flags & FLAG_LAND)


def test_takeoff_packet():
    packet = takeoff_packet()
    r, p, t, y, f = parse_control_packet(packet)
    assert r == STICK_NEUTRAL
    assert p == STICK_NEUTRAL
    assert t == 0
    assert y == STICK_NEUTRAL
    assert f == FLAG_TAKEOFF


def test_land_packet():
    _, _, _, _, f = parse_control_packet(land_packet())
    assert f == FLAG_LAND


def test_emergency_packet():
    _, _, _, _, f = parse_control_packet(emergency_packet())
    assert f == FLAG_EMERGENCY


def test_gyro_cal_packet():
    _, _, _, _, f = parse_control_packet(gyro_cal_packet())
    assert f == FLAG_GYRO_CALIBRATE


# --- Issue #23: Handshake and video init packets ---

def test_port_constants():
    assert PORT_HANDSHAKE == 40000
    assert PORT_CONTROL == 50000
    assert PORT_VIDEO == 8800


def test_handshake_packet():
    packet = build_handshake_packet()
    assert isinstance(packet, bytes)
    assert len(packet) > 0
    # Known Lewei handshake format
    assert packet[0] == 0x63
    assert packet[-1] == 0x99


def test_video_init_packet():
    packet = build_video_init_packet()
    assert packet == bytes([0xEF, 0x00, 0x04, 0x00])
    assert len(packet) == 4
