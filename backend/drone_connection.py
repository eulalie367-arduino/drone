import asyncio
import socket
from typing import Optional
from .drone_protocol import create_control_packet, FLAG_NONE

class DroneConnection:
    """
    Manages UDP communication with the X69 drone.
    Handles the 20Hz control loop and handshake protocols.
    """
    def __init__(self, drone_ip: str = "192.168.10.1", control_port: int = 50000, handshake_port: int = 40000):
        self.drone_ip = drone_ip
        self.control_port = control_port
        self.handshake_port = handshake_port
        
        # Current control state (128 = neutral)
        self.roll = 128
        self.pitch = 128
        self.throttle = 0
        self.yaw = 128
        self.flags = FLAG_NONE
        
        self._control_task: Optional[asyncio.Task] = None
        self._socket: Optional[socket.socket] = None
        self._running = False

    async def connect(self):
        """Perform handshake and start the control heartbeat."""
        if self._running:
            return

        # Initialize UDP socket
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._socket.setblocking(False)
        
        # Phase 1: Handshake (Port 40000)
        # Typically requires sending a specific sequence; here we send a placeholder
        # Based on E58/Lewei protocols, this might be "ctrl" or just an empty packet
        try:
            loop = asyncio.get_event_loop()
            await loop.sock_sendto(self._socket, b"handshake", (self.drone_ip, self.handshake_port))
        except Exception as e:
            print(f"Handshake failed: {e}")
            
        # Phase 2: Start Control Loop (20Hz / 50ms)
        self._running = True
        self._control_task = asyncio.create_task(self._control_loop())

    async def disconnect(self):
        """Stop the heartbeat and close the socket."""
        self._running = False
        if self._control_task:
            self._control_task.cancel()
            try:
                await self._control_task
            except asyncio.CancelledError:
                pass
        
        if self._socket:
            self._socket.close()
            self._socket = None

    async def _control_loop(self):
        """Sends packets every 50ms to keep the connection alive."""
        loop = asyncio.get_event_loop()
        while self._running:
            packet = create_control_packet(
                self.roll, self.pitch, self.throttle, self.yaw, self.flags
            )
            try:
                if self._socket:
                    await loop.sock_sendto(self._socket, packet, (self.drone_ip, self.control_port))
            except Exception as e:
                print(f"Control packet send failed: {e}")
            
            await asyncio.sleep(0.05) # 20Hz

    def update_controls(self, roll: int, pitch: int, throttle: int, yaw: int, flags: int = FLAG_NONE):
        """Update the internal state which will be sent in the next heartbeat."""
        self.roll = roll
        self.pitch = pitch
        self.throttle = throttle
        self.yaw = yaw
        self.flags = flags
