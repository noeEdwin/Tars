import { useEffect, useRef, useState, useCallback } from 'react';
import { ArrowLeft, Mic, MicOff, Send, Settings2 } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import type { Message } from '../../types/message';
import { parseTarsMessage } from '../../utils/messageParser';
import './ConversationScreen.css';

declare global {
    interface Window {
        SpeechRecognition: new () => SpeechRecognition;
        webkitSpeechRecognition: new () => SpeechRecognition;
    }
    interface SpeechRecognition extends EventTarget {
        lang: string;
        continuous: boolean;
        interimResults: boolean;
        start(): void;
        stop(): void;
        onresult: ((this: SpeechRecognition, ev: SpeechRecognitionEvent) => void) | null;
        onerror: ((this: SpeechRecognition, ev: Event) => void) | null;
        onend: ((this: SpeechRecognition, ev: Event) => void) | null;
    }
    interface SpeechRecognitionEvent extends Event {
        results: SpeechRecognitionResultList;
    }
    interface SpeechRecognitionResultList {
        readonly length: number;
        [index: number]: SpeechRecognitionResult;
    }
    interface SpeechRecognitionResult {
        readonly isFinal: boolean;
        [index: number]: SpeechRecognitionAlternative;
    }
    interface SpeechRecognitionAlternative {
        readonly transcript: string;
        readonly confidence: number;
    }
}

interface ConversationScreenProps {
    mode?: 'tars_normal' | 'tars_roleplay';
    messages: Message[];
    sessionReady: boolean;
    isProcessing: boolean;
    onSendMessage: (text: string) => void;
    onBack: () => void;
}

