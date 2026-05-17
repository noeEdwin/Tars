import { ArrowLeft, User, Award, Languages, Volume2, Moon, Sun, LogOut, ChevronRight, ChevronDown } from 'lucide-react';
import './SettingsScreen.css';
import { useAuthStore } from '../../stores/authStore';
import { useSessionStore } from '../../stores/sessionStore';

export default function SettingsScreen() {
    const logout = useAuthStore((s) => s.logout);
    const setView = useSessionStore((s) => s.setView);
    const isLightMode = useSessionStore((s) => s.isLightMode);
    const toggleTheme = useSessionStore((s) => s.toggleTheme);

    return (
        <div className="settings-container">
            <header className="settings-header">
                <button className="icon-btn-glass" onClick={() => setView('profile')}>
                    <ArrowLeft size={24} color="var(--text-main)" />
                </button>
                <h1 className="settings-title">Settings</h1>
                <div style={{ width: 40 }} />
            </header>

            <div className="settings-main">

                <section className="settings-section">
                    <h3 className="settings-section-label">Account</h3>
                    <div className="settings-group">
                        <div className="settings-row border-bottom" onClick={() => setView('personal-info')}>
                            <div className="settings-icon-box icon-primary">
                                <User size={20} />
                            </div>
                            <div className="settings-row-content">
                                <p className="settings-row-title">Profile</p>
                                <p className="settings-row-sub">Personal information &amp; goals</p>
                            </div>
                            <ChevronRight size={20} color="var(--text-muted)" />
                        </div>
                        <div className="settings-row">
                            <div className="settings-icon-box icon-primary">
                                <Award size={20} />
                            </div>
                            <div className="settings-row-content">
                                <p className="settings-row-title">Subscription</p>
                                <p className="settings-row-sub">Tài Sī Pro • Active</p>
                            </div>
                            <ChevronRight size={20} color="var(--text-muted)" />
                        </div>
                    </div>
                </section>

                <section className="settings-section">
                    <h3 className="settings-section-label">Preferences</h3>
                    <div className="settings-group">
                        <div className="settings-row border-bottom">
                            <div className="settings-icon-box icon-muted">
                                <Languages size={20} />
                            </div>
                            <div className="settings-row-content">
                                <p className="settings-row-title">Target Language</p>
                                <p className="settings-row-sub">Mandarin (Simplified)</p>
                            </div>
                            <ChevronDown size={20} color="var(--text-muted)" />
                        </div>
                        <div className="settings-row">
                            <div className="settings-icon-box icon-muted">
                                <Volume2 size={20} />
                            </div>
                            <div className="settings-row-content">
                                <p className="settings-row-title">Voice Speed</p>
                                <div className="voice-speed-row">
                                    <div className="voice-speed-track">
                                        <div className="voice-speed-fill" />
                                    </div>
                                    <span className="voice-speed-label">Normal</span>
                                </div>
                            </div>
                        </div>
                    </div>
                </section>

                <section className="settings-section">
                    <h3 className="settings-section-label">Display</h3>
                    <div className="settings-group">
                        <div className="settings-row" onClick={toggleTheme} style={{ cursor: 'pointer' }}>
                            <div className="settings-icon-box icon-muted">
                                {isLightMode ? <Sun size={20} /> : <Moon size={20} />}
                            </div>
                            <div className="settings-row-content">
                                <p className="settings-row-title">
                                    {isLightMode ? 'Light Mode' : 'Dark Mode'}
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
                    <button className="logout-btn" onClick={() => {
                        logout();
                        setView('sign-in');
                    }}>
                        <LogOut size={20} />
                        Log Out
                    </button>
                    <p className="settings-version">Tài Sī v2.4.0 • Built for focus</p>
                </div>

            </div>

            <div className="settings-decor top-right" />
            <div className="settings-decor bottom-left" />
        </div>
    );
}
