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
import './index.css';
import './App.css';

export type ViewState = 'home' | 'roleplay' | 'profile' | 'settings' | 'personal-info' | 'sign-in' | 'sign-up' | 'forgot-password';

function App() {
  const [isLightMode, setIsLightMode] = useState(false);
  const [currentView, setCurrentView] = useState<ViewState>('home');

  useEffect(() => {
    if (isLightMode) {
      document.documentElement.setAttribute('data-theme', 'light');
    } else {
      document.documentElement.removeAttribute('data-theme');
    }
  }, [isLightMode]);

  const toggleTheme = () => setIsLightMode(!isLightMode);

  return (
    <div className="mobile-container">
      {currentView === 'home' && (
        <>
          <Header isLightMode={isLightMode} toggleTheme={toggleTheme} />
          <MicButton />
          <ModeCards setCurrentView={setCurrentView} />
        </>
      )}

      {currentView === 'roleplay' && (
        <RoleplayScreen setCurrentView={setCurrentView} />
      )}

      {currentView === 'profile' && (
        <ProfileScreen setCurrentView={setCurrentView} />
      )}

      {currentView === 'settings' && (
        <SettingsScreen setCurrentView={setCurrentView} isLightMode={isLightMode} toggleTheme={toggleTheme} />
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

      {currentView !== 'sign-in' && currentView !== 'sign-up' && currentView !== 'forgot-password' && currentView !== 'settings' && currentView !== 'personal-info' && (
        <BottomNav currentView={currentView} setCurrentView={setCurrentView} />
      )}
    </div>
  );
}

export default App;
