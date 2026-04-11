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
    const socketRef = useRef<WebSocket | null>(null);
    const sessionRef = useRef<PreWarmedSession | null>(null);

    const reset = useCallback(() => {
        // Do NOT close the socket here — after handoff ConversationContainer owns it.
        // Closing here would kill in-flight LangGraph tokens.
        socketRef.current = null;
        setSession(null);
        sessionRef.current = null;
    }, []);

    useEffect(() => {
        if (!enabled) return;
        let cancelled = false;

        const bufferedMessages: Message[] = [];
        const bufferedAudio: string[] = [];
        let latestProcessing = true;

        const run = async () => {
            try {
                // ── Phase 1: session (blocks home-page transition) ────────────
                const sessionRes = await fetch(`${API_BASE}/start_session`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ user_id: USER_ID, mode, filename, user_role, tars_role }),
                });
                const data = await sessionRes.json();
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

                // ── Phase 2: start BEFORE snapshot so it's always in-flight ──
                // Uses its own flag independent of `cancelled` so the patch
                // always lands even if `enabled` flips false mid-flight.
                if (mode === 'tars_normal') {
                    let patchSent = false;
                    fetch(`${API_BASE}/preload_message?user_id=${USER_ID}`)
                        .then(r => r.json())
                        .then(({ text, audio_b64 }: { text?: string; audio_b64?: string }) => {
                            if (patchSent || !text) return;
                            patchSent = true;
                            const pm: PreloadMessage = { text, audio_b64: audio_b64 ?? null };
                            // Always patch via ref — works even if `cancelled` is true
                            if (sessionRef.current) {
                                const patched = { ...sessionRef.current, preloadMessage: pm };
                                sessionRef.current = patched;
                                setSession(patched);
                            }
                        })
                        .catch(() => { /* preload is cosmetic — never block on error */ });
                }

                // ── Snapshot: session is ready → unblocks home page ──────────
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
                console.error('[PreWarm] Failed:', err);
            }
        };

        run();
        return () => { cancelled = true; };
    }, [enabled, mode, filename, user_role, tars_role]);

    return { session, reset };
}