export default function ConversationScreen({ 
    mode = 'tars_normal',
    messages,
    sessionReady,
    isProcessing,
    onSendMessage,
    onBack
}: ConversationScreenProps) {
    const { t } = useTranslation();
    const [isListening, setIsListening] = useState(false);
    const [inputText, setInputText] = useState('');
    const [error, setError] = useState('');

    const [activeMenuId, setActiveMenuId] = useState<string | null>(null);
    const [showPinyin, setShowPinyin] = useState<Record<string, boolean>>({});
    const [showTranslation, setShowTranslation] = useState<Record<string, boolean>>({});
    const [isReplaying, setIsReplaying] = useState<Record<string, boolean>>({});
    const replayAudioRef = useRef<string[]>([]);
    const replayIndexRef = useRef(0);

    const bottomRef = useRef<HTMLDivElement>(null);
    const recogRef = useRef<SpeechRecognition | null>(null);

    const handleTogglePinyin = (id: string, e: React.MouseEvent) => {
        e.stopPropagation();
        setShowPinyin(prev => ({ ...prev, [id]: !prev[id] }));
    };

    const handleToggleTranslation = (id: string, e: React.MouseEvent) => {
        e.stopPropagation();
        setShowTranslation(prev => ({ ...prev, [id]: !prev[id] }));
    };

    const handleBubbleClick = (id: string, role: string) => {
        if (role === 'user') return;
        setActiveMenuId(prev => (prev === id ? null : id));
    };

    const replayTeachingAudio = (audio_b64: string[], msgId: string) => {
        if (isReplaying[msgId]) return;
        replayAudioRef.current = audio_b64;
        replayIndexRef.current = 0;
        setIsReplaying(prev => ({ ...prev, [msgId]: true }));
        playNextReplayChunk(msgId);
    };

    const playNextReplayChunk = (msgId: string) => {
        const idx = replayIndexRef.current;
        const queue = replayAudioRef.current;
        if (idx >= queue.length) {
            setIsReplaying(prev => ({ ...prev, [msgId]: false }));
            replayAudioRef.current = [];
            return;
        }
        const audio = new Audio(`data:audio/ogg;codecs=opus;base64,${queue[idx]}`);
        audio.play().catch(e => {
            console.error('Replay failed:', e);
            setIsReplaying(prev => ({ ...prev, [msgId]: false }));
        });
        audio.onended = () => {
            replayIndexRef.current = idx + 1;
            playNextReplayChunk(msgId);
        };
    };

    useEffect(() => {
        bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

    const handleSend = useCallback((text: string) => {
        if (!text.trim() || !sessionReady || isProcessing) return;
        onSendMessage(text);
        setInputText('');
    }, [sessionReady, isProcessing, onSendMessage]);

    const toggleListening = useCallback(() => {
        const SRClass = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (!SRClass) {
            setError(t('conversation.speechNotSupported'));
            return;
        }
        if (isListening) {
            recogRef.current?.stop();
            setIsListening(false);
            return;
        }
        const recog = new SRClass();
        recog.lang = 'en-US';
        recog.continuous = false;
        recog.interimResults = false;
        recog.onresult = (e: SpeechRecognitionEvent) => {
            const transcript = e.results[0][0].transcript;
            handleSend(transcript);
        };
        recog.onerror = () => setIsListening(false);
        recog.onend = () => setIsListening(false);
        recogRef.current = recog;
        recog.start();
        setIsListening(true);
    }, [isListening, handleSend, t]);

    return (
        <div className="conv-container">
            <header className="conv-header">
                <button className="conv-back-btn" onClick={onBack}>
                    <ArrowLeft size={22} color="var(--text-main)" />
                </button>
                <div className="conv-header-info">
                    <h1 className="conv-title">TARS</h1>
                    <span className={`conv-status ${sessionReady ? 'status-online' : 'status-loading'}`}>
                        {sessionReady ? (mode === 'tars_normal' ? t('conversation.normalModeActive') : t('conversation.roleplayModeActive')) : t('conversation.connecting')}
                    </span>
                </div>
                <div style={{ width: 40 }} />
            </header>

            <main className="conv-messages">
                {error && (
                    <div className="conv-error">{error}</div>
                )}
                {messages.map(m => {
                    const isTars = m.role === 'tars';
                    const parsed = isTars ? parseTarsMessage(m.text) : null;
                    const isActive = activeMenuId === m.id;

                    return (
                        <div key={m.id} className={`conv-bubble-row ${isTars ? 'row-tars' : 'row-user'}`}>
                            <div 
                                className={`conv-bubble ${isTars ? 'bubble-tars' : 'bubble-user'} ${isActive ? 'bubble-active' : ''}`}
                                onClick={() => handleBubbleClick(m.id, m.role)}
                            >
                                {isTars && parsed ? (
                                    <>
                                        <div className="conv-chinese">{parsed.chinese}</div>
                                        
                                        {isActive && (parsed.pinyin || parsed.translation) && (
                                            <div className="conv-toggles animated-fade-in">
                                                {parsed.pinyin && (
                                                    <button 
                                                        className={`toggle-btn ${showPinyin[m.id] ? 'btn-on' : ''}`}
                                                        onClick={(e) => handleTogglePinyin(m.id, e)}
                                                    >
                                                        {showPinyin[m.id] ? t('conversation.hidePinyin') : t('conversation.showPinyin')}
                                                    </button>
                                                )}
                                                {parsed.translation && (
                                                    <button 
                                                        className={`toggle-btn ${showTranslation[m.id] ? 'btn-on' : ''}`}
                                                        onClick={(e) => handleToggleTranslation(m.id, e)}
                                                    >
                                                        {showTranslation[m.id] ? t('conversation.hideTranslate') : t('conversation.showTranslate')}
                                                    </button>
                                                )}
                                                {m.isTeaching && m.audio_b64 && (
                                                    <button 
                                                        className={`toggle-btn ${isReplaying[m.id] ? 'btn-on' : ''}`}
                                                        onClick={(e) => {
                                                            e.stopPropagation();
                                                            replayTeachingAudio(m.audio_b64!, m.id);
                                                        }}
                                                        disabled={isReplaying[m.id]}
                                                    >
                                                        {isReplaying[m.id] ? t('conversation.replaying') : t('conversation.repeat')}
                                                    </button>
                                                )}
                                            </div>
                                        )}
                                        
                                        {showPinyin[m.id] && parsed.pinyin && (
                                            <div className="conv-pinyin animated-slide-down">{parsed.pinyin}</div>
                                        )}
                                        {showTranslation[m.id] && parsed.translation && (
                                            <div className="conv-translation animated-slide-down">{parsed.translation}</div>
                                        )}

                                        {parsed.explanation && (
                                            <div className="conv-explanation">{parsed.explanation}</div>
                                        )}
                                    </>
                                ) : (
                                    m.text
                                )}
                            </div>
                            {isTars && !isActive && (parsed?.pinyin || parsed?.translation) && (
                                <div className="conv-hint-icon">
                                    <Settings2 size={14} color="var(--text-muted)" />
                                </div>
                            )}
                        </div>
                    );
                })}
                {isProcessing && (
                    <div className="conv-bubble-row row-tars">
                        <div className="conv-bubble bubble-tars conv-typing">
                            <span /><span /><span />
                        </div>
                    </div>
                )}
                <div ref={bottomRef} />
            </main>

            <div className="conv-input-bar">
                <button
                    className={`conv-mic-btn ${isListening ? 'mic-active' : ''}`}
                    onClick={toggleListening}
                    disabled={!sessionReady || isProcessing}
                >
                    {isListening ? <MicOff size={22} /> : <Mic size={22} />}
                </button>
                <input
                    className="conv-text-input"
                    type="text"
                    placeholder={t('conversation.placeholder')}
                    value={inputText}
                    onChange={e => setInputText(e.target.value)}
                    onKeyDown={e => e.key === 'Enter' && handleSend(inputText)}
                    disabled={!sessionReady || isProcessing}
                />
                <button
                    className="conv-send-btn"
                    onClick={() => handleSend(inputText)}
                    disabled={!inputText.trim() || !sessionReady || isProcessing}
                >
                    <Send size={20} />
                </button>
            </div>
        </div>
    );
}
