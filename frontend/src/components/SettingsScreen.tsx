import { ArrowLeft, User, Award, Languages, Volume2, Moon, Sun, LogOut, ChevronRight, ChevronDown } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import './SettingsScreen.css';
import type { ViewState } from '../App';

interface SettingsScreenProps {
    setCurrentView: (view: ViewState) => void;
    isLightMode: boolean;
    toggleTheme: () => void;
}

export default function SettingsScreen({ setCurrentView, isLightMode, toggleTheme }: SettingsScreenProps) {
    const { t } = useTranslation();

    return (
        <div className="settings-container">
            <header className="settings-header">
                <button className="icon-btn-glass" onClick={() => setCurrentView('profile')}>
                    <ArrowLeft size={24} color="var(--text-main)" />
                </button>
                <h1 className="settings-title">{t('settings.title')}</h1>
                <div style={{ width: 40 }} />
            </header>

            <div className="settings-main">
                <section className="settings-section">
                    <h3 className="settings-section-label">{t('settings.account')}</h3>
                    <div className="settings-group">
                        <div className="settings-row border-bottom" onClick={() => setCurrentView('personal-info')}>
                            <div className="settings-icon-box icon-primary">
                                <User size={20} />
                            </div>
                            <div className="settings-row-content">
                                <p className="settings-row-title">{t('settings.profile')}</p>
                                <p className="settings-row-sub">{t('settings.profileSub')}</p>
                            </div>
                            <ChevronRight size={20} color="var(--text-muted)" />
                        </div>
                        <div className="settings-row">
                            <div className="settings-icon-box icon-primary">
                                <Award size={20} />
                            </div>
                            <div className="settings-row-content">
                                <p className="settings-row-title">{t('settings.subscription')}</p>
                                <p className="settings-row-sub">{t('settings.proActive')}</p>
                            </div>
                            <ChevronRight size={20} color="var(--text-muted)" />
                        </div>
                    </div>
                </section>

                <section className="settings-section">
                    <h3 className="settings-section-label">{t('settings.preferences')}</h3>
                    <div className="settings-group">
                        <div className="settings-row border-bottom">
                            <div className="settings-icon-box icon-muted">
                                <Languages size={20} />
                            </div>
                            <div className="settings-row-content">
                                <p className="settings-row-title">{t('settings.targetLanguage')}</p>
                                <p className="settings-row-sub">{t('settings.mandarin')}</p>
                            </div>
                            <ChevronDown size={20} color="var(--text-muted)" />
                        </div>
                        <div className="settings-row">
                            <div className="settings-icon-box icon-muted">
                                <Volume2 size={20} />
                            </div>
                            <div className="settings-row-content">
                                <p className="settings-row-title">{t('settings.voiceSpeed')}</p>
                                <div className="voice-speed-row">
                                    <div className="voice-speed-track">
                                        <div className="voice-speed-fill" />
                                    </div>
                                    <span className="voice-speed-label">{t('settings.normal')}</span>
                                </div>
                            </div>
                        </div>
                    </div>
                </section>

                <section className="settings-section">
                    <h3 className="settings-section-label">{t('settings.display')}</h3>
                    <div className="settings-group">
                        <div className="settings-row" onClick={toggleTheme} style={{ cursor: 'pointer' }}>
                            <div className="settings-icon-box icon-muted">
                                {isLightMode ? <Sun size={20} /> : <Moon size={20} />}
                            </div>
                            <div className="settings-row-content">
                                <p className="settings-row-title">
                                    {isLightMode ? t('settings.lightMode') : t('settings.darkMode')}
                                </p>
                            </div>
                            <div
                                className={`toggle-switch ${isLightMode ? 'toggle-off' : 'toggle-on'}`}
                            >
                                <span className={`toggle-thumb ${isLightMode ? 'thumb-off' : 'thumb-on'}`} />
                            </div>
                        </div>
                    </div>
                </section>

                <div className="settings-footer">
                    <button className="logout-btn" onClick={() => setCurrentView('sign-in')}>
                        <LogOut size={20} />
                        {t('settings.logOut')}
                    </button>
                    <p className="settings-version">{t('settings.version')}</p>
                </div>
            </div>

            <div className="settings-decor top-right" />
            <div className="settings-decor bottom-left" />
        </div>
    );
}
