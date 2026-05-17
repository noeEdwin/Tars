import { useEffect, useState, useRef } from 'react';
import { ChevronLeft, Info, CloudUpload, Calendar, Play, X, Trash2 } from 'lucide-react';
import './RoleplayScreen.css';
import { API_BASE } from '../../apiConfig';
import { useAuthStore } from '../../stores/authStore';
import { useSessionStore } from '../../stores/sessionStore';

export default function RoleplayScreen() {
    const [files, setFiles] = useState<string[]>([]);
    const [isUploading, setIsUploading] = useState(false);

    const [modalFile, setModalFile] = useState<string | null>(null);
    const [userRole, setUserRole] = useState('');
    const [tarsRole, setTarsRole] = useState('');
    const [fileToDelete, setFileToDelete] = useState<string | null>(null);

    const token = useAuthStore((s) => s.token);
    const setView = useSessionStore((s) => s.setView);
    const prepareRoleplaySession = useSessionStore((s) => s.prepareRoleplaySession);

    const confirmDelete = async () => {
        if (!fileToDelete) return;

        try {
            const response = await fetch(`${API_BASE}/roleplay/files/${encodeURIComponent(fileToDelete)}`, {
                method: 'DELETE',
                headers: { 'Authorization': `Bearer ${token}` },
            });

            if (response.ok) {
                setFiles(prev => prev.filter(f => f !== fileToDelete));
            }
        } catch (error) {
            console.error("Error al eliminar:", error);
        } finally {
            setFileToDelete(null);
        }
    };

    const fileInputRef = useRef<HTMLInputElement>(null);

    const handleUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
        const file = event.target.files?.[0];
        if (!file) return;

        setIsUploading(true);
        const formData = new FormData();
        formData.append("file", file);

        try {
            const response = await fetch(`${API_BASE}/roleplay/upload`, {
                method: 'POST',
                headers: { 'Authorization': `Bearer ${token}` },
                body: formData,
            });

            if (response.ok) {
                setFiles(prev => [file.name, ...prev]);
            } else {
                console.error("Error en el servidor");
            }
        } catch (error) {
            console.error("Error de conexión:", error);
        } finally {
            setIsUploading(false);
            if (fileInputRef.current) fileInputRef.current.value = '';
        }
    };

    useEffect(() => {
        fetch(`${API_BASE}/roleplay/files`, {
            headers: { 'Authorization': `Bearer ${token}` },
        })
            .then(res => res.json())
            .then(data => {
                if (data.files) setFiles(data.files);
            })
            .catch(err => console.error('Error fetching roleplay files:', err));
    }, [token]);

    const openModal = (filename: string) => {
        setModalFile(filename);
        setUserRole('');
        setTarsRole('');
    };

    const handleConfirm = () => {
        if (!modalFile || !userRole.trim() || !tarsRole.trim()) return;
        prepareRoleplaySession({
            mode: 'tars_roleplay',
            filename: modalFile,
            user_role: userRole.trim(),
            tars_role: tarsRole.trim(),
        });
        setModalFile(null);
    };

    return (
        <div className="roleplay-container">
            <header className="rp-header">
                <button
                    className="icon-btn"
                    onClick={() => setView('home')}
                >
                    <ChevronLeft color="var(--text-main)" size={24} />
                </button>
                <h1 className="rp-title">Custom Scenarios</h1>
                <button className="icon-btn">
                    <Info color="#D4AF37" size={24} />
                </button>
            </header>

            <main className="rp-main">
                <div className="upload-section">
                    <input
                        type="file"
                        ref={fileInputRef}
                        style={{ display: 'none' }}
                        accept=".pdf,.docx,.txt"
                        onChange={handleUpload}
                    />

                    <button
                        className={`upload-btn group ${isUploading ? 'opacity-70 cursor-not-allowed' : ''}`}
                        onClick={() => !isUploading && fileInputRef.current?.click()}
                        disabled={isUploading}
                    >
                        <div className="upload-bg-glow"></div>
                        <div className="upload-content">
                            {isUploading ? (
                                <>
                                    <div className="animate-spin mr-2">⏳</div>
                                    <span className="upload-text">Analizando documento...</span>
                                </>
                            ) : (
                                <>
                                    <CloudUpload className="upload-icon" size={24} />
                                    <span className="upload-text">Upload New Document</span>
                                </>
                            )}
                        </div>
                    </button>
                </div>

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
                                    <button
                                        className={`icon-box icon-${color} hover:bg-red-600 transition-all cursor-pointer z-10`}
                                        onClick={(e) => {
                                            e.stopPropagation();
                                            setFileToDelete(file);
                                        }}
                                        title="Eliminar documento"
                                        style={{ border: 'none', background: 'transparent' }}
                                    >
                                        <Trash2 size={20} />
                                    </button>
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

            <div className="bg-decor top-right"></div>
            <div className="bg-decor bottom-left"></div>

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

            {fileToDelete && (
                <div className="rp-modal-overlay" onClick={() => setFileToDelete(null)}>
                    <div className="rp-modal border-pink" onClick={e => e.stopPropagation()}>
                        <div className="rp-modal-header">
                            <h3 className="rp-modal-title text-pink">¿Eliminar escenario?</h3>
                            <button className="rp-modal-close" onClick={() => setFileToDelete(null)}>
                                <X size={18} />
                            </button>
                        </div>

                        <p className="rp-modal-file">
                            Estás a punto de borrar <strong>{fileToDelete}</strong>.
                            Esta acción eliminará también los personajes asociados en Supabase.
                        </p>

                        <div className="flex gap-4 mt-6">
                            <button
                                className="rp-modal-confirm bg-gray-700 flex-1"
                                onClick={() => setFileToDelete(null)}
                            >
                                Cancelar
                            </button>
                            <button
                                className="rp-modal-confirm bg-red-600 flex-1 shadow-[0_0_15px_rgba(220,38,38,0.4)]"
                                onClick={confirmDelete}
                            >
                                Eliminar
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
