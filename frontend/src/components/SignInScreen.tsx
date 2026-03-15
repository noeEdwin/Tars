import { Mail, Lock, Eye, ArrowRight } from 'lucide-react';
import './SignInScreen.css';
import type { ViewState } from '../App';
import darkLogo from '../assets/dark_mode.png';
import lightLogo from '../assets/light_mode.png';

interface SignInScreenProps {
    setCurrentView: (view: ViewState) => void;
    isLightMode: boolean;
}

export default function SignInScreen({ setCurrentView, isLightMode }: SignInScreenProps) {
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

                {/* Form */}
                <div className="signin-form">

                    {/* Email */}
                    <div className="signin-field">
                        <label className="signin-label">Email Address</label>
                        <div className="signin-input-wrapper group-field">
                            <Mail size={20} className="signin-input-icon" />
                            <input
                                type="email"
                                className="signin-input"
                                placeholder="name@example.com"
                            />
                        </div>
                    </div>

                    {/* Password */}
                    <div className="signin-field">
                        <div className="signin-label-row">
                            <label className="signin-label">Password</label>
                            <button className="signin-forgot" onClick={() => setCurrentView('forgot-password')}>Forgot Password?</button>
                        </div>
                        <div className="signin-input-wrapper group-field">
                            <Lock size={20} className="signin-input-icon" />
                            <input
                                type="password"
                                className="signin-input"
                                placeholder="••••••••"
                            />
                            <button type="button" className="signin-eye-btn">
                                <Eye size={20} />
                            </button>
                        </div>
                    </div>

                    {/* Sign In Button */}
                    <button
                        className="signin-btn"
                        onClick={() => setCurrentView('home')}
                    >
                        Sign In
                        <ArrowRight size={20} />
                    </button>

                </div>

                {/* Divider */}
                <div className="signin-divider">
                    <div className="signin-divider-line" />
                    <span className="signin-divider-text">or continue with</span>
                    <div className="signin-divider-line" />
                </div>

                {/* Social & Register */}
                <div className="signin-social">
                    <button className="signin-google-btn">
                        <img
                            src="https://lh3.googleusercontent.com/aida-public/AB6AXuDkurYWaGtt5X4Ph50IoA9JQYcgLzADTziFhxySkWa5NV4LIaN4Sk1MDLj9fuJKBv5g_WrCLwwRtnPAwI3_Qg6xxL6R4sZuWGvzg62Oc5K4jtoQ36FBFeMGd1BnYo4xlnAMptGhADVH0AxtsENpU-jTWBX4JHJTzftUeulJIOkJVUa8ZYM1lNVogfAiQ5sHDLkSPw2QPSP2i3uPd1uJAxtLuJgbRsIfah-VRypgy-E0o3cJvI51qp1wr5pgIz5j6ceRYRHUZMY-AUxD"
                            alt="Google"
                            className="signin-google-logo"
                        />
                        Continue with Google
                    </button>

                    <p className="signin-register-text">
                        Don't have an account?{' '}
                        <button
                            className="signin-register-link"
                            onClick={() => setCurrentView('sign-up')}
                        >
                            Create one now
                        </button>
                    </p>
                </div>

            </div>
        </div>
    );
}
