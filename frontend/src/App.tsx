import { useEffect, useRef, useCallback } from 'react';
import './App.css';
import VideoFeed from './components/VideoFeed';
import Joystick from './components/Joystick';
import HUD from './components/HUD';
import { useDrone } from './DroneContext';

const FLAG_TAKEOFF = 0x01;
const FLAG_LAND = 0x02;
const FLAG_EMERGENCY = 0x04;
const FLAG_GYRO_CAL = 0x08;

function App() {
    const { controlState, sendControl, telemetry } = useDrone();
    const controls = useRef({ roll: 128, pitch: 128, throttle: 0, yaw: 128, flags: 0 });

    // 20Hz heartbeat — send current controls via context
    useEffect(() => {
        const interval = setInterval(() => {
            sendControl(controls.current);
            if (controls.current.flags !== 0) {
                controls.current.flags = 0;
            }
        }, 50);
        return () => clearInterval(interval);
    }, [sendControl]);

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
                sendFlag(controlState === 'connected' ? FLAG_LAND : FLAG_TAKEOFF);
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
    }, [controlState]);

    const statusLabel =
        controlState === 'connected' ? 'Connected' :
        controlState === 'connecting' ? 'Connecting...' : 'Offline';

    return (
        <div className="app-container">
            <VideoFeed />
            <HUD battery={telemetry.battery} wifi={telemetry.wifi} status={statusLabel} altitude={telemetry.altitude} />

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
