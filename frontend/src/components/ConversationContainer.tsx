import { useEffect, useState, useCallback } from 'react';
import VoiceConversationScreen from './VoiceConversationScreen';
import ConversationScreen from './ConversationScreen';
import type { ViewState, SessionConfig } from '../App';

const API_BASE = `http://${window.location.hostname}:8000`;
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
    
    // Voice-specific state from backend
    const [latestAudioB64, setLatestAudioB64] = useState<string | null>(null);

    // Start session once
    useEffect(() => {
        const startSession = async () => {
            try {
                const res = await fetch(`${API_BASE}/start_session`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ 
                        user_id: USER_ID, 
                        mode,
                        filename,
                        user_role,
                        tars_role
                    }),
                });
                if (!res.ok) throw new Error('Backend error');
                const data = await res.json();
                
                setThreadId(data.thread_id);
                setConversationId(data.conversation_id);
                
                // Add initial message
                setMessages([{ 
                    id: Date.now().toString(), 
                    role: 'tars', 
                    text: data.tars_message 
                }]);
                
                if (data.audio_b64) {
                    setLatestAudioB64(data.audio_b64);
                }
                
                setSessionReady(true);
            } catch (err) {
                console.error(err);
                setMessages([{ 
                    id: 'init-err', 
                    role: 'tars', 
                    text: 'Connection failed. Make sure backend is running.' 
                }]);
            }
        };
        startSession();
    }, [mode]);

    // Send Message Logic
    const sendMessage = useCallback(async (text: string) => {
        if (!text.trim() || !sessionReady || isProcessing) return;
        
        setIsProcessing(true);
        // Optimistically add user text
        const userMsg: Message = { id: Date.now().toString(), role: 'user', text };
        setMessages(prev => [...prev, userMsg]);
        setLatestAudioB64(null); // Clear previous audio

        try {
            const res = await fetch(`${API_BASE}/chat`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    user_id: USER_ID,
                    thread_id: threadId,
                    conversation_id: conversationId,
                    user_input: text,
                    mode,
                }),
            });
            if (!res.ok) throw new Error('API Error');
            const data = await res.json();
            
            // Add tars response
            setMessages(prev => [...prev, { 
                id: Date.now().toString() + 't', 
                role: 'tars', 
                text: data.tars_message 
            }]);
            
            if (data.audio_b64) {
                setLatestAudioB64(data.audio_b64);
            }
        } catch (err) {
            console.error(err);
            setMessages(prev => [...prev, { 
                id: 'err-' + Date.now(), 
                role: 'tars', 
                text: '⚠️ Network error.' 
            }]);
        } finally {
            setIsProcessing(false);
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
            onBack={() => setSubView('voice')} // Back goes to voice
        />
    );
}
