import { ArrowLeft, Mail, Send } from 'lucide-react';
import './ForgotPasswordScreen.css';
import type { ViewState } from '../App';

interface ForgotPasswordScreenProps {
    setCurrentView: (view: ViewState) => void;
}

export default function ForgotPasswordScreen({ setCurrentView }: ForgotPasswordScreenProps) {
    return (
        <div className="fp-container">
            {/* Background grid + blurs */}
            <div className="fp-grid-bg" />
            <div className="fp-decor top-right" />
            <div className="fp-decor bottom-left" />

            <div className="fp-inner">
                {/* Back Button */}
                <div className="fp-back-row">
                    <button className="fp-back-btn" onClick={() => setCurrentView('sign-in')}>
                        <ArrowLeft size={22} />
                    </button>
                </div>

                {/* Glass Card */}
                <div className="fp-card">
                    {/* Header */}
                    <div className="fp-card-header">
                        <h1 className="fp-title">
                            Forgot <span className="fp-title-accent">Password?</span>
                        </h1>
                        <p className="fp-subtitle">
                            Don't worry, it happens to the best of us. Enter your email address to receive a password reset link.
                        </p>
                    </div>

                    {/* Form */}
                    <div className="fp-form">
                        <div className="fp-field">
                            <label className="fp-label">Email address</label>
                            <div className="fp-input-wrapper">
                                <Mail size={20} className="fp-input-icon" />
                                <input
                                    type="email"
                                    className="fp-input"
                                    placeholder="e.g. name@email.com"
                                />
                            </div>
                        </div>

                        <button className="fp-submit-btn">
                            <span>Send Reset Link</span>
                            <Send size={20} />
                        </button>
                    </div>

                    {/* Bottom link */}
                    <div className="fp-footer">
                        <p className="fp-footer-text">
                            Remember your password?{' '}
                            <button
                                className="fp-login-link"
                                onClick={() => setCurrentView('sign-in')}
                            >
                                Log in
                            </button>
                        </p>
                    </div>
                </div>
            </div>
        </div>
    );
}
