import { ArrowLeft, User, Mail, Lock, Eye, ArrowRight } from 'lucide-react';
import { Trans, useTranslation } from 'react-i18next';
import './SignUpScreen.css';
import type { ViewState } from '../App';
import darkLogo from '../assets/dark_mode.png';
import lightLogo from '../assets/light_mode.png';

interface SignUpScreenProps {
    setCurrentView: (view: ViewState) => void;
    isLightMode: boolean;
}

export default function SignUpScreen({ setCurrentView, isLightMode }: SignUpScreenProps) {
    const { t } = useTranslation();

    return (
        <div className="signup-container">
            <div className="signup-decor top-right" />
            <div className="signup-decor bottom-left" />

            <div className="signup-header">
                <button className="signup-back-btn" onClick={() => setCurrentView('sign-in')}>
                    <ArrowLeft size={24} color="var(--text-main)" />
                </button>
                <div className="signup-brand">
                    <img
                        src={isLightMode ? lightLogo : darkLogo}
                        alt="Tài Sī Logo"
                        className="signup-logo-img"
                    />
                </div>
                <div style={{ width: 40 }} />
            </div>

            <main className="signup-main">
                <div className="signup-heading">
                    <h1 className="signup-title">
                        <Trans i18nKey="signUp.joinAcademy" components={{ accent: <span className="signup-title-accent" /> }} />
                    </h1>
                    <p className="signup-subtitle">{t('signUp.subtitle')}</p>
                </div>

                <div className="signup-form">
                    <div className="signup-field">
                        <label className="signup-label">{t('signUp.fullName')}</label>
                        <div className="signup-input-wrapper">
                            <User size={20} className="signup-input-icon" />
                            <input
                                type="text"
                                className="signup-input"
                                placeholder={t('signUp.placeholderName')}
                            />
                        </div>
                    </div>

                    <div className="signup-field">
                        <label className="signup-label">{t('signUp.email')}</label>
                        <div className="signup-input-wrapper">
                            <Mail size={20} className="signup-input-icon" />
                            <input
                                type="email"
                                className="signup-input"
                                placeholder="focus@taisi.academy"
                            />
                        </div>
                    </div>

                    <div className="signup-field">
                        <label className="signup-label">{t('signUp.password')}</label>
                        <div className="signup-input-wrapper">
                            <Lock size={20} className="signup-input-icon" />
                            <input
                                type="password"
                                className="signup-input"
                                placeholder="••••••••"
                            />
                            <button type="button" className="signup-eye-btn">
                                <Eye size={20} />
                            </button>
                        </div>
                    </div>
                </div>

                <div className="signup-btn-wrapper">
                    <button
                        className="signup-btn"
                        onClick={() => setCurrentView('home')}
                    >
                        {t('signUp.createAccount')}
                        <ArrowRight size={20} />
                    </button>
                </div>

                <div className="signup-footer">
                    <div className="signup-divider">
                        <div className="signup-divider-line" />
                        <span className="signup-divider-text">{t('signUp.masteryAwaits')}</span>
                        <div className="signup-divider-line" />
                    </div>
                    <p className="signup-signin-text">
                        {t('signUp.hasAccount')}{' '}
                        <button
                            className="signup-signin-link"
                            onClick={() => setCurrentView('sign-in')}
                        >
                            {t('signUp.signIn')}
                        </button>
                    </p>
                </div>
            </main>
        </div>
    );
}
