import { useState } from 'react';
import { Mail, Lock, Eye, EyeOff, ArrowRight, Loader } from 'lucide-react';
import './SignInScreen.css';
import darkLogo from '../assets/dark_mode.png';
import lightLogo from '../assets/light_mode.png';
import { API_BASE } from '../apiConfig';
import { useAuthStore } from '../stores/authStore';
import { useSessionStore } from '../stores/sessionStore';

export default function SignInScreen() {
    const [username, setUsername]         = useState('');
    const [password, setPassword]         = useState('');
    const [showPassword, setShowPassword] = useState(false);
    const [error, setError]               = useState('');
    const [isLoading, setIsLoading]       = useState(false);

    const login = useAuthStore((s) => s.login);
    const setView = useSessionStore((s) => s.setView);
    const isLightMode = useSessionStore((s) => s.isLightMode);

    const handleLogin = async () => {
        setError('');

        if (!username.trim() || !password.trim()) {
            setError('Por favor, completa todos los campos.');
            return;
        }

        setIsLoading(true);
        try {
            const res = await fetch(`${API_BASE}/auth/login`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username: username.trim(), password }),
            });

            const data = await res.json();

            if (!res.ok) {
                setError(data.detail ?? 'Error al iniciar sesión. Inténtalo de nuevo.');
                return;
            }

            login(data.access_token, data.user_id, data.username, data.first_name);
            setView('loading');
        } catch (err: any) {
            if (err instanceof TypeError && err.message?.includes('fetch')) {
                setError('No se pudo conectar con el servidor. Verifica que el backend esté corriendo con SSL.');
            } else {
                setError('Error inesperado. Inténtalo de nuevo.');
            }
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="signin-container">
            <div className="signin-bg-mesh" />

            <div className="signin-content">

                <div className="signin-logo-group">
                    <img
                        src={isLightMode ? lightLogo : darkLogo}
                        alt="Tài Sī Logo"
                        className="signin-logo-img"
                    />
                </div>

                <div className="signin-heading">
                    <h1 className="signin-title">Welcome Back</h1>
                    <p className="signin-subtitle">Continue your journey to fluency.</p>
                </div>

                {error && (
                    <div className="signin-error-banner" role="alert">
                        {error}
                    </div>
                )}

                <div className="signin-form">

                    <div className="signin-field">
                        <label className="signin-label" htmlFor="signin-username">Username</label>
                        <div className="signin-input-wrapper group-field">
                            <Mail size={20} className="signin-input-icon" />
                            <input
                                id="signin-username"
                                type="text"
                                className="signin-input"
                                placeholder="tu_usuario"
                                value={username}
                                onChange={e => setUsername(e.target.value)}
                                onKeyDown={e => e.key === 'Enter' && handleLogin()}
                                autoComplete="username"
                                disabled={isLoading}
                            />
                        </div>
                    </div>

                    <div className="signin-field">
                        <div className="signin-label-row">
                            <label className="signin-label" htmlFor="signin-password">Password</label>
                            <button
                                className="signin-forgot"
                                onClick={() => setView('forgot-password')}
                                type="button"
                            >
                                Forgot Password?
                            </button>
                        </div>
                        <div className="signin-input-wrapper group-field">
                            <Lock size={20} className="signin-input-icon" />
                            <input
                                id="signin-password"
                                type={showPassword ? 'text' : 'password'}
                                className="signin-input"
                                placeholder="••••••••"
                                value={password}
                                onChange={e => setPassword(e.target.value)}
                                onKeyDown={e => e.key === 'Enter' && handleLogin()}
                                autoComplete="current-password"
                                disabled={isLoading}
                            />
                            <button
                                type="button"
                                className="signin-eye-btn"
                                onClick={() => setShowPassword(p => !p)}
                                aria-label={showPassword ? 'Ocultar contraseña' : 'Mostrar contraseña'}
                                disabled={isLoading}
                            >
                                {showPassword ? <EyeOff size={20} /> : <Eye size={20} />}
                            </button>
                        </div>
                    </div>

                    <button
                        id="signin-submit-btn"
                        className="signin-btn"
                        onClick={handleLogin}
                        disabled={isLoading}
                    >
                        {isLoading ? (
                            <>
                                <Loader size={20} className="signin-spinner" />
                                Signing in…
                            </>
                        ) : (
                            <>
                                Sign In
                                <ArrowRight size={20} />
                            </>
                        )}
                    </button>

                </div>

                <div className="signin-social" style={{ marginTop: '24px' }}>
                    <p className="signin-register-text">
                        Don't have an account?{' '}
                        <button
                            className="signin-register-link"
                            onClick={() => setView('sign-up')}
                            type="button"
                        >
                            Create one now
                        </button>
                    </p>
                </div>

            </div>
        </div>
    );
}
