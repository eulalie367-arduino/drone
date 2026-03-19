import asyncio
import socket
from typing import Optional, Callable, Awaitable

class VideoStream:
    """
    Receives MJPEG stream from the drone on port 8800.
    Strips the 56-byte custom header and provides raw JPEG data.
    """
    def __init__(self, host: str = "0.0.0.0", port: int = 8800):
        self.host = host
        self.port = port
        self.header_size = 56
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._socket: Optional[socket.socket] = None
        self.on_frame: Optional[Callable[[bytes], Awaitable[None]]] = None

    async def start(self):
        """Start the UDP listener task."""
        if self._running:
            return

        self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Allow multiple apps to bind to the same port for testing/relay
        self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._socket.bind((self.host, self.port))
        self._socket.setblocking(False)

        self._running = True
        self._task = asyncio.create_task(self._listen())

    async def stop(self):
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

    async def _listen(self):
        """UDP listener loop."""
        loop = asyncio.get_event_loop()
        while self._running:
            try:
                # Max packet size for UDP is 65535, but drone packets are usually < 2048
                data, addr = await loop.sock_recvfrom(self._socket, 2048)
                
                if len(data) > self.header_size:
                    # Strip 56-byte header
                    jpeg_data = data[self.header_size:]
                    
                    # Optional: Verify JPEG Start of Image (SOI) marker 0xFFD8
                    # Some packets might be fragments, so we relay all data after header
                    if self.on_frame:
                        await self.on_frame(jpeg_data)
                        
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Video stream error: {e}")
                await asyncio.sleep(0.1) # Avoid tight error loop
