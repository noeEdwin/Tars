import { useEffect, useRef, useState, useCallback } from 'react';
import { API_BASE, WS_BASE } from '../apiConfig';
import type { Message } from '../components/ConversationContainer';

const USER_ID = 1;

export interface PreloadMessage {
    text: string;
    audio_b64: string | null;
}

export interface PreWarmedSession {
    threadId: string;
    conversationId: number;
    socket: WebSocket;
    messages: Message[];
    audioQueue: string[];
    isProcessing: boolean;
    currentAudioIndex: number;
    /** TARS personalised opening message, ready to inject immediately */
    preloadMessage: PreloadMessage | null;
}

interface UsePreWarmOptions {
    mode: 'tars_normal' | 'tars_roleplay';
    enabled: boolean;
    filename?: string;
    user_role?: string;
    tars_role?: string;
}

/**
 * Kicks off /start_session + WebSocket + /preload_message (normal mode) in
 * parallel so the session and TARS's opening words are ready before the
 * user even clicks a mode button.
 */
export function usePreWarmSession({ mode, enabled, filename, user_role, tars_role }: UsePreWarmOptions) {
    const [session, setSession] = useState<PreWarmedSession | null>(null);
    const [isPreWarming, setIsPreWarming] = useState(false);
    const socketRef = useRef<WebSocket | null>(null);

    const reset = useCallback(() => {
        socketRef.current?.close();
        socketRef.current = null;
        setSession(null);
        setIsPreWarming(false);
    }, []);

    useEffect(() => {
        if (!enabled) return;

        let cancelled = false;
        setIsPreWarming(true);

        const bufferedMessages: Message[] = [];
        const bufferedAudio: string[] = [];
        let latestProcessing = true;

        const run = async () => {
            try {
                // ── Fire /start_session and (for normal mode) /preload_message in parallel ──
                const sessionFetch = fetch(`${API_BASE}/start_session`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ user_id: USER_ID, mode, filename, user_role, tars_role }),
                });

                const preloadFetch = mode === 'tars_normal'
                    ? fetch(`${API_BASE}/preload_message?user_id=${USER_ID}`).then(r => r.json()).catch(() => null)
                    : Promise.resolve(null);

                const [sessionRes, preloadData] = await Promise.all([sessionFetch, preloadFetch]);
                const data = await sessionRes.json();
                const preloadMessage: PreloadMessage | null =
                    preloadData?.text ? { text: preloadData.text, audio_b64: preloadData.audio_b64 ?? null } : null;

                if (cancelled) return;

                const socket = new WebSocket(`${WS_BASE}/ws/${USER_ID}`);
                socketRef.current = socket;

                socket.onopen = () => {
                    socket.send(JSON.stringify({
                        type: 'init_session',
                        thread_id: data.thread_id,
                        conversation_id: data.conversation_id,
                        mode,
                    }));
                };

                socket.onmessage = (event) => {
                    if (cancelled) return;
                    const msg = JSON.parse(event.data);

                    if (msg.type === 'token') {
                        const last = bufferedMessages[bufferedMessages.length - 1];
                        if (last && last.role === 'tars') {
                            last.text += msg.text;
                        } else {
                            bufferedMessages.push({ id: Date.now().toString() + 't', role: 'tars', text: msg.text });
                        }
                    }

                    if (msg.type === 'tars_answer' || msg.type === 'audio_chunk') {
                        if (msg.audio_b64) bufferedAudio.push(msg.audio_b64);
                    }

                    if (msg.type === 'tars_answer_end') {
                        latestProcessing = false;
                    }

                    setSession({
                        threadId: data.thread_id,
                        conversationId: data.conversation_id,
                        socket,
                        messages: [...bufferedMessages],
                        audioQueue: [...bufferedAudio],
                        isProcessing: latestProcessing,
                        currentAudioIndex: 0,
                        preloadMessage,
                    });
                };

                // Provide initial snapshot (session ready, no messages yet)
                setSession({
                    threadId: data.thread_id,
                    conversationId: data.conversation_id,
                    socket,
                    messages: [],
                    audioQueue: preloadMessage?.audio_b64 ? [preloadMessage.audio_b64] : [],
                    isProcessing: true,
                    currentAudioIndex: 0,
                    preloadMessage,
                });
            } catch (err) {
                console.error('[PreWarm] Failed:', err);
            } finally {
                if (!cancelled) setIsPreWarming(false);
            }
        };

        run();

        return () => {
            cancelled = true;
        };
    }, [enabled, mode, filename, user_role, tars_role]);

    return { session, isPreWarming, reset };
}
