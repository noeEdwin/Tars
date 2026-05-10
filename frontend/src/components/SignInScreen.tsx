import { useState } from 'react';
import { Mail, Lock, Eye, EyeOff, ArrowRight, Loader } from 'lucide-react';
import './SignInScreen.css';
import type { ViewState } from '../App';
import darkLogo from '../assets/dark_mode.png';
import lightLogo from '../assets/light_mode.png';
import { API_BASE } from '../apiConfig';

interface SignInScreenProps {
    setCurrentView: (view: ViewState) => void;
    isLightMode: boolean;
}

export default function SignInScreen({ setCurrentView, isLightMode }: SignInScreenProps) {
    const [username, setUsername]         = useState('');
    const [password, setPassword]         = useState('');
    const [showPassword, setShowPassword] = useState(false);
    const [error, setError]               = useState('');
    const [isLoading, setIsLoading]       = useState(false);

    const handleLogin = async () => {
        setError('');

        // Validación en cliente
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
                // El backend devuelve { detail: "..." }
                setError(data.detail ?? 'Error al iniciar sesión. Inténtalo de nuevo.');
                return;
            }

            // Guardar token y datos básicos del usuario en localStorage
            localStorage.setItem('tars_token',      data.access_token);
            localStorage.setItem('tars_user_id',    data.user_id);
            localStorage.setItem('tars_username',   data.username);
            localStorage.setItem('tars_first_name', data.first_name);

            setCurrentView('loading');
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
            {/* Background mesh gradients */}
            <div className="signin-bg-mesh" />

            <div className="signin-content">

                {/* Logo */}
                <div className="signin-logo-group">
                    <img
                        src={isLightMode ? lightLogo : darkLogo}
                        alt="Tài Sī Logo"
                        className="signin-logo-img"
                    />
                </div>

                {/* Heading */}
                <div className="signin-heading">
                    <h1 className="signin-title">Welcome Back</h1>
                    <p className="signin-subtitle">Continue your journey to fluency.</p>
                </div>

                {/* Error global */}
                {error && (
                    <div className="signin-error-banner" role="alert">
                        {error}
                    </div>
                )}

                {/* Form */}
                <div className="signin-form">

                    {/* Username */}
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

                    {/* Password */}
                    <div className="signin-field">
                        <div className="signin-label-row">
                            <label className="signin-label" htmlFor="signin-password">Password</label>
                            <button
                                className="signin-forgot"
                                onClick={() => setCurrentView('forgot-password')}
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

                    {/* Sign In Button */}
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

                {/* Social & Register */}
                <div className="signin-social" style={{ marginTop: '24px' }}>
                    <p className="signin-register-text">
                        Don't have an account?{' '}
                        <button
                            className="signin-register-link"
                            onClick={() => setCurrentView('sign-up')}
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
