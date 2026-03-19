import { useEffect, useRef } from 'react';
import nipplejs, { type NippleData } from 'nipplejs';

interface JoystickProps {
    side: 'left' | 'right';
    onMove: (data: { x: number; y: number }) => void;
    onEnd: () => void;
}

const Joystick: React.FC<JoystickProps> = ({ side, onMove, onEnd }) => {
    const containerRef = useRef<HTMLDivElement>(null);
    const managerRef = useRef<any>(null);

    useEffect(() => {
        if (containerRef.current) {
            managerRef.current = nipplejs.create({
                zone: containerRef.current,
                mode: 'static',
                position: { left: '50%', top: '50%' },
                color: '#00f2ff',
                size: 120,
            });

            managerRef.current.on('move', (_: any, data: NippleData) => {
                // Normalize vector to -1 to 1 range (nipplejs vector is -1 to 1)
                onMove({ x: data.vector.x, y: data.vector.y });
            });

            managerRef.current.on('end', () => {
                onEnd();
            });
        }

        return () => {
            if (managerRef.current) {
                managerRef.current.destroy();
            }
        };
    }, [onMove, onEnd]);

    return (
        <div className={`joystick-wrapper ${side}`} ref={containerRef}>
            <div className="joystick-label">
                {side === 'left' ? 'THROTTLE / YAW' : 'PITCH / ROLL'}
            </div>
        </div>
    );
};

export default Joystick;
