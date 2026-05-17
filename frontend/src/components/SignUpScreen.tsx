import { useState } from 'react';
import { ArrowLeft, User, Mail, Lock, Eye, EyeOff, ArrowRight, Loader, Globe, GraduationCap, Target, Lightbulb } from 'lucide-react';
import './SignUpScreen.css';
import { useSessionStore } from '../stores/sessionStore';
import darkLogo from '../assets/dark_mode.png';
import lightLogo from '../assets/light_mode.png';
import { API_BASE } from '../apiConfig';


interface FieldErrors {
    username?: string;
    first_name?: string;
    last_name?: string;
    email?: string;
    password?: string;
    password_confirm?: string;
    interests?: string;
    general?: string;
}

const EMAIL_REGEX = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

export default function SignUpScreen() {
    const setView = useSessionStore((s) => s.setView);
    const isLightMode = useSessionStore((s) => s.isLightMode);

    const [username,         setUsername]         = useState('');
    const [firstName,        setFirstName]        = useState('');
    const [lastName,         setLastName]         = useState('');
    const [email,            setEmail]            = useState('');
    const [password,         setPassword]         = useState('');
    const [passwordConfirm,  setPasswordConfirm]  = useState('');
    const [showPassword,     setShowPassword]     = useState(false);
    const [showConfirm,      setShowConfirm]      = useState(false);
    const [nativeLanguage,   setNativeLanguage]   = useState('es');
    const [hskLevel,         setHskLevel]         = useState(1);
    const [learningGoals,    setLearningGoals]    = useState('Travel');
    const [interests,        setInterests]        = useState('');
    const [errors,           setErrors]           = useState<FieldErrors>({});
    const [isLoading,        setIsLoading]        = useState(false);
    const [successMsg,       setSuccessMsg]       = useState('');

    // ── Validación en cliente ────────────────────────────────────────────────
    const validate = (): boolean => {
        const newErrors: FieldErrors = {};

        if (!username.trim()) {
            newErrors.username = 'El nombre de usuario es obligatorio.';
        } else if (username.trim().length < 3) {
            newErrors.username = 'Mínimo 3 caracteres.';
        } else if (!/^[a-zA-Z0-9_.-]+$/.test(username.trim())) {
            newErrors.username = 'Solo letras, números, _, . y -';
        }

        if (!firstName.trim()) newErrors.first_name = 'El nombre es obligatorio.';
        if (!lastName.trim())  newErrors.last_name  = 'El apellido es obligatorio.';

        if (!email.trim()) {
            newErrors.email = 'El correo es obligatorio.';
        } else if (!EMAIL_REGEX.test(email.trim())) {
            newErrors.email = 'Formato de correo no válido.';
        }

        if (!password) {
            newErrors.password = 'La contraseña es obligatoria.';
        } else if (password.length < 8) {
            newErrors.password = 'Mínimo 8 caracteres.';
        } else if (!/[A-Z]/.test(password)) {
            newErrors.password = 'Debe contener al menos una mayúscula.';
        } else if (!/[0-9]/.test(password)) {
            newErrors.password = 'Debe contener al menos un número.';
        }

        if (!passwordConfirm) {
            newErrors.password_confirm = 'Confirma tu contraseña.';
        } else if (password !== passwordConfirm) {
            newErrors.password_confirm = 'Las contraseñas no coinciden.';
        }

        if (!interests.trim()) {
            newErrors.interests = 'Los intereses son obligatorios.';
        }

        setErrors(newErrors);
        return Object.keys(newErrors).length === 0;
    };

    const handleRegister = async () => {
        setSuccessMsg('');
        if (!validate()) return;

        setIsLoading(true);
        try {
            const res = await fetch(`${API_BASE}/auth/register`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    username:         username.trim(),
                    first_name:       firstName.trim(),
                    last_name:        lastName.trim(),
                    email:            email.trim().toLowerCase(),
                    password,
                    password_confirm: passwordConfirm,
                    native_language:  nativeLanguage,
                    hsk_level:        hskLevel,
                    learning_goals:   learningGoals,
                    interests:        interests.trim(),
                }),
            });

            const data = await res.json();

            if (!res.ok) {
                // El backend puede devolver detail de Pydantic (array) o string
                if (Array.isArray(data.detail)) {
                    const msg = data.detail.map((e: { msg: string }) => e.msg).join(' ');
                    setErrors({ general: msg });
                } else {
                    setErrors({ general: data.detail ?? 'Error al registrarse. Inténtalo de nuevo.' });
                }
                return;
            }

            setSuccessMsg('¡Cuenta creada exitosamente! Redirigiendo al login…');
            setTimeout(() => setView('sign-in'), 1800);
        } catch {
            setErrors({ general: 'No se pudo conectar con el servidor. Verifica tu conexión.' });
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="signup-container">
            {/* Background decorative blurs */}
            <div className="signup-decor top-right" />
            <div className="signup-decor bottom-left" />

            {/* Header */}
            <div className="signup-header">
                <button className="signup-back-btn" onClick={() => setView('sign-in')} type="button">
                    <ArrowLeft size={24} color="var(--text-main)" />
                </button>
                <div className="signup-brand">
                    <img
                        src={isLightMode ? lightLogo : darkLogo}
                        alt="Tài Sī Logo"
                        className="signup-logo-img"
                    />
                </div>
                <div style={{ width: 40 }} />
            </div>

            {/* Main content */}
            <main className="signup-main">
                <div className="signup-heading">
                    <h1 className="signup-title">
                        Join the <span className="signup-title-accent">Academy</span>
                    </h1>
                    <p className="signup-subtitle">Enter your details to start your journey into deep focus.</p>
                </div>

                {/* Error / Success banners */}
                {errors.general && (
                    <div className="signup-error-banner" role="alert">{errors.general}</div>
                )}
                {successMsg && (
                    <div className="signup-success-banner" role="status">{successMsg}</div>
                )}

                {/* Form */}
                <div className="signup-form">

                    {/* Username */}
                    <div className="signup-field">
                        <label className="signup-label" htmlFor="signup-username">Username</label>
                        <div className={`signup-input-wrapper ${errors.username ? 'has-error' : ''}`}>
                            <User size={20} className="signup-input-icon" />
                            <input
                                id="signup-username"
                                type="text"
                                className="signup-input"
                                placeholder="tu_usuario"
                                value={username}
                                onChange={e => setUsername(e.target.value)}
                                autoComplete="username"
                                disabled={isLoading}
                            />
                        </div>
                        {errors.username && <span className="signup-field-error">{errors.username}</span>}
                    </div>

                    {/* First name */}
                    <div className="signup-field">
                        <label className="signup-label" htmlFor="signup-firstname">First Name</label>
                        <div className={`signup-input-wrapper ${errors.first_name ? 'has-error' : ''}`}>
                            <User size={20} className="signup-input-icon" />
                            <input
                                id="signup-firstname"
                                type="text"
                                className="signup-input"
                                placeholder="Confucio"
                                value={firstName}
                                onChange={e => setFirstName(e.target.value)}
                                autoComplete="given-name"
                                disabled={isLoading}
                            />
                        </div>
                        {errors.first_name && <span className="signup-field-error">{errors.first_name}</span>}
                    </div>

                    {/* Last name */}
                    <div className="signup-field">
                        <label className="signup-label" htmlFor="signup-lastname">Last Name</label>
                        <div className={`signup-input-wrapper ${errors.last_name ? 'has-error' : ''}`}>
                            <User size={20} className="signup-input-icon" />
                            <input
                                id="signup-lastname"
                                type="text"
                                className="signup-input"
                                placeholder="Zhongni"
                                value={lastName}
                                onChange={e => setLastName(e.target.value)}
                                autoComplete="family-name"
                                disabled={isLoading}
                            />
                        </div>
                        {errors.last_name && <span className="signup-field-error">{errors.last_name}</span>}
                    </div>

                    {/* Email */}
                    <div className="signup-field">
                        <label className="signup-label" htmlFor="signup-email">Email Address</label>
                        <div className={`signup-input-wrapper ${errors.email ? 'has-error' : ''}`}>
                            <Mail size={20} className="signup-input-icon" />
                            <input
                                id="signup-email"
                                type="email"
                                className="signup-input"
                                placeholder="focus@taisi.academy"
                                value={email}
                                onChange={e => setEmail(e.target.value)}
                                autoComplete="email"
                                disabled={isLoading}
                            />
                        </div>
                        {errors.email && <span className="signup-field-error">{errors.email}</span>}
                    </div>

                    {/* Password */}
                    <div className="signup-field">
                        <label className="signup-label" htmlFor="signup-password">Password</label>
                        <div className={`signup-input-wrapper ${errors.password ? 'has-error' : ''}`}>
                            <Lock size={20} className="signup-input-icon" />
                            <input
                                id="signup-password"
                                type={showPassword ? 'text' : 'password'}
                                className="signup-input"
                                placeholder="••••••••"
                                value={password}
                                onChange={e => setPassword(e.target.value)}
                                autoComplete="new-password"
                                disabled={isLoading}
                            />
                            <button
                                type="button"
                                className="signup-eye-btn"
                                onClick={() => setShowPassword(p => !p)}
                                aria-label={showPassword ? 'Ocultar' : 'Mostrar'}
                                disabled={isLoading}
                            >
                                {showPassword ? <EyeOff size={20} /> : <Eye size={20} />}
                            </button>
                        </div>
                        {errors.password && <span className="signup-field-error">{errors.password}</span>}
                        <span className="signup-hint">Min. 8 chars, 1 uppercase, 1 number.</span>
                    </div>

                    {/* Confirm Password */}
                    <div className="signup-field">
                        <label className="signup-label" htmlFor="signup-confirm">Confirm Password</label>
                        <div className={`signup-input-wrapper ${errors.password_confirm ? 'has-error' : ''}`}>
                            <Lock size={20} className="signup-input-icon" />
                            <input
                                id="signup-confirm"
                                type={showConfirm ? 'text' : 'password'}
                                className="signup-input"
                                placeholder="••••••••"
                                value={passwordConfirm}
                                onChange={e => setPasswordConfirm(e.target.value)}
                                autoComplete="new-password"
                                disabled={isLoading}
                            />
                            <button
                                type="button"
                                className="signup-eye-btn"
                                onClick={() => setShowConfirm(p => !p)}
                                aria-label={showConfirm ? 'Ocultar' : 'Mostrar'}
                                disabled={isLoading}
                            >
                                {showConfirm ? <EyeOff size={20} /> : <Eye size={20} />}
                            </button>
                        </div>
                        {errors.password_confirm && (
                            <span className="signup-field-error">{errors.password_confirm}</span>
                        )}
                    </div>

                    {/* Native Language */}
                    <div className="signup-field">
                        <label className="signup-label">Native Language</label>
                        <div className="signup-input-wrapper">
                            <Globe size={20} className="signup-input-icon" />
                            <select 
                                className="signup-input signup-select"
                                value={nativeLanguage}
                                onChange={e => setNativeLanguage(e.target.value)}
                                disabled={isLoading}
                            >
                                <option value="en">English</option>
                                <option value="fr">French</option>
                                <option value="de">German</option>
                                <option value="es">Spanish</option>
                            </select>
                        </div>
                    </div>

                    {/* HSK Level */}
                    <div className="signup-field">
                        <label className="signup-label">HSK Level</label>
                        <div className="signup-input-wrapper">
                            <GraduationCap size={20} className="signup-input-icon" />
                            <select 
                                className="signup-input signup-select"
                                value={hskLevel}
                                onChange={e => setHskLevel(Number(e.target.value))}
                                disabled={isLoading}
                            >
                                <option value={1}>HSK 1 (Beginner)</option>
                                <option value={2}>HSK 2 (Elementary)</option>
                                <option value={3}>HSK 3 (Intermediate)</option>
                                <option value={4}>HSK 4 (Upper Intermediate)</option>
                                <option value={5}>HSK 5 (Advanced)</option>
                                <option value={6}>HSK 6 (Proficient)</option>
                            </select>
                        </div>
                    </div>

                    {/* Learning Goals */}
                    <div className="signup-field">
                        <label className="signup-label">Learning Goals</label>
                        <div className="signup-input-wrapper">
                            <Target size={20} className="signup-input-icon" />
                            <select 
                                className="signup-input signup-select"
                                value={learningGoals}
                                onChange={e => setLearningGoals(e.target.value)}
                                disabled={isLoading}
                            >
                                <option value="Travel">Travel</option>
                                <option value="Business">Business</option>
                                <option value="Academic">Academic</option>
                                <option value="Hobby / Cultural">Hobby / Cultural</option>
                            </select>
                        </div>
                    </div>

                    {/* Interests */}
                    <div className="signup-field">
                        <label className="signup-label">Interests</label>
                        <div className={`signup-input-wrapper ${errors.interests ? 'has-error' : ''}`}>
                            <Lightbulb size={20} className="signup-input-icon" />
                            <input
                                type="text"
                                className="signup-input"
                                placeholder="e.g. Engineering, Literature"
                                value={interests}
                                onChange={e => setInterests(e.target.value)}
                                disabled={isLoading}
                            />
                        </div>
                        {errors.interests && <span className="signup-field-error">{errors.interests}</span>}
                    </div>

                </div>

                {/* Create Account Button */}
                <div className="signup-btn-wrapper">
                    <button
                        id="signup-submit-btn"
                        className="signup-btn"
                        onClick={handleRegister}
                        disabled={isLoading}
                        type="button"
                    >
                        {isLoading ? (
                            <>
                                <Loader size={20} className="signup-spinner" />
                                Creating Account…
                            </>
                        ) : (
                            <>
                                Create Account
                                <ArrowRight size={20} />
                            </>
                        )}
                    </button>
                </div>

                {/* Footer */}
                <div className="signup-footer">
                    <div className="signup-divider">
                        <div className="signup-divider-line" />
                        <span className="signup-divider-text">Mastery awaits</span>
                        <div className="signup-divider-line" />
                    </div>
                    <p className="signup-signin-text">
                        Already have an account?{' '}
                        <button
                            className="signup-signin-link"
                            onClick={() => setView('sign-in')}
                            type="button"
                        >
                            Sign In
                        </button>
                    </p>
                </div>
            </main>
        </div>
    );
}
