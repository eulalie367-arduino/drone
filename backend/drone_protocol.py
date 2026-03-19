from typing import Tuple

# Protocol Constants
HEADER = 0x66
FOOTER = 0x99

# Port Constants
PORT_HANDSHAKE = 40000
PORT_CONTROL = 50000
PORT_VIDEO = 8800

# Drone IP (AP mode default)
DRONE_IP = "192.168.0.1"

# Flags
FLAG_NONE = 0x00
FLAG_TAKEOFF = 0x01
FLAG_LAND = 0x02
FLAG_EMERGENCY = 0x04
FLAG_FLIP = 0x08
FLAG_HEADLESS = 0x10
FLAG_MOTOR_UNLOCK = 0x40
FLAG_GYRO_CALIBRATE = 0x80

# Neutral stick value
STICK_NEUTRAL = 128

def create_control_packet(
    roll: int, 
    pitch: int, 
    throttle: int, 
    yaw: int, 
    flags: int = FLAG_NONE
) -> bytes:
    """
    Constructs an 8-byte UDP control packet for the X69 drone.
    
    Format: [HEADER, ROLL, PITCH, THROTTLE, YAW, FLAGS, CHECKSUM, FOOTER]
    - Bytes 1-5 (Roll-Flags) are standard 0-255 values (128 = neutral for R/P/Y).
    - Checksum is XOR of bytes 0 (Header) through 5 (Flags).
    """
    # Ensure values are within 1-byte range (0-255)
    roll = max(0, min(255, roll))
    pitch = max(0, min(255, pitch))
    throttle = max(0, min(255, throttle))
    yaw = max(0, min(255, yaw))
    flags = max(0, min(255, flags))
    
    packet_data = [HEADER, roll, pitch, throttle, yaw, flags]
    
    # Calculate XOR checksum of bytes 0 through 5
    checksum = 0
    for b in packet_data:
        checksum ^= b
        
    packet_data.append(checksum)
    packet_data.append(FOOTER)
    
    return bytes(packet_data)

def parse_control_packet(packet: bytes) -> Tuple[int, int, int, int, int]:
    """
    Validates and parses an 8-byte control packet.
    Returns (roll, pitch, throttle, yaw, flags).
    Raises ValueError if packet is invalid.
    """
    if len(packet) != 8:
        raise ValueError(f"Invalid packet length: {len(packet)}. Expected 8.")
    
    if packet[0] != HEADER or packet[7] != FOOTER:
        raise ValueError("Invalid header or footer.")
    
    # Verify checksum
    checksum = 0
    for i in range(6):
        checksum ^= packet[i]
        
    if checksum != packet[6]:
        raise ValueError(f"Checksum mismatch: calculated {checksum}, got {packet[6]}.")
        
    return (packet[1], packet[2], packet[3], packet[4], packet[5])


def _neutral_packet(flags: int) -> bytes:
    """Create a control packet with neutral sticks and the given flags."""
    return create_control_packet(
        STICK_NEUTRAL, STICK_NEUTRAL, 0, STICK_NEUTRAL, flags
    )


def takeoff_packet() -> bytes:
    return _neutral_packet(FLAG_TAKEOFF)


def land_packet() -> bytes:
    return _neutral_packet(FLAG_LAND)


def emergency_packet() -> bytes:
    return _neutral_packet(FLAG_EMERGENCY)


def gyro_cal_packet() -> bytes:
    return _neutral_packet(FLAG_GYRO_CALIBRATE)


def build_handshake_packet() -> bytes:
    """Handshake packet sent to PORT_HANDSHAKE to initiate connection."""
    return bytes([0x63, 0x63, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x10, 0x99])


def build_video_init_packet() -> bytes:
    """Video init packet sent to PORT_VIDEO to start MJPEG stream."""
    return bytes([0xEF, 0x00, 0x04, 0x00])
