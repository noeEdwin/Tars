import { useEffect } from 'react';
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
import { useAuthStore } from './stores/authStore';
import { useSessionStore } from './stores/sessionStore';
import './index.css';
import './App.css';

function App() {
    const checkAuth = useAuthStore((s) => s.checkAuth);
    const logout = useAuthStore((s) => s.logout);

    const currentView = useSessionStore((s) => s.currentView);
    const setView = useSessionStore((s) => s.setView);
    const sessionConfig = useSessionStore((s) => s.sessionConfig);
    const roleplayConfig = useSessionStore((s) => s.roleplayConfig);
    const isLightMode = useSessionStore((s) => s.isLightMode);
    const consumeSession = useSessionStore((s) => s.consumeSession);

    // On mount: check if token is valid, set initial view
    useEffect(() => {
        if (!checkAuth()) {
            setView('sign-in');
        }
    }, []);

    // Apply theme
    useEffect(() => {
        if (isLightMode) {
            document.documentElement.setAttribute('data-theme', 'light');
        } else {
            document.documentElement.removeAttribute('data-theme');
        }
    }, [isLightMode]);

    // ── Pre-warm normal mode ────────────────────
    const {
        session: preWarmedSession,
        preloadMessage: normalPreloadMessage,
        reset: resetPreWarm,
    } = usePreWarmSession({
        mode: 'tars_normal',
        enabled: currentView === 'loading' || currentView === 'home' || currentView === 'conversation',
    });

    // ── Pre-warm roleplay mode ──────────────────
    const {
        session: preWarmedRoleplaySession,
        preloadMessage: roleplayPreloadMessage,
        reset: resetRoleplayPreWarm,
    } = usePreWarmSession({
        mode: 'tars_roleplay',
        enabled: roleplayConfig !== null,
        filename: roleplayConfig?.filename,
        user_role: roleplayConfig?.user_role,
        tars_role: roleplayConfig?.tars_role,
    });

    // Transition: loading → home
    useEffect(() => {
        if (currentView !== 'loading') return;
        if (normalPreloadMessage) {
            setView('home');
            return;
        }
        const fallback = setTimeout(() => {
            if (preWarmedSession) setView('home');
        }, 5000);
        return () => clearTimeout(fallback);
    }, [currentView, preWarmedSession, normalPreloadMessage]);

    // Transition: loading-conversation → conversation
    useEffect(() => {
        if (currentView !== 'loading-conversation') return;
        if (preWarmedRoleplaySession && roleplayPreloadMessage) {
            setView('conversation');
        }
    }, [currentView, preWarmedRoleplaySession, roleplayPreloadMessage]);

    // Handle 401 from API calls — logout and redirect
    useEffect(() => {
        if (!checkAuth() && currentView !== 'sign-in' && currentView !== 'sign-up' && currentView !== 'forgot-password') {
            logout();
            setView('sign-in');
        }
    }, [currentView]);

    const activePreWarmedSession =
        currentView === 'conversation'
            ? sessionConfig.mode === 'tars_normal'
                ? preWarmedSession
                : preWarmedRoleplaySession
            : null;

    const activePreloadMessage =
        currentView === 'conversation'
            ? sessionConfig.mode === 'tars_normal'
                ? normalPreloadMessage
                : roleplayPreloadMessage
            : null;

    return (
        <div className="mobile-container">
            {currentView === 'loading' && (
                <LoadingScreen
                    personalised={true}
                    fallbackMessage="Waking up TARS..."
                />
            )}

            {currentView === 'loading-conversation' && (
                <LoadingScreen
                    personalised={false}
                    fallbackMessage="Preparing roleplay..."
                />
            )}

            {currentView === 'home' && (
                <>
                    <Header />
                    <MicButton />
                    <ModeCards />
                </>
            )}

            {currentView === 'roleplay' && (
                <RoleplayScreen />
            )}

            {currentView === 'conversation' && (
                <ConversationContainer
                    sessionConfig={sessionConfig}
                    preWarmedSession={activePreWarmedSession}
                    preloadMessage={activePreloadMessage}
                    onSessionConsumed={() => {
                        resetPreWarm();
                        resetRoleplayPreWarm();
                        consumeSession();
                    }}
                />
            )}

            {currentView === 'profile' && (
                <ProfileScreen />
            )}

            {currentView === 'settings' && (
                <SettingsScreen />
            )}

            {currentView === 'personal-info' && (
                <PersonalInfoScreen />
            )}

            {currentView === 'sign-in' && (
                <SignInScreen />
            )}

            {currentView === 'sign-up' && (
                <SignUpScreen />
            )}

            {currentView === 'forgot-password' && (
                <ForgotPasswordScreen />
            )}

            {currentView !== 'sign-in' &&
                currentView !== 'sign-up' &&
                currentView !== 'forgot-password' &&
                currentView !== 'settings' &&
                currentView !== 'personal-info' &&
                currentView !== 'conversation' &&
                currentView !== 'loading' &&
                currentView !== 'loading-conversation' && (
                    <BottomNav />
                )}
        </div>
    );
}

export default App;
