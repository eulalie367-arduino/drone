import React from 'react';

interface HUDProps {
    battery: number;
    wifi: number;
    status: string;
    altitude: number;
}

const HUD: React.FC<HUDProps> = ({ battery, wifi, status, altitude }) => {
    return (
        <div className="hud-overlay">
            {/* Top Bar */}
            <div className="hud-top">
                <div className="hud-item battery">
                    <span className="label">BAT:</span>
                    <div className="bar-container">
                        <div className="bar" style={{ width: `${battery}%`, background: battery < 20 ? '#ff0055' : '#00f2ff' }}></div>
                    </div>
                    <span className="value">{battery}%</span>
                </div>
                
                <div className="hud-item status">
                    <span className="status-text">{status.toUpperCase()}</span>
                </div>

                <div className="hud-item wifi">
                    <span className="label">LINK:</span>
                    <span className="value">{wifi}%</span>
                </div>
            </div>

            {/* Center Crosshair */}
            <div className="hud-center">
                <div className="crosshair"></div>
                <div className="horizon"></div>
            </div>

            {/* Side Gauges */}
            <div className="hud-side left">
                <div className="altitude-gauge">
                    <span className="label">ALT</span>
                    <span className="value">{altitude.toFixed(1)}m</span>
                </div>
            </div>

            {/* Bottom Scanlines overlay is handled in CSS */}
            <div className="scanlines"></div>
        </div>
    );
};

export default HUD;
