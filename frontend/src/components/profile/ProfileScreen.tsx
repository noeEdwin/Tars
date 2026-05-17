import { ArrowLeft, Settings, TrendingUp, Sparkles, Flame, PlusCircle } from 'lucide-react';
import './ProfileScreen.css';
import { useAuthStore } from '../../stores/authStore';
import { useSessionStore } from '../../stores/sessionStore';

export default function ProfileScreen() {
    const firstName = useAuthStore((s) => s.firstName);
    const username = useAuthStore((s) => s.username);
    const setView = useSessionStore((s) => s.setView);

    const displayName = (firstName && firstName !== 'null') ? firstName : (username || 'User');

    return (
        <div className="profile-container">
            <header className="profile-header">
                <button
                    className="icon-btn-glass"
                    onClick={() => setView('home')}
                >
                    <ArrowLeft size={24} color="var(--text-main)" />
                </button>
                <h1 className="profile-title">Scholar Profile</h1>
                <button className="icon-btn-glass" onClick={() => setView('settings')}>
                    <Settings size={24} color="var(--text-main)" />
                </button>
            </header>

            <main className="profile-main">
                <section className="user-info-section">
                    <div className="avatar-wrapper">
                        <div className="avatar-ring">
                            <div className="avatar-inner">
                                <img
                                    src="https://lh3.googleusercontent.com/aida-public/AB6AXuC5vgsaWvjE0DCUTFwifn_Gpudh5ESvDwXeJiA1NBN_YXdWgVzTu0zhWy8vIiSjnU4Fnei7w6gw9zedoirJDKEH3OzWX1YS5QH5xJd8NFD6byTQ_ob1qaUnQ0YKiCPGkeFT5VreHdhZaExItkuVSxlcIfnl1J_pHY8IdmmbSTwkCqbo0f-lmtKYDjfu8cwZPBLakuBUTHk_ATypkeNQ7V_d__uVhAxGN7xSXaTu5M_nuUiQe4qE71fru46ONXZ-XbBsXJV2jJjbhQqd"
                                    alt="User Profile"
                                    className="avatar-img"
                                />
                            </div>
                        </div>
                        <div className="level-badge">Lvl 42</div>
                    </div>

                    <div className="user-details">
                        <h2 className="user-name">{displayName}</h2>
                        <p className="user-title">Imperial Scholar</p>
                        <div className="user-status">
                            <Sparkles size={18} color="var(--jade-accent)" fill="var(--jade-accent)" />
                            <span>Mandarin Master</span>
                        </div>
                    </div>
                </section>

                <section className="stats-grid">
                    <div className="stat-card border-jade">
                        <p className="stat-label">Hours Spoken</p>
                        <p className="stat-value">128.5<span className="stat-unit unit-jade">h</span></p>
                        <div className="stat-trend trend-jade">
                            <TrendingUp size={12} />
                            <span>12% this month</span>
                        </div>
                    </div>

                    <div className="stat-card border-gold">
                        <p className="stat-label">Mastery</p>
                        <p className="stat-value">45<span className="stat-unit unit-gold">%</span></p>
                        <div className="stat-trend trend-gold">
                            <Sparkles size={12} />
                            <span>HSK 5 Level</span>
                        </div>
                    </div>

                    <div className="stat-card border-primary">
                        <p className="stat-label">Current Streak</p>
                        <p className="stat-value">214<span className="stat-unit unit-primary">d</span></p>
                        <div className="stat-trend trend-primary">
                            <Flame size={12} />
                            <span>Top 1% streak</span>
                        </div>
                    </div>

                    <div className="stat-card border-jade">
                        <p className="stat-label">Vocabulary</p>
                        <p className="stat-value">5,240</p>
                        <div className="stat-trend trend-jade">
                            <PlusCircle size={12} />
                            <span>+150 this week</span>
                        </div>
                    </div>
                </section>

            </main>
        </div>
    );
}
