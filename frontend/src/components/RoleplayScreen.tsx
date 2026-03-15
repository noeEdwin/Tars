import { ChevronLeft, Info, CloudUpload, Calendar, FileText, Play, CornerDownLeft, History } from 'lucide-react';
import './RoleplayScreen.css';
import type { ViewState } from '../App';

interface RoleplayScreenProps {
    setCurrentView: (view: ViewState) => void;
}

export default function RoleplayScreen({ setCurrentView }: RoleplayScreenProps) {
    return (
        <div className="roleplay-container">
            {/* Header */}
            <header className="rp-header">
                <button
                    className="icon-btn"
                    onClick={() => setCurrentView('home')}
                >
                    <ChevronLeft color="var(--text-main)" size={24} />
                </button>
                <h1 className="rp-title">Custom Scenarios</h1>
                <button className="icon-btn">
                    <Info color="#D4AF37" size={24} />
                </button>
            </header>

            <main className="rp-main">
                {/* Upload Section */}
                <div className="upload-section">
                    <button className="upload-btn group">
                        <div className="upload-bg-glow"></div>
                        <div className="upload-content">
                            <CloudUpload className="upload-icon" size={24} />
                            <span className="upload-text">Upload New Document</span>
                        </div>
                    </button>
                    <p className="upload-subtext">Supported: PDF, DOCX, TXT (Max 10MB)</p>
                </div>

                {/* List Section */}
                <div className="list-section">
                    <div className="list-header">
                        <h2 className="list-title">Your Knowledge Base</h2>
                        <span className="file-badge">3 Files</span>
                    </div>

                    {/* Card 1 */}
                    <div className="rp-glass-card group-card border-primary">
                        <div className="glow-circle glow-primary"></div>
                        <div className="card-top">
                            <div className="card-info">
                                <h3 className="doc-title title-primary">React_Architecture.pdf</h3>
                                <div className="doc-meta">
                                    <Calendar size={14} />
                                    <span>Oct 12, 2023</span>
                                </div>
                            </div>
                            <div className="icon-box icon-primary">
                                <FileText size={20} />
                            </div>
                        </div>

                        <div className="card-bottom">
                            <div className="tag-group">
                                <div className="tag tag-js">JS</div>
                                <div className="tag tag-ui">UI</div>
                            </div>
                            <button className="action-btn btn-primary neon-glow-primary">
                                <span>Start Session</span>
                                <Play size={16} fill="currentColor" />
                            </button>
                        </div>
                    </div>

                    {/* Card 2 */}
                    <div className="rp-glass-card group-card border-gold">
                        <div className="glow-circle glow-gold"></div>
                        <div className="card-top">
                            <div className="card-info">
                                <h3 className="doc-title title-gold">Business_Travel_Guide.pdf</h3>
                                <div className="doc-meta">
                                    <Calendar size={14} />
                                    <span>Sep 28, 2023</span>
                                </div>
                            </div>
                            <div className="icon-box icon-gold">
                                <FileText size={20} />
                            </div>
                        </div>

                        <div className="card-bottom">
                            <div className="tag-group">
                                <div className="tag tag-tr">TR</div>
                                <div className="tag tag-en">EN</div>
                            </div>
                            <button className="action-btn btn-gold neon-border-gold">
                                <span>Resume</span>
                                <CornerDownLeft size={16} />
                            </button>
                        </div>
                    </div>

                    {/* Card 3 */}
                    <div className="rp-glass-card group-card border-pink">
                        <div className="card-top">
                            <div className="card-info">
                                <h3 className="doc-title title-pink">Coffee_Shop_Dialogues.txt</h3>
                                <div className="doc-meta">
                                    <Calendar size={14} />
                                    <span>Aug 15, 2023</span>
                                </div>
                            </div>
                            <div className="icon-box icon-pink">
                                <FileText size={20} />
                            </div>
                        </div>

                        <div className="card-bottom">
                            <span className="last-practiced">Last practiced 2 days ago</span>
                            <button className="action-btn btn-ghost">
                                <span>History</span>
                                <History size={16} />
                            </button>
                        </div>
                    </div>

                </div>
            </main>

            {/* Decorative gradients */}
            <div className="bg-decor top-right"></div>
            <div className="bg-decor bottom-left"></div>
        </div>
    );
}
