import { useEffect, useState } from 'react';
import Lottie from 'lottie-react';
import sleepAnimation from '../assets/animations/sleep.json';
import { API_BASE } from '../apiConfig';
import './LoadingScreen.css';

const USER_ID = 1;

interface LoadingScreenProps {
    fallbackMessage?: string;
    /** When true, fire /greeting and show it as a toast pop-up */
    personalised?: boolean;
}

export default function LoadingScreen({
    fallbackMessage = 'Waking up TARS...',
    personalised = false,
}: LoadingScreenProps) {
    const [greeting, setGreeting] = useState<string | null>(null);
    const [toastVisible, setToastVisible] = useState(false);
    const [toastDismissed, setToastDismissed] = useState(false);

    useEffect(() => {
        if (!personalised) return;

        let cancelled = false;
        fetch(`${API_BASE}/greeting?user_id=${USER_ID}`)
            .then(r => r.json())
            .then(data => {
                if (!cancelled && data.greeting) {
                    setGreeting(data.greeting);
                    setToastVisible(true);
                    // Auto-dismiss after 5 s
                    setTimeout(() => {
                        if (!cancelled) setToastVisible(false);
                    }, 5000);
                }
            })
            .catch(() => { /* silently fall back */ });

        return () => { cancelled = true; };
    }, [personalised]);

    const handleDismissToast = () => {
        setToastVisible(false);
        setToastDismissed(true);
    };

    return (
        <div className="loading-screen">
            <div className="loading-bg-glow" />

            {/* ── Toast notification ── */}
            {greeting && !toastDismissed && (
                <div className={`loading-toast ${toastVisible ? 'toast-visible' : 'toast-hiding'}`}>
                    <div className="toast-avatar">T</div>
                    <div className="toast-body">
                        <span className="toast-name">TARS</span>
                        <p className="toast-text">{greeting}</p>
                    </div>
                    <button className="toast-close" onClick={handleDismissToast}>✕</button>
                </div>
            )}

            <div className="loading-content">
                <div className="loading-lottie-wrapper">
                    <Lottie
                        animationData={sleepAnimation}
                        loop={true}
                        autoplay={true}
                        className="loading-lottie"
                    />
                </div>

                <div className="loading-text-area">
                    <h2 className="loading-title">TARS</h2>
                    <p className="loading-message">{fallbackMessage}</p>
                    <div className="loading-dots">
                        <span /><span /><span />
                    </div>
                </div>
            </div>
        </div>
    );
}
