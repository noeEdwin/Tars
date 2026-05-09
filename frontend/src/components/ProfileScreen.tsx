import { ArrowLeft, Settings, TrendingUp, Sparkles, Flame, PlusCircle } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import './ProfileScreen.css';
import type { ViewState } from '../App';

interface ProfileScreenProps {
    setCurrentView: (view: ViewState) => void;
}

export default function ProfileScreen({ setCurrentView }: ProfileScreenProps) {
    const { t } = useTranslation();

    return (
        <div className="profile-container">
            <header className="profile-header">
                <button
                    className="icon-btn-glass"
                    onClick={() => setCurrentView('home')}
                >
                    <ArrowLeft size={24} color="var(--text-main)" />
                </button>
                <h1 className="profile-title">{t('profile.title')}</h1>
                <button className="icon-btn-glass" onClick={() => setCurrentView('settings')}>
                    <Settings size={24} color="var(--text-main)" />
                </button>
            </header>

            <main className="profile-main">
                <section className="user-info-section">
                    <div className="avatar-wrapper">
                        <div className="avatar-ring">
                            <div className="avatar-inner">
                                <img
                                    src="https://lh3.googleusercontent.com/aida-public/AB6AXuC5vgsaWvjE0DCUTFwifn_Gpudh5ESvDwXeJiA1NBN_YXdWgVzTu0zhWy8vIiSjnU4Fnei7w6gw9zedoirJDKEH3OzWX1YS5QH5xJd8NFD8byTQ_ob1qaUnQ0YKiCPGkeFT5VreHdhZaExItkuVSxlcIfnl1J_pHY8IdmmbSTwkCqbo0f-lmtKYDjfu8cwZPBLakuBUTHk_ATypkeNQ7V_d__uVhAxGN7xSXaTu5M_nuUiQe4qE71fru46ONXZ-XbBsXJV2jJjbhQqd"
                                    alt="User Profile"
                                    className="avatar-img"
                                />
                            </div>
                        </div>
                        <div className="level-badge">{t('profile.level')}</div>
                    </div>

                    <div className="user-details">
                        <h2 className="user-name">Lin Yao</h2>
                        <p className="user-title">{t('profile.imperialScholar')}</p>
                        <div className="user-status">
                            <Sparkles size={18} color="var(--jade-accent)" fill="var(--jade-accent)" />
                            <span>{t('profile.mandarinMaster')}</span>
                        </div>
                    </div>
                </section>

                <section className="stats-grid">
                    <div className="stat-card border-jade">
                        <p className="stat-label">{t('profile.hoursSpoken')}</p>
                        <p className="stat-value">128.5<span className="stat-unit unit-jade">{t('profile.hoursUnit')}</span></p>
                        <div className="stat-trend trend-jade">
                            <TrendingUp size={12} />
                            <span>{t('profile.thisMonth')}</span>
                        </div>
                    </div>

                    <div className="stat-card border-gold">
                        <p className="stat-label">{t('profile.mastery')}</p>
                        <p className="stat-value">45<span className="stat-unit unit-gold">{t('profile.masteryUnit')}</span></p>
                        <div className="stat-trend trend-gold">
                            <Sparkles size={12} />
                            <span>{t('profile.hskLevel')}</span>
                        </div>
                    </div>

                    <div className="stat-card border-primary">
                        <p className="stat-label">{t('profile.currentStreak')}</p>
                        <p className="stat-value">214<span className="stat-unit unit-primary">{t('profile.streakUnit')}</span></p>
                        <div className="stat-trend trend-primary">
                            <Flame size={12} />
                            <span>{t('profile.topStreak')}</span>
                        </div>
                    </div>

                    <div className="stat-card border-jade">
                        <p className="stat-label">{t('profile.vocabulary')}</p>
                        <p className="stat-value">5,240</p>
                        <div className="stat-trend trend-jade">
                            <PlusCircle size={12} />
                            <span>{t('profile.thisWeek')}</span>
                        </div>
                    </div>
                </section>
            </main>
        </div>
    );
}
