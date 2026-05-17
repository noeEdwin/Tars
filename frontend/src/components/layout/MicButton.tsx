import { useRef, useState } from 'react';
import { Mic } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import './MicButton.css';
import { useSessionStore } from '../../stores/sessionStore';

const HOLD_DURATION = 3000;

export default function MicButton() {
    const { t } = useTranslation();
    const setView = useSessionStore((s) => s.setView);
    const [progress, setProgress] = useState(0);
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
                setView('conversation');
            }
        }, 30);
    };

    const cancelHold = () => {
        if (intervalRef.current) clearInterval(intervalRef.current);
        setHolding(false);
        setProgress(0);
    };

    const R = 108;
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
                    {holding ? t('micButton.holdToActivate') : t('micButton.holdToSpeak')}
                </h1>
                <p className="mic-subtitle">
                    {holding ? t('micButton.releaseToCancel') : t('micButton.normalMode3sec')}
                </p>
            </div>
        </div>
    );
}
