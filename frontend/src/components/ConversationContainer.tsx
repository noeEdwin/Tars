import { useEffect, useState, useCallback, useRef } from 'react';
import VoiceConversationScreen from './VoiceConversationScreen';
import ConversationScreen from './ConversationScreen';
import type { ViewState, SessionConfig } from '../App';
import type { PreWarmedSession } from '../utils/usePreWarmSession';
import { API_BASE, WS_BASE } from '../apiConfig';

const USER_ID = 1;

export interface Message {
    id: string;
    role: 'tars' | 'user';
    text: string;
}

interface ConversationContainerProps {
    setCurrentView: (view: ViewState) => void;
    sessionConfig: SessionConfig;
    /** If provided, skip cold-start and reuse this pre-warmed session */
    preWarmedSession?: PreWarmedSession | null;
    /** Called after the pre-warmed session is "consumed" so parent can reset */
    onSessionConsumed?: () => void;
}

export default function ConversationContainer({
    setCurrentView,
    sessionConfig,
    preWarmedSession,
    onSessionConsumed,
}: ConversationContainerProps) {
    const { mode, filename, user_role, tars_role } = sessionConfig;
    const [subView, setSubView] = useState<'voice' | 'text'>('voice');

    // Shared State
    const [messages, setMessages] = useState<Message[]>([]);
    const [threadId, setThreadId] = useState('');
    const [conversationId, setConversationId] = useState(0);
    const [sessionReady, setSessionReady] = useState(false);
    const [isProcessing, setIsProcessing] = useState(false);
    const socketRef = useRef<WebSocket | null>(null);
    const [audioQueue, setAudioQueue] = useState<string[]>([]);
    const [currentAudioIndex, setCurrentAudioIndex] = useState(0);

    // ── FAST PATH: consume the pre-warmed session ──────────────────────────
    useEffect(() => {
        if (!preWarmedSession) return;

        socketRef.current = preWarmedSession.socket;
        setThreadId(preWarmedSession.threadId);
        setConversationId(preWarmedSession.conversationId);
        setCurrentAudioIndex(preWarmedSession.currentAudioIndex);

        // Inject the preload message as the first TARS bubble (if any)
        const pm = preWarmedSession.preloadMessage;
        const initialMessages: Message[] = pm?.text
            ? [{ id: 'preload-0', role: 'tars', text: pm.text }, ...preWarmedSession.messages]
            : [...preWarmedSession.messages];

        setMessages(initialMessages);

        // Pre-load audio queue: put preload audio first, then buffered websocket audio
        const initialAudio: string[] = [
            ...(pm?.audio_b64 ? [pm.audio_b64] : []),
            ...preWarmedSession.audioQueue,
        ];
        setAudioQueue(initialAudio);
        setIsProcessing(preWarmedSession.isProcessing && initialAudio.length === 0);
        setSessionReady(true);

        // Re-attach onmessage so we keep receiving future events
        preWarmedSession.socket.onmessage = (event) => {
            const data = JSON.parse(event.data);

            if (data.type === 'token') {
                setMessages(prev => {
                    const lastMsg = prev[prev.length - 1];
                    if (lastMsg && lastMsg.role === 'tars') {
                        return [...prev.slice(0, -1), { ...lastMsg, text: lastMsg.text + data.text }];
                    }
                    return [...prev, { id: Date.now().toString() + 't', role: 'tars', text: data.text }];
                });
            }

            if (data.type === 'tars_answer' || data.type === 'audio_chunk') {
                if (data.audio_b64) setAudioQueue(prev => [...prev, data.audio_b64]);
            }

            if (data.type === 'tars_answer_end') setIsProcessing(false);
            if (data.type === 'error') {
                console.error('Tars error:', data.message);
                setIsProcessing(false);
            }
        };

        onSessionConsumed?.();
    // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []); // Run once on mount — preWarmedSession is the initial value

    // ── COLD PATH: no pre-warm → start from scratch ────────────────────────
    useEffect(() => {
        if (preWarmedSession) return; // already handled above

        const startSession = async () => {
            const res = await fetch(`${API_BASE}/start_session`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ user_id: USER_ID, mode, filename, user_role, tars_role }),
            });
            const data = await res.json();
            setThreadId(data.thread_id);
            setConversationId(data.conversation_id);
            setSessionReady(true);
        };
        startSession();
    // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [mode]);

    // Start WebSocket once session is ready (cold path only)
    useEffect(() => {
        if (preWarmedSession) return;
        if (!sessionReady || !threadId) return;

        const socket = new WebSocket(`${WS_BASE}/ws/${USER_ID}`);
        socketRef.current = socket;

        socket.onopen = () => {
            socket.send(JSON.stringify({
                type: 'init_session',
                thread_id: threadId,
                conversation_id: conversationId,
                mode,
            }));
            setIsProcessing(true);
        };

        socket.onmessage = (event) => {
            const data = JSON.parse(event.data);

            if (data.type === 'token') {
                setMessages(prev => {
                    const lastMsg = prev[prev.length - 1];
                    if (lastMsg && lastMsg.role === 'tars') {
                        return [...prev.slice(0, -1), { ...lastMsg, text: lastMsg.text + data.text }];
                    }
                    return [...prev, { id: Date.now().toString() + 't', role: 'tars', text: data.text }];
                });
            }

            if (data.type === 'tars_answer' || data.type === 'audio_chunk') {
                if (data.audio_b64) setAudioQueue(prev => [...prev, data.audio_b64]);
            }

            if (data.type === 'tars_answer_end') setIsProcessing(false);
            if (data.type === 'error') {
                console.error('Tars error:', data.message);
                setIsProcessing(false);
            }
        };

        return () => { socket.close(); };
    }, [sessionReady, threadId]);

    // ── Interrupt ──────────────────────────────────────────────────────────
    const interruptTars = useCallback(() => {
        if (socketRef.current?.readyState === WebSocket.OPEN) {
            socketRef.current.send(JSON.stringify({ type: 'interrupt' }));
            setAudioQueue([]);
            setCurrentAudioIndex(0);
            setIsProcessing(false);
        }
    }, []);

    // ── Send Message ───────────────────────────────────────────────────────
    const sendMessage = useCallback(async (text: string) => {
        if (!text.trim() || !sessionReady || isProcessing) return;

        setIsProcessing(true);
        const userMsg: Message = { id: Date.now().toString(), role: 'user', text };
        setMessages(prev => [...prev, userMsg]);
        setAudioQueue([]);
        setCurrentAudioIndex(0);

        if (socketRef.current?.readyState === WebSocket.OPEN) {
            socketRef.current.send(JSON.stringify({
                type: 'chat',
                text,
                thread_id: threadId,
                conversation_id: conversationId,
                mode,
            }));
        }
    }, [sessionReady, isProcessing, threadId, conversationId, mode]);

    // ── Cleanup ────────────────────────────────────────────────────────────
    useEffect(() => {
        return () => {
            if (!preWarmedSession) socketRef.current?.close();
        };
    }, []);

    if (subView === 'voice') {
        return (
            <VoiceConversationScreen
                mode={mode}
                messages={messages}
                sessionReady={sessionReady}
                isProcessing={isProcessing}
                audioQueue={audioQueue}
                currentAudioIndex={currentAudioIndex}
                setCurrentAudioIndex={setCurrentAudioIndex}
                onSendMessage={sendMessage}
                onInterrupt={interruptTars}
                onBack={() => setCurrentView('home')}
                onSwitchToText={() => setSubView('text')}
            />
        );
    }

    return (
        <ConversationScreen
            mode={mode}
            messages={messages}
            sessionReady={sessionReady}
            isProcessing={isProcessing}
            onSendMessage={sendMessage}
            onBack={() => setSubView('voice')}
        />
    );
}
