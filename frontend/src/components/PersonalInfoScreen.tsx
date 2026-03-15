import { ChevronLeft, Camera } from 'lucide-react';
import './PersonalInfoScreen.css';
import type { ViewState } from '../App';

interface PersonalInfoScreenProps {
    setCurrentView: (view: ViewState) => void;
}

export default function PersonalInfoScreen({ setCurrentView }: PersonalInfoScreenProps) {
    return (
        <div className="pinfo-container">
            {/* Header */}
            <header className="pinfo-header">
                <button className="pinfo-back-btn" onClick={() => setCurrentView('settings')}>
                    <ChevronLeft size={24} color="var(--text-muted)" />
                </button>
                <h1 className="pinfo-title">Personal Info</h1>
                <div style={{ width: 40 }} />
            </header>

            {/* Scrollable content */}
            <main className="pinfo-main">

                {/* Avatar Section */}
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
                    <p className="pinfo-avatar-label">Upload Profile Photo</p>
                </section>

                {/* Form */}
                <form className="pinfo-form">

                    {/* Full Name */}
                    <div className="pinfo-field">
                        <label className="pinfo-label">Full Name</label>
                        <div className="pinfo-input-box">
                            <input
                                type="text"
                                className="pinfo-input"
                                defaultValue="Alexander Chen"
                                placeholder="Your Name"
                            />
                        </div>
                    </div>

                    {/* Native Language */}
                    <div className="pinfo-field">
                        <label className="pinfo-label">Native Language</label>
                        <div className="pinfo-input-box">
                            <select className="pinfo-input pinfo-select">
                                <option value="en">English</option>
                                <option value="fr">French</option>
                                <option value="de">German</option>
                                <option value="es">Spanish</option>
                            </select>
                        </div>
                    </div>

                    {/* HSK Level */}
                    <div className="pinfo-field">
                        <label className="pinfo-label">Current HSK Level</label>
                        <div className="pinfo-input-box">
                            <select className="pinfo-input pinfo-select">
                                <option>HSK 1 (Beginner)</option>
                                <option>HSK 2 (Elementary)</option>
                                <option defaultValue="">HSK 3 (Intermediate)</option>
                                <option>HSK 4 (Upper Intermediate)</option>
                                <option>HSK 5 (Advanced)</option>
                                <option>HSK 6 (Proficient)</option>
                            </select>
                        </div>
                    </div>

                    {/* Learning Goals */}
                    <div className="pinfo-field">
                        <label className="pinfo-label">Learning Goals</label>
                        <div className="pinfo-input-box">
                            <select className="pinfo-input pinfo-select">
                                <option>Travel</option>
                                <option>Business</option>
                                <option>Academic</option>
                                <option>Hobby / Cultural</option>
                            </select>
                        </div>
                    </div>

                    {/* Interests */}
                    <div className="pinfo-field">
                        <label className="pinfo-label">Interests</label>
                        <div className="pinfo-input-box">
                            <input
                                type="text"
                                className="pinfo-input"
                                defaultValue="Engineering, Technology, Urbanism"
                                placeholder="e.g. Engineering, Literature"
                            />
                        </div>
                    </div>

                    {/* Save Button */}
                    <div className="pinfo-save-wrapper">
                        <button type="submit" className="pinfo-save-btn">
                            Save Changes
                        </button>
                    </div>

                </form>
            </main>
        </div>
    );
}
