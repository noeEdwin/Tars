import { Flame, Smartphone, Sun, Moon } from 'lucide-react';
import './Header.css';
import { useAuthStore } from '../stores/authStore';
import { useSessionStore } from '../stores/sessionStore';

export default function Header() {
    const firstName = useAuthStore((s) => s.firstName);
    const username = useAuthStore((s) => s.username);
    const isLightMode = useSessionStore((s) => s.isLightMode);
    const toggleTheme = useSessionStore((s) => s.toggleTheme);

    const displayName = (firstName && firstName !== 'null') ? firstName : (username || 'User');

    return (
        <header className="app-header">
            <div className="profile-section">
                <div className="avatar-circle">
                    <Smartphone size={18} color="#ffffff" strokeWidth={2.5} />
                </div>
                <div className="profile-info">
                    <h2 className="profile-name">{displayName}</h2>
                    <p className="profile-level">LEVEL 24 • ADVANCED</p>
                </div>
            </div>

            <div className="header-actions">
                <button className="theme-toggle" onClick={toggleTheme}>
                    {isLightMode ? (
                        <Moon size={20} color="#fbbf24" strokeWidth={2} />
                    ) : (
                        <Sun size={20} color="#fbbf24" strokeWidth={2} />
                    )}
                </button>
                <div className="streak-pill">
                    <Flame size={16} fill="#fbbf24" color="#fbbf24" />
                    <span className="streak-text">12 DAYS</span>
                </div>
            </div>
        </header>
    );
}
