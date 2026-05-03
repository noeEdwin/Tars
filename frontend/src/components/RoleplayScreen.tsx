import { useEffect, useState } from 'react';
import { ChevronLeft, Info, CloudUpload, Calendar, FileText, Play, X } from 'lucide-react';
import './RoleplayScreen.css';
import type { ViewState, SessionConfig } from '../App';
import { API_BASE } from '../apiConfig';

interface RoleplayScreenProps {
    setCurrentView: (view: ViewState) => void;
    startConversation: (config: SessionConfig) => void;
}

export default function RoleplayScreen({ setCurrentView, startConversation }: RoleplayScreenProps) {
    const [files, setFiles] = useState<string[]>([]);

    // Modal state
    const [modalFile, setModalFile] = useState<string | null>(null);
    const [userRole, setUserRole] = useState('Customer');
    const [tarsRole, setTarsRole] = useState('Barista');

    useEffect(() => {
        fetch(`${API_BASE}/roleplay/files?user_id=1`)
            .then(res => res.json())
            .then(data => {
                if (data.files) setFiles(data.files);
            })
            .catch(err => console.error('Error fetching roleplay files:', err));
    }, []);

    const openModal = (filename: string) => {
        setModalFile(filename);
        setUserRole('Customer');
        setTarsRole('Barista');
    };

    const handleConfirm = () => {
        if (!modalFile || !userRole.trim() || !tarsRole.trim()) return;
        startConversation({
            mode: 'tars_roleplay',
            filename: modalFile,
            user_role: userRole.trim(),
            tars_role: tarsRole.trim(),
        });
        setModalFile(null);
    };

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
                        <span className="file-badge">{files.length} Files</span>
                    </div>

                    {files.length === 0 && (
                        <div style={{ textAlign: 'center', opacity: 0.5, marginTop: '20px', fontSize: '14px' }}>
                            Loading your files...
                        </div>
                    )}

                    {files.map((file, idx) => {
                        const colors = ['primary', 'gold', 'pink'];
                        const color = colors[idx % colors.length];

                        return (
                            <div key={file} className={`rp-glass-card group-card border-${color}`}>
                                {color !== 'pink' && <div className={`glow-circle glow-${color}`}></div>}
                                <div className="card-top">
                                    <div className="card-info">
                                        <h3 className={`doc-title title-${color}`}>{file}</h3>
                                        <div className="doc-meta">
                                            <Calendar size={14} />
                                            <span>Recently Uploaded</span>
                                        </div>
                                    </div>
                                    <div className={`icon-box icon-${color}`}>
                                        <FileText size={20} />
                                    </div>
                                </div>

                                <div className="card-bottom">
                                    <div className="tag-group">
                                        <div className="tag tag-js">SCENARIO</div>
                                    </div>
                                    <button
                                        className={`action-btn btn-${color} neon-glow-${color}`}
                                        onClick={() => openModal(file)}
                                    >
                                        <span>Start Session</span>
                                        <Play size={16} fill="currentColor" />
                                    </button>
                                </div>
                            </div>
                        );
                    })}
                </div>
            </main>

            {/* Decorative gradients */}
            <div className="bg-decor top-right"></div>
            <div className="bg-decor bottom-left"></div>

            {/* Role entry modal */}
            {modalFile && (
                <div className="rp-modal-overlay" onClick={() => setModalFile(null)}>
                    <div className="rp-modal" onClick={e => e.stopPropagation()}>
                        <div className="rp-modal-header">
                            <h3 className="rp-modal-title">Set up roles</h3>
                            <button className="rp-modal-close" onClick={() => setModalFile(null)}>
                                <X size={18} />
                            </button>
                        </div>
                        <p className="rp-modal-file">Scenario: <strong>{modalFile}</strong></p>

                        <label className="rp-modal-label">Your character role</label>
                        <input
                            className="rp-modal-input"
                            value={userRole}
                            onChange={e => setUserRole(e.target.value)}
                            placeholder="e.g. Customer"
                            autoFocus
                        />

                        <label className="rp-modal-label">TARS character role</label>
                        <input
                            className="rp-modal-input"
                            value={tarsRole}
                            onChange={e => setTarsRole(e.target.value)}
                            placeholder="e.g. Barista"
                            onKeyDown={e => e.key === 'Enter' && handleConfirm()}
                        />

                        <button
                            className="rp-modal-confirm"
                            onClick={handleConfirm}
                            disabled={!userRole.trim() || !tarsRole.trim()}
                        >
                            <Play size={16} fill="currentColor" />
                            Start Session
                        </button>
                    </div>
                </div>
            )}
        </div>
    );
}
