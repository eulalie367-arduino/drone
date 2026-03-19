import React, { useEffect, useRef, useState } from 'react';

const VideoFeed: React.FC = () => {
    const canvasRef = useRef<HTMLCanvasElement>(null);
    const [isConnected, setIsConnected] = useState(false);
    const [fps, setFps] = useState(0);
    const framesCount = useRef(0);

    useEffect(() => {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const ws = new WebSocket(`${protocol}//${window.location.hostname}:8000/ws/video`);
        ws.binaryType = 'blob';

        ws.onopen = () => setIsConnected(true);
        ws.onclose = () => setIsConnected(false);

        ws.onmessage = async (event) => {
            if (event.data instanceof Blob) {
                const url = URL.createObjectURL(event.data);
                const img = new Image();
                img.onload = () => {
                    const ctx = canvasRef.current?.getContext('2d');
                    if (ctx && canvasRef.current) {
                        ctx.drawImage(img, 0, 0, canvasRef.current.width, canvasRef.current.height);
                    }
                    URL.revokeObjectURL(url);
                    framesCount.current++;
                };
                img.src = url;
            }
        };

        const fpsInterval = setInterval(() => {
            setFps(framesCount.current);
            framesCount.current = 0;
        }, 1000);

        return () => {
            ws.close();
            clearInterval(fpsInterval);
        };
    }, []);

    return (
        <div className="video-container">
            {!isConnected && <div className="overlay">LINK INITIALIZING...</div>}
            <canvas 
                ref={canvasRef} 
                width={1280} 
                height={720} 
                className="video-canvas"
            />
            <div className="video-stats">
                {isConnected ? 'LIVE' : 'OFFLINE'} | {fps} FPS
            </div>
        </div>
    );
};

export default VideoFeed;
