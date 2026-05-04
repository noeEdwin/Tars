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
    audio_b64?: string[];  // Cached audio chunks for repeat
    isTeaching?: boolean;   // Is this a teaching phrase
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
    const currentTeachingMsgId = useRef<string | null>(null);

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

        // Preload audio goes FIRST so TARS speaks the greeting immediately
        const initialAudio = [
            ...(pm?.audio_b64 ? [pm.audio_b64] : []),
            ...preWarmedSession.audioQueue,
        ];
        setAudioQueue(initialAudio);

        // The greeting comes from /preload_message — NOT from LangGraph streaming.
        // tars_answer_end was never sent (socket may have closed before that).
        // Force isProcessing=false so the mic unlocks once audio finishes.
        setIsProcessing(pm ? false : preWarmedSession.isProcessing);
        setSessionReady(true);

        // Re-attach onmessage so we keep receiving future events
        preWarmedSession.socket.onmessage = (event) => {
            const data = JSON.parse(event.data);

            if (data.type === 'token') {
                setMessages(prev => {
                    const lastMsg = prev[prev.length - 1];
                    if (lastMsg && lastMsg.role === 'tars') {
                        const updatedText = lastMsg.text + data.text;
                        // Detect teaching mode: contains **target word** pattern
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
                    // Cache audio for teaching messages
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
                // Don't reset currentTeachingMsgId here - let the audio finish playing
                // Reset after a delay to allow audio caching to complete
                setTimeout(() => { currentTeachingMsgId.current = null; }, 5000);
            }
            if (data.type === 'error') {
                console.error('Tars error:', data.message);
                setIsProcessing(false);
            }
        };

        // Defer until after this synchronous effect finishes.
        // This guarantees the re-attached onmessage above is active before
        // App.tsx calls resetPreWarm() (which used to close the socket).
        setTimeout(() => onSessionConsumed?.(), 0);
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
                        const updatedText = lastMsg.text + data.text;
                        // Detect teaching mode: contains **target word** pattern
                        const isTeaching = updatedText.includes('**');
                        // Update currentTeachingMsgId if this becomes a teaching message
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
                    // Cache audio for teaching messages
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
                // Don't reset currentTeachingMsgId here - let audio finish playing
                // Reset after a delay to allow audio caching to complete
                setTimeout(() => { currentTeachingMsgId.current = null; }, 5000);
            }
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
            // Happy path — socket is alive
            doSend(currentSocket);
        } else {
            // Pre-warm socket died (race). Re-open and send after init.
            console.warn('[ConversationContainer] Socket not open, reconnecting...');
            const newSocket = new WebSocket(`${WS_BASE}/ws/${USER_ID}`);
            socketRef.current = newSocket;

            // Reattach all message handlers to the new socket
            newSocket.onmessage = (event) => {
                const data = JSON.parse(event.data);
                if (data.type === 'token') {
                    setMessages(prev => {
                        const last = prev[prev.length - 1];
                        if (last && last.role === 'tars') {
                            const updatedText = last.text + data.text;
                            const isTeaching = updatedText.includes('**');
                            // Update currentTeachingMsgId if this becomes a teaching message
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
                    // Don't reset currentTeachingMsgId here - let audio finish playing
                    setTimeout(() => { currentTeachingMsgId.current = null; }, 5000);
                }
                if (data.type === 'error') { console.error('Tars error:', data.message); setIsProcessing(false); }
            };

            newSocket.onopen = () => {
                // Re-init session state, then immediately send the user message
                newSocket.send(JSON.stringify({
                    type: 'init_session',
                    thread_id: threadId,
                    conversation_id: conversationId,
                    mode,
                }));
                doSend(newSocket);
            };

            newSocket.onerror = () => {
                console.error('[ConversationContainer] Reconnect failed');
                setIsProcessing(false);
            };
        }
    }, [sessionReady, isProcessing, threadId, conversationId, mode]);

    // ── Cleanup ────────────────────────────────────────────────────────────
    // ConversationContainer is always the final socket owner:
    //  - fast path: socket was handed off from usePreWarmSession
    //  - cold path: socket was created here
    // Either way, close it when this component unmounts.
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
