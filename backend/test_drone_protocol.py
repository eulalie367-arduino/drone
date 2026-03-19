import pytest
from backend.drone_protocol import (
    create_control_packet, 
    parse_control_packet, 
    HEADER, 
    FOOTER,
    FLAG_TAKEOFF,
    FLAG_NONE
)

def test_create_packet_neutral():
    # Neutral state: R/P/Y at 128, Throttle at 0, no flags
    packet = create_control_packet(128, 128, 0, 128, FLAG_NONE)
    assert len(packet) == 8
    assert packet[0] == HEADER
    assert packet[1] == 128
    assert packet[2] == 128
    assert packet[3] == 0
    assert packet[4] == 128
    assert packet[5] == FLAG_NONE
    assert packet[7] == FOOTER
    
    # Checksum: 0x66 ^ 128 ^ 128 ^ 0 ^ 128 ^ 0 
    # 128 ^ 128 = 0
    # 0x66 ^ 0 ^ 0 ^ 128 ^ 0 = 0x66 ^ 128 = 102 ^ 128 = 230
    assert packet[6] == 0x66 ^ 128 ^ 128 ^ 0 ^ 128 ^ 0

def test_create_packet_takeoff():
    packet = create_control_packet(128, 128, 0, 128, FLAG_TAKEOFF)
    assert packet[5] == FLAG_TAKEOFF
    
    # Parse back
    roll, pitch, throttle, yaw, flags = parse_control_packet(packet)
    assert roll == 128
    assert flags == FLAG_TAKEOFF

def test_invalid_packets():
    # Wrong length
    with pytest.raises(ValueError, match="Invalid packet length"):
        parse_control_packet(bytes([HEADER, 128, 128, 0, 128, 0, 230]))
        
    # Wrong header
    with pytest.raises(ValueError, match="Invalid header or footer"):
        parse_control_packet(bytes([0x00, 128, 128, 0, 128, 0, 230, FOOTER]))

    # Checksum mismatch
    packet = create_control_packet(128, 128, 0, 128, FLAG_NONE)
    corrupt_packet = bytearray(packet)
    corrupt_packet[6] = 0x00 # Corrupt checksum
    with pytest.raises(ValueError, match="Checksum mismatch"):
        parse_control_packet(bytes(corrupt_packet))

def test_clipping():
    # Values > 255 should be clipped
    packet = create_control_packet(300, -10, 500, 128)
    roll, pitch, throttle, yaw, flags = parse_control_packet(packet)
    assert roll == 255
    assert pitch == 0
    assert throttle == 255
