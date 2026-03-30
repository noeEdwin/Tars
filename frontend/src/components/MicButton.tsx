import { useRef, useState } from 'react';
import { Mic } from 'lucide-react';
import './MicButton.css';
import type { ViewState } from '../App';

const HOLD_DURATION = 3000; // 3 seconds

interface MicButtonProps {
    setCurrentView: (view: ViewState) => void;
}

export default function MicButton({ setCurrentView }: MicButtonProps) {
    const [progress, setProgress] = useState(0); // 0–100
    const [holding, setHolding] = useState(false);
    const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
    const startRef = useRef<number>(0);

    const startHold = () => {
        setHolding(true);
        setProgress(0);
        startRef.current = Date.now();

        intervalRef.current = setInterval(() => {
            const elapsed = Date.now() - startRef.current;
            const pct = Math.min((elapsed / HOLD_DURATION) * 100, 100);
            setProgress(pct);
            if (pct >= 100) {
                clearInterval(intervalRef.current!);
                setHolding(false);
                setProgress(0);
                setCurrentView('conversation');
            }
        }, 30);
    };

    const cancelHold = () => {
        if (intervalRef.current) clearInterval(intervalRef.current);
        setHolding(false);
        setProgress(0);
    };

    // SVG ring params
    const R = 108;           // radius (half of 220px - 2px padding)
    const circumference = 2 * Math.PI * R;
    const dashoffset = circumference * (1 - progress / 100);

    return (
        <div className="mic-container">
            <div
                className={`mic-ring${holding ? ' mic-ring-holding' : ''}`}
                onPointerDown={startHold}
                onPointerUp={cancelHold}
                onPointerLeave={cancelHold}
            >
                {/* SVG progress ring overlay */}
                {holding && (
                    <svg className="mic-progress-ring" viewBox="0 0 220 220">
                        <circle
                            cx="110" cy="110" r={R}
                            fill="none"
                            stroke="#f10034"
                            strokeWidth="4"
                            strokeLinecap="round"
                            strokeDasharray={circumference}
                            strokeDashoffset={dashoffset}
                            transform="rotate(-90 110 110)"
                        />
                    </svg>
                )}

                <div className="mic-inner">
                    <div className="mic-icon-wrapper">
                        <Mic size={48} color="#ffffff" strokeWidth={2} className="mic-icon-svg" />
                    </div>
                    <div className="audio-bars">
                        <span className="bar bar-1"></span>
                        <span className="bar bar-2"></span>
                        <span className="bar bar-3"></span>
                        <span className="bar bar-4"></span>
                    </div>
                </div>
            </div>

            <div className="mic-text-container">
                <h1 className="mic-title">
                    {holding ? 'HOLD TO ACTIVATE…' : 'HOLD TO SPEAK'}
                </h1>
                <p className="mic-subtitle">
                    {holding ? 'RELEASE TO CANCEL' : 'NORMAL MODE · 3 SECONDS'}
                </p>
            </div>
        </div>
    );
}
