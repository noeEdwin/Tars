import { useEffect, useRef, useState } from 'react';
import type { Message } from './ConversationContainer';
import { parseTarsMessage } from '../utils/messageParser';
import { API_BASE } from '../apiConfig';
import './VoiceConversationScreen.css';

type UIState = 'idle' | 'listening' | 'speaking';

interface VoiceScreenProps {
    mode?: 'tars_normal' | 'tars_roleplay';
    messages: Message[];
    sessionReady: boolean;
    isProcessing: boolean;
    audioQueue: string[];
    currentAudioIndex: number;
    setCurrentAudioIndex: React.Dispatch<React.SetStateAction<number>>;
    onSendMessage: (text: string) => void;
    onBack: () => void;
    onSwitchToText: () => void;
    onInterrupt: () => void;
}

export default function VoiceConversationScreen({
    mode = 'tars_normal',
    messages,
    sessionReady,
    isProcessing,
    audioQueue,
    currentAudioIndex,
    setCurrentAudioIndex,
    onSendMessage,
    onBack,
    onSwitchToText,
    onInterrupt
}: VoiceScreenProps) {
    const [uiState, setUiState] = useState<UIState>('idle');
    const [interimText, setInterimText] = useState('');
    const [isTranscribing, setIsTranscribing] = useState(false);

    const mediaRecorderRef = useRef<MediaRecorder | null>(null);
    const audioChunksRef = useRef<BlobPart[]>([]);
    const streamRef = useRef<MediaStream | null>(null);
    const audioRef = useRef<HTMLAudioElement | null>(null);

    // Derive tarsSubtitle from messages
    const tarsMessages = messages.filter(m => m.role === 'tars');
    const rawSubtitle = tarsMessages.length > 0 ? tarsMessages[tarsMessages.length - 1].text : '';
    const tarsSubtitle = rawSubtitle ? parseTarsMessage(rawSubtitle).chinese : '';

    const pendingPlayRef = useRef(false);
    // Mirror queue and index in refs so tryPlayCurrent always reads fresh values
    // even when called from a stale closure (e.g. setAudioRef callback on mount)
    const audioQueueRef = useRef<string[]>(audioQueue);
    const currentAudioIndexRef = useRef<number>(currentAudioIndex);
    useEffect(() => { audioQueueRef.current = audioQueue; }, [audioQueue]);
    useEffect(() => { currentAudioIndexRef.current = currentAudioIndex; }, [currentAudioIndex]);

    // Plays the current chunk if the audio element is ready
    const tryPlayCurrent = () => {
        const el = audioRef.current;
        const queue = audioQueueRef.current;
        const idx   = currentAudioIndexRef.current;
        if (!el || queue.length === 0 || queue.length <= idx) return;
        if (uiState === 'speaking' && !el.paused && !el.ended) return; // already playing

        el.src = `data:audio/ogg;codecs=opus;base64,${queue[idx]}`;
        setUiState('speaking');
        el.play().catch(e => console.error('Audio playback failed:', e));
        pendingPlayRef.current = false;
    };

    // Callback ref — fires the instant <audio> is mounted in the DOM
    const setAudioRef = (el: HTMLAudioElement | null) => {
        audioRef.current = el;
        if (el && pendingPlayRef.current) {
            tryPlayCurrent();
        }
    };

    // Handle Audio Queue
    useEffect(() => {
        // Queue emptied (e.g. interrupt) → stop
        if (audioQueue.length === 0) {
            if (uiState === 'speaking') setUiState('idle');
            return;
        }

        if (audioRef.current) {
            tryPlayCurrent();
        } else {
            // audioRef not mounted yet — flag it so the callback ref triggers play
            pendingPlayRef.current = true;
        }
    }, [audioQueue, currentAudioIndex]); // eslint-disable-line react-hooks/exhaustive-deps

    // Track processing state cleanly
    useEffect(() => {
        if (isProcessing && uiState !== 'listening') {
            setInterimText('');
        }
    }, [isProcessing, uiState]);

    // ── Pointer Handlers for Holding Mic ────────────────────────────────────
    const handlePointerDown = async (e: React.PointerEvent<HTMLDivElement>) => {
        e.preventDefault();
        (e.target as HTMLElement).setPointerCapture(e.pointerId);
        // 1. Detener audio actual y avisar al backend 
        if (audioRef.current) {
            audioRef.current.pause();
            audioRef.current.currentTime = 0; // Reinicia el audio
        }
        onInterrupt();
        setUiState('idle');

        // 2. Desbloqueo de audio para Mobile 
        // Solo lo hacemos si el src está vacío o es el silencio inicial
        if (audioRef.current && (audioRef.current.src === '' || audioRef.current.src.includes('base64'))) {
            audioRef.current.src = 'data:audio/wav;base64,UklGRigAAABXQVZFZm10IBIAAAABAAEARKwAAIhYAQACABAAAABkYXRhAgAAAAEA';
            audioRef.current.play().then(() => audioRef.current?.pause()).catch(() => { });
        }

        if (!sessionReady || isProcessing || isTranscribing) return;

        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            streamRef.current = stream;

            const mediaRecorder = new MediaRecorder(stream);
            mediaRecorderRef.current = mediaRecorder;
            audioChunksRef.current = [];

            mediaRecorder.ondataavailable = (event) => {
                if (event.data.size > 0) {
                    audioChunksRef.current.push(event.data);
                }
            };

            mediaRecorder.start();
            setUiState('listening');
            setInterimText('Listening...');
        } catch (err) {
            console.error('Microphone access denied or error:', err);
            alert('Microphone access is required to speak to Tars.');
            setUiState('idle');
        }
    };

    const handlePointerUp = (e: React.PointerEvent<HTMLDivElement>) => {
        e.preventDefault();
        (e.target as HTMLElement).releasePointerCapture(e.pointerId);
        if (uiState !== 'listening') return;

        if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
            mediaRecorderRef.current.onstop = async () => {
                // Stop all tracks to release mic
                if (streamRef.current) {
                    streamRef.current.getTracks().forEach(track => track.stop());
                    streamRef.current = null;
                }

                // Dynamically handle MIME type for Safari/iOS support
                const mimeType = mediaRecorderRef.current?.mimeType || 'audio/webm';
                let ext = 'webm';
                if (mimeType.includes('mp4') || mimeType.includes('m4a')) ext = 'm4a';
                else if (mimeType.includes('ogg')) ext = 'ogg';
                else if (mimeType.includes('wav')) ext = 'wav';

                const audioBlob = new Blob(audioChunksRef.current, { type: mimeType });

                setIsTranscribing(true);
                setUiState('idle');

                try {
                    const formData = new FormData();
                    formData.append('audio', audioBlob, `voice_record.${ext}`);

                    const response = await fetch(`${API_BASE}/stt`, {
                        method: 'POST',
                        body: formData,
                    });

                    if (!response.ok) {
                        throw new Error('STT request failed');
                    }

                    const data = await response.json();

                    if (data.detail) {
                        throw new Error(data.detail);
                    }

                    const text = data.text;

                    if (text && text.trim()) {
                        onSendMessage(text);
                    } else {
                        setInterimText('Could not hear anything clearly.');
                        setTimeout(() => setInterimText(''), 3000);
                    }
                } catch (error: any) {
                    console.error('STT error:', error);
                    setInterimText(`Connection error: ${error.message || 'Server failed'}`);
                    setTimeout(() => setInterimText(''), 4000);
                } finally {
                    setIsTranscribing(false);
                }
            };

            mediaRecorderRef.current.stop();
        } else {
            setUiState('idle');
            setInterimText('');
        }
    };

    return (
        <div className="voice-screen-body">
            <audio 
                ref={setAudioRef} 
                style={{ display: 'none' }} 
                onEnded={() => {
                    const nextIndex = currentAudioIndex + 1;
                    if (nextIndex < audioQueue.length) {
                        setCurrentAudioIndex(nextIndex);
                    } else {
                        setCurrentAudioIndex(nextIndex);
                        setUiState('idle'); // Finalizó de hablar todos los chunks
                    }
                }}
            />
            <div className="ambient-glow"></div>

            <main className="voice-main">

                {/* Header */}
                <header className="voice-header">
                    <button
                        onClick={onBack}
                        className="voice-back-btn"
                    >
                        &larr; Back
                    </button>
                    <h1 className="voice-title">
                        Tài Sī · {mode === 'tars_normal' ? 'Focus' : 'Roleplay'}
                    </h1>
                </header>

                {/* Voice Interface */}
                <section className="voice-interface">
                    <div className={`voice-mic-wrapper ${uiState === 'listening' ? 'listening' : ''}`}>

                        {/* Outer Glow Ring */}
                        <div
                            onPointerDown={handlePointerDown}
                            onPointerUp={handlePointerUp}
                            onPointerCancel={handlePointerUp}
                            style={{ touchAction: 'none' }}
                            className={`voice-mic-ring ${uiState === 'listening' ? 'listening' : 'idle'}`}
                        >
                            <div className="inner-circle">
                                {/* Microphone Icon */}
                                <svg
                                    className={`voice-mic-icon ${uiState === 'listening' ? 'listening' : ''}`}
                                    fill="none"
                                    stroke="currentColor"
                                    strokeLinecap="round"
                                    strokeLinejoin="round"
                                    strokeWidth="1.5"
                                    viewBox="0 0 24 24"
                                >
                                    <path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z"></path>
                                    <path d="M19 10v2a7 7 0 0 1-14 0v-2"></path>
                                    <line x1="12" x2="12" y1="19" y2="22"></line>
                                </svg>
                            </div>
                        </div>
                    </div>

                    {/* Subtitles Area */}
                    <div className="subtitles-container">
                        {uiState === 'listening' && (
                            <p className="voice-interim">
                                {interimText}
                            </p>
                        )}
                        {isTranscribing && (
                            <p className="voice-processing">
                                Transcribing audio...
                            </p>
                        )}
                        {isProcessing && !isTranscribing && (
                            <p className="voice-processing">
                                Processing...
                            </p>
                        )}
                        {(uiState === 'speaking' || uiState === 'idle') && !isProcessing && !isTranscribing && tarsSubtitle && (
                            <div className="voice-subtitle">
                                {tarsSubtitle}
                            </div>
                        )}
                    </div>
                </section>

                {/* Controls */}
                <footer className="voice-footer">
                    <button
                        className="voice-history-btn"
                        title="Transcript History"
                        onClick={onSwitchToText}
                    >
                        <svg fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                            <path d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" strokeLinecap="round" strokeLinejoin="round"></path>
                        </svg>
                    </button>
                </footer>
            </main>
        </div>
    );
}
