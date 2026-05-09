import { Home, Layers, User } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import './BottomNav.css';
import type { ViewState } from '../App';

interface BottomNavProps {
    currentView: ViewState;
    setCurrentView: (view: ViewState) => void;
}

export default function BottomNav({ currentView, setCurrentView }: BottomNavProps) {
    const { t } = useTranslation();

    return (
        <div className="bottom-nav-container">
            <div className="nav-bar">
                <div
                    className={`nav-item ${currentView === 'home' ? 'active' : ''}`}
                    onClick={() => setCurrentView('home')}
                >
                    <Home
                        size={24}
                        color={currentView === 'home' ? "#f10034" : "#666666"}
                        fill={currentView === 'home' ? "#f10034" : "none"}
                    />
                    <span className={`nav-label ${currentView === 'home' ? 'nav-label-active' : ''}`}>{t('bottomNav.home')}</span>
                </div>

                <div
                    className={`nav-item ${currentView === 'roleplay' ? 'active' : ''}`}
                    onClick={() => setCurrentView('roleplay')}
                >
                    <div className="nav-icon-relative">
                        <Layers
                            size={24}
                            color={currentView === 'roleplay' ? "#f10034" : "#666666"}
                            fill={currentView === 'roleplay' ? "#f10034" : "none"}
                        />
                        <span className="nav-dot" />
                    </div>
                    <span className={`nav-label ${currentView === 'roleplay' ? 'nav-label-active' : ''}`}>{t('bottomNav.roleplay')}</span>
                </div>

                <div
                    className={`nav-item ${currentView === 'profile' ? 'active' : ''}`}
                    onClick={() => setCurrentView('profile')}
                >
                    <User
                        size={24}
                        color={currentView === 'profile' ? "#f10034" : "#666666"}
                        fill={currentView === 'profile' ? "#f10034" : "#666666"}
                    />
                    <span className={`nav-label ${currentView === 'profile' ? 'nav-label-active' : ''}`}>{t('bottomNav.profile')}</span>
                </div>
            </div>
        </div>
    );
}
