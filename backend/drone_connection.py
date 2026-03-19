import asyncio
import logging
import socket
import time
from typing import Optional

from .drone_protocol import (
    create_control_packet,
    build_handshake_packet,
    FLAG_LAND,
    FLAG_NONE,
    STICK_NEUTRAL,
    PORT_CONTROL,
    PORT_HANDSHAKE,
    DRONE_IP,
)

logger = logging.getLogger(__name__)

# Safety thresholds (seconds)
NEUTRAL_TIMEOUT = 1.0
LAND_TIMEOUT = 3.0


class DroneConnection:
    """
    Manages UDP communication with the X69 drone.
    Handles the 20Hz control loop, handshake, and safety heartbeat.
    """

    def __init__(
        self,
        drone_ip: str = DRONE_IP,
        control_port: int = PORT_CONTROL,
        handshake_port: int = PORT_HANDSHAKE,
    ):
        self.drone_ip = drone_ip
        self.control_port = control_port
        self.handshake_port = handshake_port

        # Current control state (128 = neutral)
        self.roll = STICK_NEUTRAL
        self.pitch = STICK_NEUTRAL
        self.throttle = 0
        self.yaw = STICK_NEUTRAL
        self.flags = FLAG_NONE

        # Safety: track last browser input
        self._last_input_time: float = time.monotonic()
        self._safety_state: str = "ok"  # "ok", "neutral", "landing"

        self._control_task: Optional[asyncio.Task] = None
        self._socket: Optional[socket.socket] = None
        self._running = False

    @property
    def safety_state(self) -> str:
        return self._safety_state

    async def connect(self) -> None:
        """Perform handshake and start the control heartbeat."""
        if self._running:
            return

        self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._socket.setblocking(False)

        try:
            loop = asyncio.get_event_loop()
            await loop.sock_sendto(
                self._socket,
                build_handshake_packet(),
                (self.drone_ip, self.handshake_port),
            )
        except Exception as e:
            logger.warning("Handshake failed: %s", e)

        self._running = True
        self._last_input_time = time.monotonic()
        self._safety_state = "ok"
        self._control_task = asyncio.create_task(self._control_loop())

    async def disconnect(self) -> None:
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

    async def _control_loop(self) -> None:
        """Sends packets every 50ms. Applies safety timeout logic."""
        loop = asyncio.get_event_loop()
        while self._running:
            self._check_safety()

            packet = create_control_packet(
                self.roll, self.pitch, self.throttle, self.yaw, self.flags
            )
            try:
                if self._socket:
                    await loop.sock_sendto(
                        self._socket, packet, (self.drone_ip, self.control_port)
                    )
            except Exception as e:
                logger.error("Control packet send failed: %s", e)

            await asyncio.sleep(0.05)  # 20Hz

    def _check_safety(self) -> None:
        """Revert to neutral or land if browser input has stopped."""
        elapsed = time.monotonic() - self._last_input_time

        if elapsed >= LAND_TIMEOUT:
            if self._safety_state != "landing":
                logger.warning("Safety: no input for %.1fs — sending LAND", elapsed)
            self.roll = STICK_NEUTRAL
            self.pitch = STICK_NEUTRAL
            self.throttle = 0
            self.yaw = STICK_NEUTRAL
            self.flags = FLAG_LAND
            self._safety_state = "landing"

        elif elapsed >= NEUTRAL_TIMEOUT and self._safety_state == "ok":
            logger.info("Safety: no input for %.1fs — reverting to neutral", elapsed)
            self.roll = STICK_NEUTRAL
            self.pitch = STICK_NEUTRAL
            self.throttle = 0
            self.yaw = STICK_NEUTRAL
            self.flags = FLAG_NONE
            self._safety_state = "neutral"

    def update_controls(
        self,
        roll: int,
        pitch: int,
        throttle: int,
        yaw: int,
        flags: int = FLAG_NONE,
    ) -> None:
        """Update the internal state which will be sent in the next heartbeat."""
        self.roll = roll
        self.pitch = pitch
        self.throttle = throttle
        self.yaw = yaw
        self.flags = flags
        self._last_input_time = time.monotonic()
        self._safety_state = "ok"
