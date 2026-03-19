import asyncio
import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from backend.video_stream import VideoStream

@pytest.mark.asyncio
async def test_video_stream_stripping():
    """Verify that the 56-byte header is stripped from incoming packets."""
    with patch('asyncio.get_event_loop') as mock_loop_getter:
        mock_loop = MagicMock()
        mock_loop_getter.return_value = mock_loop
        
        # Fake MJPEG packet: 56 bytes header + "JPEGDATA"
        header = bytes([0] * 56)
        payload = b"JPEGDATA"
        full_packet = header + payload
        
        # Mock sock_recvfrom to return our packet then raise CancelledError to stop loop
        mock_loop.sock_recvfrom = AsyncMock()
        mock_loop.sock_recvfrom.side_effect = [(full_packet, ("127.0.0.1", 8800)), asyncio.CancelledError()]
        
        received_frames = []
        async def mock_on_frame(frame: bytes):
            received_frames.append(frame)
            
        stream = VideoStream()
        stream.on_frame = mock_on_frame
        
        # Start and run for a tiny bit
        await stream.start()
        await asyncio.sleep(0.01)
        await stream.stop()
        
        assert len(received_frames) == 1
        assert received_frames[0] == payload
