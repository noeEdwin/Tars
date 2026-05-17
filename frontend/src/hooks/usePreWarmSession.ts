import { useEffect, useRef, useState, useCallback } from 'react';
import { WS_BASE } from '../apiConfig';
import type { Message } from '../types/message';
import { useAuthStore } from '../stores/authStore';
import { chatApi, profileApi, ApiError } from '../api';

function getUserId(): number {
    const userId = useAuthStore.getState().userId;
    return userId ?? 1;
}

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
    /** Arrives separately — may be null if preload hasn't finished yet */
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
 * Phase 1 (fast, ~1-3 s): /start_session + WebSocket → sets `session`
 *                          App can transition to home immediately.
 * Phase 2 (parallel, ~1-2 s): /preload_message → patches `session.preloadMessage`
 *                          Ready before the user clicks Normal Mode.
 */
export function usePreWarmSession({ mode, enabled, filename, user_role, tars_role }: UsePreWarmOptions) {
    const [session, setSession] = useState<PreWarmedSession | null>(null);
    const [preloadMessage, setPreloadMessage] = useState<PreloadMessage | null>(null);
    const socketRef = useRef<WebSocket | null>(null);
    const sessionRef = useRef<PreWarmedSession | null>(null);

    const reset = useCallback(() => {
        socketRef.current = null;
        setSession(null);
    }, []);

    useEffect(() => {
        if (!enabled) return;

        const token = useAuthStore.getState().token;
        if (!token) return;

        let cancelled = false;
        const controller = new AbortController();

        const bufferedMessages: Message[] = [];
        const bufferedAudio: string[] = [];
        let latestProcessing = true;

        const run = async () => {
            try {
                const data = await chatApi.startSession({ mode, filename, user_role, tars_role });

                if (cancelled) return;

                const socket = new WebSocket(`${WS_BASE}/ws/${getUserId()}`);
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
                    if ((msg.type === 'tars_answer' || msg.type === 'audio_chunk') && msg.audio_b64) {
                        bufferedAudio.push(msg.audio_b64);
                    }
                    if (msg.type === 'tars_answer_end') latestProcessing = false;

                    const next: PreWarmedSession = {
                        threadId: data.thread_id,
                        conversationId: data.conversation_id,
                        socket,
                        messages: [...bufferedMessages],
                        audioQueue: [...bufferedAudio],
                        isProcessing: latestProcessing,
                        currentAudioIndex: 0,
                        preloadMessage: sessionRef.current?.preloadMessage ?? null,
                    };
                    sessionRef.current = next;
                    setSession(next);
                };

                let patchSent = false;
                const fetchPreload = mode === 'tars_roleplay'
                    ? () => profileApi.getRoleplayPreloadMessage(tars_role || '', filename || '')
                    : () => profileApi.getPreloadMessage();

                fetchPreload()
                    .then((data) => {
                        if (!data || patchSent || !data.text) return;
                        patchSent = true;
                        const pm: PreloadMessage = { text: data.text, audio_b64: data.audio_b64 ?? null };
                        if (sessionRef.current) {
                            const patched = { ...sessionRef.current, preloadMessage: pm };
                            sessionRef.current = patched;
                            setSession(patched);
                        }
                        setPreloadMessage(pm);
                    })
                    .catch(() => { /* preload is cosmetic — never block on error */ });

                const snap: PreWarmedSession = {
                    threadId: data.thread_id,
                    conversationId: data.conversation_id,
                    socket,
                    messages: [],
                    audioQueue: [],
                    isProcessing: true,
                    currentAudioIndex: 0,
                    preloadMessage: null,
                };
                sessionRef.current = snap;
                setSession(snap);

            } catch (err) {
                if (err instanceof ApiError && err.status === 401) {
                    useAuthStore.getState().logout();
                    window.location.href = '/';
                    return;
                }
                if (!cancelled) {
                    console.error('[PreWarm] Failed:', err);
                }
            }
        };

        run();
        return () => {
            cancelled = true;
            controller.abort();
        };
    }, [enabled, mode, filename, user_role, tars_role]);

    return { session, preloadMessage, reset };
}
