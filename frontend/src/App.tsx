import React, { useState, useEffect, useRef, useCallback } from 'react';
import './App.css';
import VideoFeed from './components/VideoFeed';
import Joystick from './components/Joystick';
import HUD from './components/HUD';

const FLAG_TAKEOFF = 0x01;
const FLAG_LAND = 0x02;
const FLAG_EMERGENCY = 0x04;
const FLAG_GYRO_CAL = 0x08;

function App() {
    const [ws, setWs] = useState<WebSocket | null>(null);
    const [status, setStatus] = useState('Standby');
    const controls = useRef({ roll: 128, pitch: 128, throttle: 0, yaw: 128, flags: 0 });

    useEffect(() => {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const newWs = new WebSocket(`${protocol}//${window.location.hostname}:8000/ws/control`);
        
        newWs.onopen = () => setStatus('Connected');
        newWs.onclose = () => setStatus('Offline');
        setWs(newWs);

        // Send heartbeat at 20Hz
        const interval = setInterval(() => {
            if (newWs.readyState === WebSocket.OPEN) {
                newWs.send(JSON.stringify(controls.current));
                // Clear one-time flags (takeoff/land) after sending
                if (controls.current.flags !== 0) {
                    controls.current.flags = 0;
                }
            }
        }, 50);

        return () => {
            clearInterval(interval);
            newWs.close();
        };
    }, []);

    const handleLeftMove = useCallback((data: { x: number; y: number }) => {
        // Left: Throttle (y) and Yaw (x)
        // Normalize: x/y are -1 to 1. Convert to 0-255 or 0-100
        controls.current.yaw = Math.round(128 + data.x * 127);
        // Throttle is 0-255, typically up is positive.
        controls.current.throttle = Math.max(0, Math.min(255, Math.round(data.y * 255)));
    }, []);

    const handleRightMove = useCallback((data: { x: number; y: number }) => {
        // Right: Pitch (y) and Roll (x)
        controls.current.roll = Math.round(128 + data.x * 127);
        controls.current.pitch = Math.round(128 + data.y * 127);
    }, []);

    const resetLeft = useCallback(() => {
        controls.current.yaw = 128;
        // Keep throttle where it is (manual) or reset? Usually neutral for alt-hold drones is 128
        // For simple drones, 0 is idle.
    }, []);

    const resetRight = useCallback(() => {
        controls.current.roll = 128;
        controls.current.pitch = 128;
    }, []);

    const sendFlag = (flag: number) => {
        controls.current.flags = flag;
    };

    return (
        <div className="app-container">
            <VideoFeed />
            <HUD battery={84} wifi={92} status={status} altitude={1.2} />
            
            <div className="ui-overlay">
                <div className="side-panel left">
                    <Joystick side="left" onMove={handleLeftMove} onEnd={resetLeft} />
                </div>

                <div className="center-actions">
                    <button className="btn neon takeoff" onClick={() => sendFlag(FLAG_TAKEOFF)}>TAKEOFF</button>
                    <button className="btn neon land" onClick={() => sendFlag(FLAG_LAND)}>LAND</button>
                    <button className="btn neon emergency" onClick={() => sendFlag(FLAG_EMERGENCY)}>EMERGENCY</button>
                    <button className="btn neon gyro" onClick={() => sendFlag(FLAG_GYRO_CAL)}>GYRO CAL</button>
                </div>

                <div className="side-panel right">
                    <Joystick side="right" onMove={handleRightMove} onEnd={resetRight} />
                </div>
            </div>

            <div className="hud-corners">
                <div className="corner tl"></div>
                <div className="corner tr"></div>
                <div className="corner bl"></div>
                <div className="corner br"></div>
            </div>
        </div>
    );
}

export default App;
