import { useEffect, useState, useCallback, useRef } from 'react';
import { useTranslation } from 'react-i18next';
import VoiceConversationScreen from './VoiceConversationScreen';
import ConversationScreen from './ConversationScreen';
import type { ViewState, SessionConfig } from '../App';
import type { PreWarmedSession } from '../utils/usePreWarmSession';
import { API_BASE, WS_BASE } from '../apiConfig';

function getUserId(): number {
    const stored = localStorage.getItem('tars_user_id');
    return stored ? parseInt(stored, 10) : 1;
}

export interface Message {
    id: string;
    role: 'tars' | 'user';
    text: string;
    audio_b64?: string[];
    isTeaching?: boolean;
}

interface ConversationContainerProps {
    setCurrentView: (view: ViewState) => void;
    sessionConfig: SessionConfig;
    preWarmedSession?: PreWarmedSession | null;
    onSessionConsumed?: () => void;
}

export default function ConversationContainer({
    setCurrentView,
    sessionConfig,
    preWarmedSession,
    onSessionConsumed,
}: ConversationContainerProps) {
    const { t } = useTranslation();
    const { mode, filename, user_role, tars_role } = sessionConfig;
    const [subView, setSubView] = useState<'voice' | 'text'>('voice');

    const [messages, setMessages] = useState<Message[]>([]);
    const [threadId, setThreadId] = useState('');
    const [conversationId, setConversationId] = useState(0);
    const [sessionReady, setSessionReady] = useState(false);
    const [isProcessing, setIsProcessing] = useState(false);
    const socketRef = useRef<WebSocket | null>(null);
    const [audioQueue, setAudioQueue] = useState<string[]>([]);
    const [currentAudioIndex, setCurrentAudioIndex] = useState(0);
    const currentTeachingMsgId = useRef<string | null>(null);

    useEffect(() => {
        if (!preWarmedSession) return;

        socketRef.current = preWarmedSession.socket;
        setThreadId(preWarmedSession.threadId);
        setConversationId(preWarmedSession.conversationId);
        setCurrentAudioIndex(preWarmedSession.currentAudioIndex);

        const pm = preWarmedSession.preloadMessage;
        const initialMessages: Message[] = pm?.text
            ? [{ id: 'preload-0', role: 'tars', text: pm.text }, ...preWarmedSession.messages]
            : [...preWarmedSession.messages];

        setMessages(initialMessages);

        const initialAudio = [
            ...(pm?.audio_b64 ? [pm.audio_b64] : []),
            ...preWarmedSession.audioQueue,
        ];
        setAudioQueue(initialAudio);

        setIsProcessing(pm ? false : preWarmedSession.isProcessing);
        setSessionReady(true);

        preWarmedSession.socket.onmessage = (event) => {
            const data = JSON.parse(event.data);

            if (data.type === 'token') {
                setMessages(prev => {
                    const lastMsg = prev[prev.length - 1];
                    if (lastMsg && lastMsg.role === 'tars') {
                        const updatedText = lastMsg.text + data.text;
                        const isTeaching = updatedText.includes('**');
                        return [...prev.slice(0, -1), { ...lastMsg, text: updatedText, isTeaching: isTeaching || lastMsg.isTeaching }];
                    }
                    
                    const newMsg: Message = { id: Date.now().toString() + 't', role: 'tars', text: data.text, isTeaching: data.text.includes('**') };
                    if (newMsg.isTeaching) {
                        currentTeachingMsgId.current = newMsg.id;
                    }
                    return [...prev, newMsg];
                });
            }

            if (data.type === 'tars_answer' || data.type === 'audio_chunk') {
                if (data.audio_b64) {
                    setAudioQueue(prev => [...prev, data.audio_b64]);
                    if (currentTeachingMsgId.current) {
                        setMessages(prev => prev.map(msg => 
                            msg.id === currentTeachingMsgId.current 
                                ? { ...msg, audio_b64: [...(msg.audio_b64 || []), data.audio_b64] }
                                : msg
                        ));
                    }
                }
            }

            if (data.type === 'tars_answer_end') {
                setIsProcessing(false);
                setTimeout(() => { currentTeachingMsgId.current = null; }, 5000);
            }
            if (data.type === 'error') {
                console.error(t('conversationContainer.error'), data.message);
                setIsProcessing(false);
            }
        };

        setTimeout(() => onSessionConsumed?.(), 0);
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    useEffect(() => {
        if (preWarmedSession) return;

        const startSession = async () => {
            const res = await fetch(`${API_BASE}/start_session`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ user_id: getUserId(), mode, filename, user_role, tars_role }),
            });
            const data = await res.json();
            setThreadId(data.thread_id);
            setConversationId(data.conversation_id);
            setSessionReady(true);
        };
        startSession();
    }, [mode]);

    useEffect(() => {
        if (preWarmedSession) return;
        if (!sessionReady || !threadId) return;

        const socket = new WebSocket(`${WS_BASE}/ws/${getUserId()}`);
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
                        const updatedText = lastMsg.text + data.text;
                        const isTeaching = updatedText.includes('**');
                        if (isTeaching && !lastMsg.isTeaching) {
                            currentTeachingMsgId.current = lastMsg.id;
                        }
                        return [...prev.slice(0, -1), { ...lastMsg, text: updatedText, isTeaching: isTeaching || lastMsg.isTeaching }];
                    }
                    const newMsg: Message = { id: Date.now().toString() + 't', role: 'tars', text: data.text, isTeaching: data.text.includes('**') };
                    if (newMsg.isTeaching) {
                        currentTeachingMsgId.current = newMsg.id;
                    }
                    return [...prev, newMsg];
                });
            }

            if (data.type === 'tars_answer' || data.type === 'audio_chunk') {
                if (data.audio_b64) {
                    setAudioQueue(prev => [...prev, data.audio_b64]);
                    if (currentTeachingMsgId.current) {
                        setMessages(prev => prev.map(msg => 
                            msg.id === currentTeachingMsgId.current 
                                ? { ...msg, audio_b64: [...(msg.audio_b64 || []), data.audio_b64] }
                                : msg
                        ));
                    }
                }
            }

            if (data.type === 'tars_answer_end') {
                setIsProcessing(false);
                setTimeout(() => { currentTeachingMsgId.current = null; }, 5000);
            }
            if (data.type === 'error') {
                console.error(t('conversationContainer.error'), data.message);
                setIsProcessing(false);
            }
        };

        return () => { socket.close(); };
    }, [sessionReady, threadId]);

    const interruptTars = useCallback(() => {
        if (socketRef.current?.readyState === WebSocket.OPEN) {
            socketRef.current.send(JSON.stringify({ type: 'interrupt' }));
            setAudioQueue([]);
            setCurrentAudioIndex(0);
            setIsProcessing(false);
        }
    }, []);

    const sendMessage = useCallback(async (text: string) => {
        if (!text.trim() || !sessionReady || isProcessing) return;

        setIsProcessing(true);
        const userMsg: Message = { id: Date.now().toString(), role: 'user', text };
        setMessages(prev => [...prev, userMsg]);
        setAudioQueue([]);
        setCurrentAudioIndex(0);

        const doSend = (socket: WebSocket) => {
            socket.send(JSON.stringify({
                type: 'chat',
                text,
                thread_id: threadId,
                conversation_id: conversationId,
                mode,
            }));
        };

        const currentSocket = socketRef.current;

        if (currentSocket && currentSocket.readyState === WebSocket.OPEN) {
            doSend(currentSocket);
        } else {
            console.warn(t('conversationContainer.socketReconnecting'));
            const newSocket = new WebSocket(`${WS_BASE}/ws/${getUserId()}`);
            socketRef.current = newSocket;

            newSocket.onmessage = (event) => {
                const data = JSON.parse(event.data);
                if (data.type === 'token') {
                    setMessages(prev => {
                        const last = prev[prev.length - 1];
                        if (last && last.role === 'tars') {
                            const updatedText = last.text + data.text;
                            const isTeaching = updatedText.includes('**');
                            if (isTeaching && !last.isTeaching) {
                                currentTeachingMsgId.current = last.id;
                            }
                            return [...prev.slice(0, -1), { ...last, text: updatedText, isTeaching: isTeaching || last.isTeaching }];
                        }
                        const newMsg: Message = { id: Date.now().toString() + 't', role: 'tars', text: data.text, isTeaching: data.text.includes('**') };
                        if (newMsg.isTeaching) {
                            currentTeachingMsgId.current = newMsg.id;
                        }
                        return [...prev, newMsg];
                    });
                }
                if ((data.type === 'tars_answer' || data.type === 'audio_chunk') && data.audio_b64) {
                    setAudioQueue(prev => [...prev, data.audio_b64]);
                    if (currentTeachingMsgId.current) {
                        setMessages(prev => prev.map(msg => 
                            msg.id === currentTeachingMsgId.current 
                                ? { ...msg, audio_b64: [...(msg.audio_b64 || []), data.audio_b64] }
                                : msg
                        ));
                    }
                }
                if (data.type === 'tars_answer_end') {
                    setIsProcessing(false);
                    setTimeout(() => { currentTeachingMsgId.current = null; }, 5000);
                }
                if (data.type === 'error') { console.error(t('conversationContainer.error'), data.message); setIsProcessing(false); }
            };

            newSocket.onopen = () => {
                newSocket.send(JSON.stringify({
                    type: 'init_session',
                    thread_id: threadId,
                    conversation_id: conversationId,
                    mode,
                }));
                doSend(newSocket);
            };

            newSocket.onerror = () => {
                console.error(t('conversationContainer.reconnectFailed'));
                setIsProcessing(false);
            };
        }
    }, [sessionReady, isProcessing, threadId, conversationId, mode, t]);

    useEffect(() => {
        return () => { socketRef.current?.close(); };
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
