import { ChevronLeft, Camera } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import './PersonalInfoScreen.css';
import type { ViewState } from '../App';

interface PersonalInfoScreenProps {
    setCurrentView: (view: ViewState) => void;
}

export default function PersonalInfoScreen({ setCurrentView }: PersonalInfoScreenProps) {
    const { t } = useTranslation();

    return (
        <div className="pinfo-container">
            <header className="pinfo-header">
                <button className="pinfo-back-btn" onClick={() => setCurrentView('settings')}>
                    <ChevronLeft size={24} color="var(--text-muted)" />
                </button>
                <h1 className="pinfo-title">{t('personalInfo.title')}</h1>
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
                        <button className="pinfo-avatar-edit">
                            <Camera size={16} color="white" />
                        </button>
                    </div>
                    <p className="pinfo-avatar-label">{t('personalInfo.uploadPhoto')}</p>
                </section>

                <form className="pinfo-form">
                    <div className="pinfo-field">
                        <label className="pinfo-label">{t('personalInfo.fullName')}</label>
                        <div className="pinfo-input-box">
                            <input
                                type="text"
                                className="pinfo-input"
                                defaultValue="Alexander Chen"
                                placeholder={t('personalInfo.yourName')}
                            />
                        </div>
                    </div>

                    <div className="pinfo-field">
                        <label className="pinfo-label">{t('personalInfo.nativeLanguage')}</label>
                        <div className="pinfo-input-box">
                            <select className="pinfo-input pinfo-select">
                                <option value="en">{t('personalInfo.english')}</option>
                                <option value="fr">{t('personalInfo.french')}</option>
                                <option value="de">{t('personalInfo.german')}</option>
                                <option value="es">{t('personalInfo.spanish')}</option>
                            </select>
                        </div>
                    </div>

                    <div className="pinfo-field">
                        <label className="pinfo-label">{t('personalInfo.hskLevel')}</label>
                        <div className="pinfo-input-box">
                            <select className="pinfo-input pinfo-select">
                                <option>{t('personalInfo.hsk1')}</option>
                                <option>{t('personalInfo.hsk2')}</option>
                                <option defaultValue="">{t('personalInfo.hsk3')}</option>
                                <option>{t('personalInfo.hsk4')}</option>
                                <option>{t('personalInfo.hsk5')}</option>
                                <option>{t('personalInfo.hsk6')}</option>
                            </select>
                        </div>
                    </div>

                    <div className="pinfo-field">
                        <label className="pinfo-label">{t('personalInfo.learningGoals')}</label>
                        <div className="pinfo-input-box">
                            <select className="pinfo-input pinfo-select">
                                <option>{t('personalInfo.travel')}</option>
                                <option>{t('personalInfo.business')}</option>
                                <option>{t('personalInfo.academic')}</option>
                                <option>{t('personalInfo.hobby')}</option>
                            </select>
                        </div>
                    </div>

                    <div className="pinfo-field">
                        <label className="pinfo-label">{t('personalInfo.interests')}</label>
                        <div className="pinfo-input-box">
                            <input
                                type="text"
                                className="pinfo-input"
                                defaultValue="Engineering, Technology, Urbanism"
                                placeholder="e.g. Engineering, Literature"
                            />
                        </div>
                    </div>

                    <div className="pinfo-save-wrapper">
                        <button type="submit" className="pinfo-save-btn">
                            {t('personalInfo.saveChanges')}
                        </button>
                    </div>
                </form>
            </main>
        </div>
    );
}
