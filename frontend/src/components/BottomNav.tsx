import { Home, Layers, User } from 'lucide-react';
import './BottomNav.css';
import type { ViewState } from '../App';

interface BottomNavProps {
    currentView: ViewState;
    setCurrentView: (view: ViewState) => void;
}

export default function BottomNav({ currentView, setCurrentView }: BottomNavProps) {
    return (
        <div className="bottom-nav-container">

            {/* Navigation Bar */}
            <div className="nav-bar">

                {/* Home */}
                <div
                    className={`nav-item ${currentView === 'home' ? 'active' : ''}`}
                    onClick={() => setCurrentView('home')}
                >
                    <Home
                        size={24}
                        color={currentView === 'home' ? "#f10034" : "#666666"}
                        fill={currentView === 'home' ? "#f10034" : "none"}
                    />
                    <span className={`nav-label ${currentView === 'home' ? 'nav-label-active' : ''}`}>Home</span>
                </div>

                {/* Roleplay – with dot indicator */}
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
                    <span className={`nav-label ${currentView === 'roleplay' ? 'nav-label-active' : ''}`}>Roleplay</span>
                </div>

                {/* Profile */}
                <div
                    className={`nav-item ${currentView === 'profile' ? 'active' : ''}`}
                    onClick={() => setCurrentView('profile')}
                >
                    <User
                        size={24}
                        color={currentView === 'profile' ? "#f10034" : "#666666"}
                        fill={currentView === 'profile' ? "#f10034" : "#666666"}
                    />
                    <span className={`nav-label ${currentView === 'profile' ? 'nav-label-active' : ''}`}>Profile</span>
                </div>

            </div>

        </div>
    );
}
