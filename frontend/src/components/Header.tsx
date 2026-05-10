import { useState, useEffect } from 'react';
import { Flame, Smartphone, Sun, Moon } from 'lucide-react';
import './Header.css';

interface HeaderProps {
    isLightMode: boolean;
    toggleTheme: () => void;
}

export default function Header({ isLightMode, toggleTheme }: HeaderProps) {
    const [userName, setUserName] = useState('User');

    useEffect(() => {
        const firstName = localStorage.getItem('tars_first_name');
        const username = localStorage.getItem('tars_username');
        if (firstName && firstName !== 'null') {
            setUserName(firstName);
        } else if (username) {
            setUserName(username);
        }
    }, []);

    return (
        <header className="app-header">
            <div className="profile-section">
                <div className="avatar-circle">
                    <Smartphone size={18} color="#ffffff" strokeWidth={2.5} />
                </div>
                <div className="profile-info">
                    <h2 className="profile-name">{userName}</h2>
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
