declare module 'nipplejs' {
    export interface NippleData {
        position: { x: number, y: number };
        force: number;
        distance: number;
        angle: {
            radian: number;
            degree: number;
        };
        direction?: {
            x: 'left' | 'right';
            y: 'up' | 'down';
            angle: string;
        };
        vector: { x: number, y: number };
        instance: any;
    }

    export interface NippleOptions {
        zone?: HTMLElement;
        color?: string;
        size?: number;
        threshold?: number;
        fadeTime?: number;
        multitouch?: boolean;
        maxNumberOfNipples?: number;
        dataOnly?: boolean;
        position?: { top?: string, left?: string, right?: string, bottom?: string };
        mode?: 'static' | 'semi' | 'dynamic';
        restJoystick?: boolean;
        restOpacity?: number;
        catchDistance?: number;
    }

    export interface JoystickManager {
        on(event: string, callback: (evt: any, data: NippleData) => void): void;
        destroy(): void;
    }

    export function create(options: NippleOptions): JoystickManager;
}
