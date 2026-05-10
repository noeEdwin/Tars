import { useEffect, useState } from 'react';
import Lottie from 'lottie-react';
import { useTranslation } from 'react-i18next';
import sleepAnimation from '../assets/animations/sleep.json';
import { API_BASE } from '../apiConfig';
import './LoadingScreen.css';

interface LoadingScreenProps {
    fallbackMessage?: string;
    personalised?: boolean;
}

export default function LoadingScreen({
    personalised = false,
}: LoadingScreenProps) {
    const { t } = useTranslation();
    const [greeting, setGreeting] = useState<string | null>(null);
    const [toastVisible, setToastVisible] = useState(false);
    const [toastDismissed, setToastDismissed] = useState(false);

    useEffect(() => {
        if (!personalised) return;

        const token = localStorage.getItem('tars_token');
        if (!token) return;

        let cancelled = false;
        fetch(`${API_BASE}/greeting`, {
            headers: { 'Authorization': `Bearer ${token}` },
        })
            .then(r => r.json())
            .then(data => {
                if (!cancelled && data.greeting) {
                    setGreeting(data.greeting);
                    setToastVisible(true);
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

            {greeting && !toastDismissed && (
                <div className={`loading-toast ${toastVisible ? 'toast-visible' : 'toast-hiding'}`}>
                    <div className="toast-avatar">T</div>
                    <div className="toast-body">
                        <span className="toast-name">{t('loadingScreen.toastName')}</span>
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
                    <h2 className="loading-title">{t('loadingScreen.tars')}</h2>
                    <p className="loading-message">{t('loadingScreen.wakingUp')}</p>
                    <div className="loading-dots">
                        <span /><span /><span />
                    </div>
                </div>
            </div>
        </div>
    );
}
