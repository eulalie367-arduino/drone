import asyncio
import logging
import socket
from typing import Optional, Callable, Awaitable

from .drone_protocol import TelemetryPacket, parse_telemetry_packet, PORT_HANDSHAKE

logger = logging.getLogger(__name__)

TelemetryCallback = Callable[[TelemetryPacket], Awaitable[None]]


class TelemetryReceiver:
    """
    Listens for UDP status packets from the X69 drone on PORT_HANDSHAKE (40000).
    The drone sends ~10-byte telemetry replies to the host that initiated the handshake.
    """

    def __init__(self, host: str = "0.0.0.0", port: int = PORT_HANDSHAKE):
        self.host = host
        self.port = port
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._socket: Optional[socket.socket] = None
        self.on_telemetry: Optional[TelemetryCallback] = None

    async def start(self) -> None:
        """Start the UDP listener task."""
        if self._running:
            return
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._socket.bind((self.host, self.port))
        self._socket.setblocking(False)
        self._running = True
        self._task = asyncio.create_task(self._listen())

    async def stop(self) -> None:
        """Stop the listener and close the socket."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        if self._socket:
            self._socket.close()
            self._socket = None

    async def _listen(self) -> None:
        """UDP receive loop."""
        loop = asyncio.get_event_loop()
        while self._running:
            try:
                data, _ = await loop.sock_recvfrom(self._socket, 256)

                # Skip handshake echo packets (start with 0x63) and too-short packets
                if len(data) < 6 or data[0] == 0x63:
                    continue

                try:
                    packet = parse_telemetry_packet(data)
                    if self.on_telemetry:
                        await self.on_telemetry(packet)
                except ValueError as e:
                    logger.debug("Ignoring unrecognised telemetry packet: %s", e)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.warning("Telemetry receive error: %s", e)
                await asyncio.sleep(0.1)
