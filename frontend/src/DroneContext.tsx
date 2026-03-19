import { createContext, useContext, useEffect, useRef, useState } from 'react';
import type { ReactNode } from 'react';

type ConnectionState = 'disconnected' | 'connecting' | 'connected';

interface DroneContextValue {
    controlState: ConnectionState;
    videoState: ConnectionState;
    sendControl: (data: Record<string, number>) => void;
    onVideoFrame: (handler: (data: Blob) => void) => () => void;
}

const DroneContext = createContext<DroneContextValue | null>(null);

const MAX_BACKOFF = 8000;

function createReconnectingWs(
    url: string,
    onOpen: () => void,
    onClose: () => void,
    onMessage: (e: MessageEvent) => void,
    binaryType?: BinaryType,
): { getWs: () => WebSocket | null; cleanup: () => void } {
    let ws: WebSocket | null = null;
    let attempt = 0;
    let timer: ReturnType<typeof setTimeout> | null = null;
    let stopped = false;

    function connect() {
        if (stopped) return;
        ws = new WebSocket(url);
        if (binaryType) ws.binaryType = binaryType;

        ws.onopen = () => {
            attempt = 0;
            onOpen();
        };
        ws.onclose = () => {
            ws = null;
            onClose();
            if (!stopped) {
                const delay = Math.min(1000 * 2 ** attempt, MAX_BACKOFF);
                attempt++;
                timer = setTimeout(connect, delay);
            }
        };
        ws.onmessage = onMessage;
    }

    connect();

    return {
        getWs: () => ws,
        cleanup: () => {
            stopped = true;
            if (timer) clearTimeout(timer);
            if (ws) ws.close();
        },
    };
}

export function DroneProvider({ children }: { children: ReactNode }) {
    const [controlState, setControlState] = useState<ConnectionState>('disconnected');
    const [videoState, setVideoState] = useState<ConnectionState>('disconnected');
    const controlWsRef = useRef<{ getWs: () => WebSocket | null; cleanup: () => void } | null>(null);
    const videoHandlerRef = useRef<((data: Blob) => void) | null>(null);

    useEffect(() => {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const base = `${protocol}//${window.location.hostname}:8000`;

        setControlState('connecting');
        controlWsRef.current = createReconnectingWs(
            `${base}/ws/control`,
            () => setControlState('connected'),
            () => setControlState('disconnected'),
            () => {},
        );

        setVideoState('connecting');
        const videoConn = createReconnectingWs(
            `${base}/ws/video`,
            () => setVideoState('connected'),
            () => setVideoState('disconnected'),
            (e) => {
                if (e.data instanceof Blob && videoHandlerRef.current) {
                    videoHandlerRef.current(e.data);
                }
            },
            'blob',
        );

        return () => {
            controlWsRef.current?.cleanup();
            videoConn.cleanup();
        };
    }, []);

    const sendControl = (data: Record<string, number>) => {
        const ws = controlWsRef.current?.getWs();
        if (ws && ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify(data));
        }
    };

    const onVideoFrame = (handler: (data: Blob) => void) => {
        videoHandlerRef.current = handler;
        return () => {
            videoHandlerRef.current = null;
        };
    };

    return (
        <DroneContext.Provider value={{ controlState, videoState, sendControl, onVideoFrame }}>
            {children}
        </DroneContext.Provider>
    );
}

export function useDrone() {
    const ctx = useContext(DroneContext);
    if (!ctx) throw new Error('useDrone must be used within DroneProvider');
    return ctx;
}
