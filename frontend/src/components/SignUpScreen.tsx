import { ArrowLeft, User, Mail, Lock, Eye, ArrowRight } from 'lucide-react';
import './SignUpScreen.css';
import type { ViewState } from '../App';
import darkLogo from '../assets/dark_mode.png';
import lightLogo from '../assets/light_mode.png';

interface SignUpScreenProps {
    setCurrentView: (view: ViewState) => void;
    isLightMode: boolean;
}

export default function SignUpScreen({ setCurrentView, isLightMode }: SignUpScreenProps) {
    return (
        <div className="signup-container">
            {/* Background decorative blurs */}
            <div className="signup-decor top-right" />
            <div className="signup-decor bottom-left" />

            {/* Header */}
            <div className="signup-header">
                <button className="signup-back-btn" onClick={() => setCurrentView('sign-in')}>
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

                {/* Form */}
                <div className="signup-form">
                    {/* Full Name */}
                    <div className="signup-field">
                        <label className="signup-label">Full Name</label>
                        <div className="signup-input-wrapper">
                            <User size={20} className="signup-input-icon" />
                            <input
                                type="text"
                                className="signup-input"
                                placeholder="Master Confucius"
                            />
                        </div>
                    </div>

                    {/* Email */}
                    <div className="signup-field">
                        <label className="signup-label">Email Address</label>
                        <div className="signup-input-wrapper">
                            <Mail size={20} className="signup-input-icon" />
                            <input
                                type="email"
                                className="signup-input"
                                placeholder="focus@taisi.academy"
                            />
                        </div>
                    </div>

                    {/* Password */}
                    <div className="signup-field">
                        <label className="signup-label">Password</label>
                        <div className="signup-input-wrapper">
                            <Lock size={20} className="signup-input-icon" />
                            <input
                                type="password"
                                className="signup-input"
                                placeholder="••••••••"
                            />
                            <button type="button" className="signup-eye-btn">
                                <Eye size={20} />
                            </button>
                        </div>
                    </div>
                </div>

                {/* Create Account Button */}
                <div className="signup-btn-wrapper">
                    <button
                        className="signup-btn"
                        onClick={() => setCurrentView('home')}
                    >
                        Create Account
                        <ArrowRight size={20} />
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
                            onClick={() => setCurrentView('sign-in')}
                        >
                            Sign In
                        </button>
                    </p>
                </div>
            </main>
        </div>
    );
}
