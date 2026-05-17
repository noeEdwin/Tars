import { useState, useEffect } from 'react';
import { ChevronLeft, Camera, Loader } from 'lucide-react';
import './PersonalInfoScreen.css';
import { API_BASE } from '../apiConfig';
import { useAuthStore } from '../stores/authStore';
import { useSessionStore } from '../stores/sessionStore';

export default function PersonalInfoScreen() {
    const [fullName, setFullName] = useState('');
    const [nativeLanguage, setNativeLanguage] = useState('es');
    const [hskLevel, setHskLevel] = useState(1);
    const [learningGoals, setLearningGoals] = useState('Travel');
    const [interests, setInterests] = useState('');

    const [isLoading, setIsLoading] = useState(true);
    const [isSaving, setIsSaving] = useState(false);
    const [message, setMessage] = useState({ text: '', type: '' });

    const token = useAuthStore((s) => s.token);
    const updateFirstName = useAuthStore((s) => s.updateFirstName);
    const setView = useSessionStore((s) => s.setView);

    useEffect(() => {
        const fetchProfile = async () => {
            if (!token) return;

            try {
                const res = await fetch(`${API_BASE}/api/user/profile`, {
                    headers: { 'Authorization': `Bearer ${token}` }
                });
                if (res.ok) {
                    const data = await res.json();
                    setFullName(`${data.first_name} ${data.last_name}`.trim());
                    setNativeLanguage(data.native_language || 'es');
                    setHskLevel(data.hsk_level || 1);
                    setLearningGoals(data.learning_goals || 'Travel');
                    setInterests(data.interests || '');
                }
            } catch (err) {
                console.error("Error fetching profile", err);
            } finally {
                setIsLoading(false);
            }
        };
        fetchProfile();
    }, [token]);

    const handleSave = async (e: React.FormEvent) => {
        e.preventDefault();
        setMessage({ text: '', type: '' });
        setIsSaving(true);

        const nameParts = fullName.trim().split(' ');
        const firstName = nameParts[0] || '';
        const lastName = nameParts.slice(1).join(' ') || '';

        try {
            const res = await fetch(`${API_BASE}/api/user/profile`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({
                    first_name: firstName,
                    last_name: lastName,
                    hsk_level: hskLevel,
                    native_language: nativeLanguage,
                    learning_goals: learningGoals,
                    interests: interests
                })
            });

            if (res.ok) {
                const data = await res.json();
                updateFirstName(data.first_name);
                setMessage({ text: 'Profile updated successfully!', type: 'success' });
            } else {
                setMessage({ text: 'Failed to update profile.', type: 'error' });
            }
        } catch (err) {
            setMessage({ text: 'Network error.', type: 'error' });
        } finally {
            setIsSaving(false);
        }
    };

    if (isLoading) {
        return (
            <div className="pinfo-container" style={{ display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
                <Loader size={32} className="spinning" color="var(--primary)" />
            </div>
        );
    }

    return (
        <div className="pinfo-container">
            <header className="pinfo-header">
                <button className="pinfo-back-btn" onClick={() => setView('settings')} type="button">
                    <ChevronLeft size={24} color="var(--text-muted)" />
                </button>
                <h1 className="pinfo-title">Personal Info</h1>
                <div style={{ width: 40 }} />
            </header>

            <main className="pinfo-main">

                <section className="pinfo-avatar-section">
                    <div className="pinfo-avatar-wrapper">
                        <div className="pinfo-avatar">
                            <img
                                src="https://lh3.googleusercontent.com/aida-public/AB6AXuCKeKD-chEZ3OzdMiLIR4sNnY_1LVjNZPqi0YvR4yyD18AtMlNCzYNyhrDpoIrUclmJs48b3_20kWJRlA6MCBh0r1bsEYUpGjTnAA-KUc1Tp0Fl05UvrpiFbIkZkro_VLbdkGbhE6gLRZep-rCL030V3IGM5q_YP4SNkrF3Z8vSKZQGpYLjD_bIitFc5BJibxN8yIXBCpl4mszsimJ3SZe15j4tushTbDjN0m5PfxgfxoYQ_WWn7uRNF8vijMUMrVwLKDNzHPOGPpDU"
                                alt="Profile"
                                className="pinfo-avatar-img"
                            />
                        </div>
                        <button className="pinfo-avatar-edit" type="button">
                            <Camera size={16} color="white" />
                        </button>
                    </div>
                    <p className="pinfo-avatar-label">Upload Profile Photo</p>
                </section>

                <form className="pinfo-form" onSubmit={handleSave}>

                    {message.text && (
                        <div style={{
                            padding: '10px',
                            marginBottom: '15px',
                            borderRadius: '8px',
                            textAlign: 'center',
                            backgroundColor: message.type === 'success' ? 'rgba(46, 204, 113, 0.1)' : 'rgba(231, 76, 60, 0.1)',
                            color: message.type === 'success' ? '#2ecc71' : '#e74c3c'
                        }}>
                            {message.text}
                        </div>
                    )}

                    <div className="pinfo-field">
                        <label className="pinfo-label">Full Name</label>
                        <div className="pinfo-input-box">
                            <input
                                type="text"
                                className="pinfo-input"
                                value={fullName}
                                onChange={e => setFullName(e.target.value)}
                                placeholder="Your Name"
                                required
                            />
                        </div>
                    </div>

                    <div className="pinfo-field">
                        <label className="pinfo-label">Native Language</label>
                        <div className="pinfo-input-box">
                            <select
                                className="pinfo-input pinfo-select"
                                value={nativeLanguage}
                                onChange={e => setNativeLanguage(e.target.value)}
                            >
                                <option value="en">English</option>
                                <option value="fr">French</option>
                                <option value="de">German</option>
                                <option value="es">Spanish</option>
                            </select>
                        </div>
                    </div>

                    <div className="pinfo-field">
                        <label className="pinfo-label">Current HSK Level</label>
                        <div className="pinfo-input-box">
                            <select
                                className="pinfo-input pinfo-select"
                                value={hskLevel}
                                onChange={e => setHskLevel(Number(e.target.value))}
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

                    <div className="pinfo-field">
                        <label className="pinfo-label">Learning Goals</label>
                        <div className="pinfo-input-box">
                            <select
                                className="pinfo-input pinfo-select"
                                value={learningGoals}
                                onChange={e => setLearningGoals(e.target.value)}
                            >
                                <option value="Travel">Travel</option>
                                <option value="Business">Business</option>
                                <option value="Academic">Academic</option>
                                <option value="Hobby / Cultural">Hobby / Cultural</option>
                            </select>
                        </div>
                    </div>

                    <div className="pinfo-field">
                        <label className="pinfo-label">Interests</label>
                        <div className="pinfo-input-box">
                            <input
                                type="text"
                                className="pinfo-input"
                                value={interests}
                                onChange={e => setInterests(e.target.value)}
                                placeholder="e.g. Engineering, Literature"
                            />
                        </div>
                    </div>

                    <div className="pinfo-save-wrapper">
                        <button type="submit" className="pinfo-save-btn" disabled={isSaving}>
                            {isSaving ? 'Saving...' : 'Save Changes'}
                        </button>
                    </div>

                </form>
            </main>
        </div>
    );
}
