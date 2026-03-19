import { useState, useEffect, useRef, useCallback } from 'react';
import './App.css';
import VideoFeed from './components/VideoFeed';
import Joystick from './components/Joystick';
import HUD from './components/HUD';

const FLAG_TAKEOFF = 0x01;
const FLAG_LAND = 0x02;
const FLAG_EMERGENCY = 0x04;
const FLAG_GYRO_CAL = 0x08;

function App() {
    const [status, setStatus] = useState('Standby');
    const controls = useRef({ roll: 128, pitch: 128, throttle: 0, yaw: 128, flags: 0 });

    useEffect(() => {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const newWs = new WebSocket(`${protocol}//${window.location.hostname}:8000/ws/control`);

        newWs.onopen = () => setStatus('Connected');
        newWs.onclose = () => setStatus('Offline');

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
        controls.current.yaw = Math.round(128 + data.x * 127);
        controls.current.throttle = Math.max(0, Math.min(255, Math.round(data.y * 255)));
    }, []);

    const handleRightMove = useCallback((data: { x: number; y: number }) => {
        controls.current.roll = Math.round(128 + data.x * 127);
        controls.current.pitch = Math.round(128 + data.y * 127);
    }, []);

    const resetLeft = useCallback(() => {
        controls.current.yaw = 128;
    }, []);

    const resetRight = useCallback(() => {
        controls.current.roll = 128;
        controls.current.pitch = 128;
    }, []);

    const sendFlag = (flag: number) => {
        controls.current.flags = flag;
    };

    // Keyboard controls (#32)
    const keysDown = useRef(new Set<string>());
    const STICK_STEP = 64;

    useEffect(() => {
        const onKeyDown = (e: KeyboardEvent) => {
            if (e.repeat) return;
            keysDown.current.add(e.key);
            applyKeyboard();

            if (e.key === ' ') {
                e.preventDefault();
                sendFlag(status === 'Flying' ? FLAG_LAND : FLAG_TAKEOFF);
            }
            if (e.key === 'Escape') {
                e.preventDefault();
                sendFlag(FLAG_EMERGENCY);
            }
        };

        const onKeyUp = (e: KeyboardEvent) => {
            keysDown.current.delete(e.key);
            applyKeyboard();
        };

        const applyKeyboard = () => {
            const keys = keysDown.current;
            let throttle = 0;
            if (keys.has('w') || keys.has('W')) throttle = 128 + STICK_STEP;
            if (keys.has('s') || keys.has('S')) throttle = Math.max(0, throttle - STICK_STEP);

            let yaw = 128;
            if (keys.has('a') || keys.has('A')) yaw -= STICK_STEP;
            if (keys.has('d') || keys.has('D')) yaw += STICK_STEP;

            let pitch = 128;
            if (keys.has('ArrowUp')) pitch += STICK_STEP;
            if (keys.has('ArrowDown')) pitch -= STICK_STEP;

            let roll = 128;
            if (keys.has('ArrowLeft')) roll -= STICK_STEP;
            if (keys.has('ArrowRight')) roll += STICK_STEP;

            controls.current.throttle = Math.max(0, Math.min(255, throttle));
            controls.current.yaw = Math.max(0, Math.min(255, yaw));
            controls.current.pitch = Math.max(0, Math.min(255, pitch));
            controls.current.roll = Math.max(0, Math.min(255, roll));
        };

        window.addEventListener('keydown', onKeyDown);
        window.addEventListener('keyup', onKeyUp);
        return () => {
            window.removeEventListener('keydown', onKeyDown);
            window.removeEventListener('keyup', onKeyUp);
        };
    }, [status]);

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

            <div className="keybinds-overlay">
                <div className="keybind"><kbd>W</kbd><kbd>S</kbd> Throttle</div>
                <div className="keybind"><kbd>A</kbd><kbd>D</kbd> Yaw</div>
                <div className="keybind"><kbd>&uarr;</kbd><kbd>&darr;</kbd> Pitch</div>
                <div className="keybind"><kbd>&larr;</kbd><kbd>&rarr;</kbd> Roll</div>
                <div className="keybind"><kbd>Space</kbd> Takeoff/Land</div>
                <div className="keybind"><kbd>Esc</kbd> Emergency</div>
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
