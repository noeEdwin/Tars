import { ArrowLeft, Mail, Send } from 'lucide-react';
import { Trans, useTranslation } from 'react-i18next';
import './ForgotPasswordScreen.css';
import { useSessionStore } from '../stores/sessionStore';

export default function ForgotPasswordScreen() {
    const { t } = useTranslation();
    const setView = useSessionStore((s) => s.setView);

    return (
        <div className="fp-container">
            <div className="fp-grid-bg" />
            <div className="fp-decor top-right" />
            <div className="fp-decor bottom-left" />

            <div className="fp-inner">
                <div className="fp-back-row">
                    <button className="fp-back-btn" onClick={() => setView('sign-in')}>
                        <ArrowLeft size={22} />
                    </button>
                </div>

                <div className="fp-card">
                    <div className="fp-card-header">
                        <h1 className="fp-title">
                            <Trans i18nKey="forgotPassword.title" components={{ accent: <span className="fp-title-accent" /> }} />
                        </h1>
                        <p className="fp-subtitle">
                            {t('forgotPassword.subtitle')}
                        </p>
                    </div>

                    <div className="fp-form">
                        <div className="fp-field">
                            <label className="fp-label">{t('forgotPassword.email')}</label>
                            <div className="fp-input-wrapper">
                                <Mail size={20} className="fp-input-icon" />
                                <input
                                    type="email"
                                    className="fp-input"
                                    placeholder="e.g. name@email.com"
                                />
                            </div>
                        </div>

                        <button className="fp-submit-btn">
                            <span>{t('forgotPassword.sendLink')}</span>
                            <Send size={20} />
                        </button>
                    </div>

                    <div className="fp-footer">
                        <p className="fp-footer-text">
                            {t('forgotPassword.rememberPassword')}{' '}
                            <button
                                className="fp-login-link"
                                onClick={() => setView('sign-in')}
                            >
                                {t('forgotPassword.logIn')}
                            </button>
                        </p>
                    </div>
                </div>
            </div>
        </div>
    );
}
