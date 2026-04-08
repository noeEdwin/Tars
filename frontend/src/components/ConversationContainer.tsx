import { useEffect, useState, useCallback, useRef } from 'react';
import VoiceConversationScreen from './VoiceConversationScreen';
import ConversationScreen from './ConversationScreen';
import type { ViewState, SessionConfig } from '../App';
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
}

export default function ConversationContainer({ setCurrentView, sessionConfig }: ConversationContainerProps) {
    const { mode, filename, user_role, tars_role } = sessionConfig;
    const [subView, setSubView] = useState<'voice' | 'text'>('voice');

    // Shared State
    const [messages, setMessages] = useState<Message[]>([]);
    const [threadId, setThreadId] = useState('');
    const [conversationId, setConversationId] = useState(0);
    const [sessionReady, setSessionReady] = useState(false);
    const [isProcessing, setIsProcessing] = useState(false);
    const socketRef = useRef<WebSocket | null>(null);
    // Voice-specific state from backend
    const [latestAudioB64, setLatestAudioB64] = useState<string | null>(null);

    useEffect(() => {
        const startSession = async () => {
            const res = await fetch(`${API_BASE}/start_session`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ user_id: USER_ID, mode, filename, user_role, tars_role }),
            });
            const data = await res.json();
            setThreadId(data.thread_id);
            setConversationId(data.conversation_id);

            // Añadir el primer mensaje de Tars
            setMessages([{ id: Date.now().toString(), role: 'tars', text: data.tars_message }]);
            if (data.audio_b64) setLatestAudioB64(data.audio_b64);

            setSessionReady(true);
        };
        startSession();
    }, [mode]);

    // Start session once
    useEffect(() => {
        if (!sessionReady || !threadId) return;

        // Creamos la conexión
        const socket = new WebSocket(`${WS_BASE}/ws/${USER_ID}`);
        socketRef.current = socket;

        socket.onmessage = (event) => {
            const data = JSON.parse(event.data);

            if (data.type === 'tars_answer') {
                setMessages(prev => [...prev, {
                    id: Date.now().toString() + 't',
                    role: 'tars',
                    text: data.text
                }]);
                if (data.audio_b64) setLatestAudioB64(data.audio_b64);
                setIsProcessing(false);
            }

            if (data.type === 'error') {
                console.error("Error de Tars:", data.message);
                setIsProcessing(false);
            }
        };

        return () => {
            socket.close();
        };
    }, [sessionReady, threadId]);

    // --- Función para Interrumpir---
    const interruptTars = useCallback(() => {
        if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
            socketRef.current.send(JSON.stringify({ type: 'interrupt' }));
            setLatestAudioB64(null);
            setIsProcessing(false);
        }
    }, []);

    const sendMessage = useCallback(async (text: string) => {
        if (!text.trim() || !sessionReady || isProcessing) return;

        setIsProcessing(true);
        const userMsg: Message = { id: Date.now().toString(), role: 'user', text };
        setMessages(prev => [...prev, userMsg]);
        setLatestAudioB64(null);

        if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
            socketRef.current.send(JSON.stringify({
                type: 'chat',
                text: text,
                thread_id: threadId,
                conversation_id: conversationId,
                mode: mode
            }));
        }
    }, [sessionReady, isProcessing, threadId, conversationId, mode]);

    if (subView === 'voice') {
        return (
            <VoiceConversationScreen
                mode={mode}
                messages={messages}
                sessionReady={sessionReady}
                isProcessing={isProcessing}
                latestAudioB64={latestAudioB64}
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
            onInterrupt={interruptTars}
            onBack={() => setSubView('voice')} // Back goes to voice
        />
    );
}
