import { useState, useEffect } from 'react';
import Header from './components/Header';
import MicButton from './components/MicButton';
import ModeCards from './components/ModeCards';
import BottomNav from './components/BottomNav';
import RoleplayScreen from './components/RoleplayScreen';
import ProfileScreen from './components/ProfileScreen';
import SettingsScreen from './components/SettingsScreen';
import PersonalInfoScreen from './components/PersonalInfoScreen';
import SignInScreen from './components/SignInScreen';
import SignUpScreen from './components/SignUpScreen';
import ForgotPasswordScreen from './components/ForgotPasswordScreen';
import ConversationContainer from './components/ConversationContainer';
import LoadingScreen from './components/LoadingScreen';
import { usePreWarmSession } from './utils/usePreWarmSession';
import { isTokenValid } from './utils/auth';
import './index.css';
import './App.css';

export type ViewState =
    | 'home'
    | 'roleplay'
    | 'profile'
    | 'settings'
    | 'personal-info'
    | 'sign-in'
    | 'sign-up'
    | 'forgot-password'
    | 'conversation'
    | 'loading'               // initial app load — pre-warming normal session
    | 'loading-conversation'; // transition to conversation — pre-warming for chosen mode

export interface SessionConfig {
    mode: 'tars_normal' | 'tars_roleplay';
    filename?: string;
    tars_role?: string;
    user_role?: string;
}

function App() {
    const [isLightMode, setIsLightMode] = useState(false);
    
    // Si no hay token guardado, iniciamos directamente en la vista de login.
    // Si lo hay, iniciamos en 'loading' para hacer el pre-warm y pasar al 'home'.
    const [currentView, setCurrentView] = useState<ViewState>(() => {
        return isTokenValid() ? 'loading' : 'sign-in';
    });
    
    const [sessionConfig, setSessionConfig] = useState<SessionConfig>({ mode: 'tars_normal' });

    // ── Pre-warm normal mode ────────────────────
    const {
        session: preWarmedSession,
        reset: resetPreWarm,
    } = usePreWarmSession({
        mode: 'tars_normal',
        enabled: currentView === 'loading' || currentView === 'home' || currentView === 'conversation',
    });
    // ── Pre-warm roleplay mode when config is chosen in RoleplayScreen ────
    const [roleplayConfig, setRoleplayConfig] = useState<SessionConfig | null>(null);
    const {
        session: preWarmedRoleplaySession,
        reset: resetRoleplayPreWarm,
    } = usePreWarmSession({
        mode: 'tars_roleplay',
        enabled: roleplayConfig !== null,
        filename: roleplayConfig?.filename,
        user_role: roleplayConfig?.user_role,
        tars_role: roleplayConfig?.tars_role,
    });

    /**
     * Called by ModeCards for Normal Mode.
     * Everything is guaranteed ready (session + preloadMessage) by the time
     * home is shown — go directly to conversation, zero loading screen.
     */
    const startConversation = (config: SessionConfig) => {
        setSessionConfig(config);
        setCurrentView('conversation'); // direct — no second loading screen
    };

    // Transition: loading → home
    // Waits for BOTH the session AND the preloadMessage so the greeting
    // is guaranteed available the instant the user clicks Normal Mode.
    // Falls back after 5 s so a slow network never blocks indefinitely.
    useEffect(() => {
        if (currentView !== 'loading') return;
        if (preWarmedSession?.preloadMessage) {
            setCurrentView('home');
            return;
        }
        // Fallback: show home even if preload message didn't arrive
        const fallback = setTimeout(() => {
            if (preWarmedSession) setCurrentView('home');
        }, 5000);
        return () => clearTimeout(fallback);
    }, [currentView, preWarmedSession]);

    // Transition: loading-conversation → conversation (roleplay only)
    useEffect(() => {
        if (currentView !== 'loading-conversation') return;
        if (preWarmedRoleplaySession) {
            setCurrentView('conversation');
        }
    }, [currentView, preWarmedRoleplaySession]);

    /**
     * Called by RoleplayScreen → lets us pre-warm the roleplay session
     * right after the user picks a scenario (before they even press Start).
     */
    const prepareRoleplaySession = (config: SessionConfig) => {
        setRoleplayConfig(config);
        setSessionConfig(config);
        setCurrentView('loading-conversation');
    };

    const handleSessionConsumed = () => {
        resetPreWarm();
        resetRoleplayPreWarm();
        setRoleplayConfig(null);
    };

    useEffect(() => {
        if (isLightMode) {
            document.documentElement.setAttribute('data-theme', 'light');
        } else {
            document.documentElement.removeAttribute('data-theme');
        }
    }, [isLightMode]);

    const toggleTheme = () => setIsLightMode(!isLightMode);

    const activePreWarmedSession =
        currentView === 'conversation'
            ? sessionConfig.mode === 'tars_normal'
                ? preWarmedSession
                : preWarmedRoleplaySession
            : null;

    return (
        <div className="mobile-container">
            {/* Boot loading screen — only shown once at startup */}
            {currentView === 'loading' && (
                <LoadingScreen
                    personalised={true}
                    fallbackMessage="Waking up TARS..."
                />
            )}

            {/* Roleplay preparation loading screen */}
            {currentView === 'loading-conversation' && (
                <LoadingScreen
                    personalised={false}
                    fallbackMessage="Preparing roleplay..."
                />
            )}

            {currentView === 'home' && (
                <>
                    <Header isLightMode={isLightMode} toggleTheme={toggleTheme} />
                    <MicButton setCurrentView={setCurrentView} />
                    <ModeCards
                        setCurrentView={setCurrentView}
                        startConversation={startConversation}
                    />
                </>
            )}

            {currentView === 'roleplay' && (
                <RoleplayScreen
                    setCurrentView={setCurrentView}
                    startConversation={prepareRoleplaySession}
                />
            )}

            {currentView === 'conversation' && (
                <ConversationContainer
                    setCurrentView={setCurrentView}
                    sessionConfig={sessionConfig}
                    preWarmedSession={activePreWarmedSession}
                    onSessionConsumed={handleSessionConsumed}
                />
            )}

            {currentView === 'profile' && (
                <ProfileScreen setCurrentView={setCurrentView} />
            )}

            {currentView === 'settings' && (
                <SettingsScreen
                    setCurrentView={setCurrentView}
                    isLightMode={isLightMode}
                    toggleTheme={toggleTheme}
                />
            )}

            {currentView === 'personal-info' && (
                <PersonalInfoScreen setCurrentView={setCurrentView} />
            )}

            {currentView === 'sign-in' && (
                <SignInScreen setCurrentView={setCurrentView} isLightMode={isLightMode} />
            )}

            {currentView === 'sign-up' && (
                <SignUpScreen setCurrentView={setCurrentView} isLightMode={isLightMode} />
            )}

            {currentView === 'forgot-password' && (
                <ForgotPasswordScreen setCurrentView={setCurrentView} />
            )}

            {currentView !== 'sign-in' &&
                currentView !== 'sign-up' &&
                currentView !== 'forgot-password' &&
                currentView !== 'settings' &&
                currentView !== 'personal-info' &&
                currentView !== 'conversation' &&
                currentView !== 'loading' &&
                currentView !== 'loading-conversation' && (
                    <BottomNav currentView={currentView} setCurrentView={setCurrentView} />
                )}
        </div>
    );
}

export default App;
