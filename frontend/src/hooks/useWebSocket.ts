import { useEffect, useState, useCallback, useRef } from 'react';
import { useAuthStore } from '../stores/authStore';
import { API_BASE, WS_BASE } from '../apiConfig';
import type { Message } from '../types/message';
import type { PreWarmedSession, PreloadMessage } from './usePreWarmSession';

interface UseWebSocketOptions {
    userId: number;
    mode: string;
    filename?: string;
    user_role?: string;
    tars_role?: string;
    preWarmedSession?: PreWarmedSession | null;
    preloadMessage?: PreloadMessage | null;
    onSessionConsumed?: () => void;
}

function handleSocketMessage(
    data: any,
    setMessages: React.Dispatch<React.SetStateAction<Message[]>>,
    setAudioQueue: React.Dispatch<React.SetStateAction<string[]>>,
    setIsProcessing: React.Dispatch<React.SetStateAction<boolean>>,
    currentTeachingMsgId: React.MutableRefObject<string | null>,
    onError: (message: string) => void,
) {
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
        onError(data.message);
        setIsProcessing(false);
    }
}

function attachMessageHandler(
    socket: WebSocket,
    setMessages: React.Dispatch<React.SetStateAction<Message[]>>,
    setAudioQueue: React.Dispatch<React.SetStateAction<string[]>>,
    setIsProcessing: React.Dispatch<React.SetStateAction<boolean>>,
    currentTeachingMsgId: React.MutableRefObject<string | null>,
    onError: (message: string) => void,
) {
    socket.onmessage = (event) => {
        const data = JSON.parse(event.data);
        handleSocketMessage(data, setMessages, setAudioQueue, setIsProcessing, currentTeachingMsgId, onError);
    };
}

export default function useWebSocket({
    userId,
    mode,
    filename,
    user_role,
    tars_role,
    preWarmedSession,
    onSessionConsumed,
}: UseWebSocketOptions) {
    const [messages, setMessages] = useState<Message[]>([]);
    const [audioQueue, setAudioQueue] = useState<string[]>([]);
    const [currentAudioIndex, setCurrentAudioIndex] = useState(0);
    const [isProcessing, setIsProcessing] = useState(false);
    const [sessionReady, setSessionReady] = useState(false);
    const [threadId, setThreadId] = useState('');
    const [conversationId, setConversationId] = useState(0);
    const socketRef = useRef<WebSocket | null>(null);
    const currentTeachingMsgId = useRef<string | null>(null);
    const preloadMessageRef = useRef<PreloadMessage | null>(null);

    const handleError = useCallback((message: string) => {
        console.error('WebSocket error:', message);
    }, []);

    // Pre-warmed session: adopt existing socket and state
    useEffect(() => {
        if (!preWarmedSession) return;

        socketRef.current = preWarmedSession.socket;
        setThreadId(preWarmedSession.threadId);
        setConversationId(preWarmedSession.conversationId);
        setCurrentAudioIndex(preWarmedSession.currentAudioIndex);

        const pm = preWarmedSession.preloadMessage;
        if (pm?.text) {
            preloadMessageRef.current = pm;
        }
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

        attachMessageHandler(
            preWarmedSession.socket,
            setMessages,
            setAudioQueue,
            setIsProcessing,
            currentTeachingMsgId,
            handleError,
        );

        // Delay consumption so the preload message has time to arrive
        setTimeout(() => onSessionConsumed?.(), 0);
    }, []);

    // Handle late-arriving preload message (arrives after session adoption)
    useEffect(() => {
        if (!preWarmedSession || !preWarmedSession.preloadMessage?.text) return;

        const pm = preWarmedSession.preloadMessage;
        setMessages(prev => {
            if (prev.some(m => m.id === 'preload-0')) return prev;
            return [{ id: 'preload-0', role: 'tars', text: pm.text }, ...prev];
        });
        if (pm.audio_b64) {
            setAudioQueue(prev => {
                if (prev.includes(pm.audio_b64!)) return prev;
                return [pm.audio_b64!, ...prev];
            });
        }
        setIsProcessing(false);
    }, [preWarmedSession?.preloadMessage]);

    // Fresh session: call /start_session then create WebSocket
    useEffect(() => {
        if (preWarmedSession !== null) return;
        if (!mode) return;

        let cancelled = false;

        const startSession = async () => {
            const token = useAuthStore.getState().token;
            const res = await fetch(`${API_BASE}/start_session`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
                },
                body: JSON.stringify({ mode, filename, user_role, tars_role }),
            });
            const data = await res.json();
            if (cancelled) return;

            setThreadId(data.thread_id);
            setConversationId(data.conversation_id);

            const socket = new WebSocket(`${WS_BASE}/ws/${userId}`);
            socketRef.current = socket;

            socket.onopen = () => {
                socket.send(JSON.stringify({
                    type: 'init_session',
                    thread_id: data.thread_id,
                    conversation_id: data.conversation_id,
                    mode,
                }));
                setIsProcessing(true);
                setSessionReady(true);
            };

            attachMessageHandler(socket, setMessages, setAudioQueue, setIsProcessing, currentTeachingMsgId, handleError);
        };

        startSession();

        return () => {
            cancelled = true;
            socketRef.current?.close();
        };
    }, [mode, preWarmedSession]);

    // Cleanup on unmount
    useEffect(() => {
        return () => { socketRef.current?.close(); };
    }, []);

    const interruptTars = useCallback(() => {
        if (socketRef.current?.readyState === WebSocket.OPEN) {
            socketRef.current.send(JSON.stringify({ type: 'interrupt' }));
            setAudioQueue([]);
            setCurrentAudioIndex(0);
            setIsProcessing(false);
        }
    }, []);

    const sendMessage = useCallback((text: string) => {
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
            console.warn('Socket reconnecting...');
            const newSocket = new WebSocket(`${WS_BASE}/ws/${userId}`);
            socketRef.current = newSocket;

            attachMessageHandler(newSocket, setMessages, setAudioQueue, setIsProcessing, currentTeachingMsgId, handleError);

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
                console.error('Reconnection failed');
                setIsProcessing(false);
            };
        }
    }, [sessionReady, isProcessing, threadId, conversationId, mode, userId]);

    return {
        sessionReady,
        messages,
        audioQueue,
        currentAudioIndex,
        setCurrentAudioIndex,
        isProcessing,
        sendMessage,
        interruptTars,
    };
}
