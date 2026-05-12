import { useEffect, useRef, useState, useCallback } from 'react';
import { API_BASE, WS_BASE } from '../apiConfig';
import type { Message } from '../components/ConversationContainer';
import { clearAuth } from './auth';

function getUserId(): number {
    const stored = localStorage.getItem('tars_user_id');
    return stored ? parseInt(stored, 10) : 1;
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
        const controller = new AbortController();

        const bufferedMessages: Message[] = [];
        const bufferedAudio: string[] = [];
        let latestProcessing = true;

        const run = async () => {
            try {
                // ── Phase 1: session (blocks home-page transition) ────────────
                const startUrl = `${API_BASE}/start_session`;
                const token = localStorage.getItem('tars_token');
                const sessionRes = await fetch(startUrl, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
                    },
                    body: JSON.stringify({ mode, filename, user_role, tars_role }),
                    signal: controller.signal,
                });
                if (!sessionRes.ok) {
                    if (sessionRes.status === 401) {
                        clearAuth();
                        window.location.href = '/';
                        return;
                    }
                    const body = await sessionRes.text().catch(() => '');
                    throw new Error(
                        `[PreWarm] start_session failed (${sessionRes.status} ${sessionRes.statusText}) url=${startUrl} body=${body.slice(0, 500)}`,
                    );
                }
                const data = await sessionRes.json().catch(async () => {
                    const body = await sessionRes.text().catch(() => '');
                    throw new Error(`[PreWarm] start_session invalid JSON url=${startUrl} body=${body.slice(0, 500)}`);
                });
                if (cancelled) return;

                const threadId = data.thread_id;
                const conversationId = data.conversation_id;

                const connectSocket = (hasPreload: boolean) => {
                    if (cancelled) return;
                    const socket = new WebSocket(`${WS_BASE}/ws/${getUserId()}`);
                    socketRef.current = socket;

                    socket.onopen = () => {
                        socket.send(JSON.stringify({
                            type: 'init_session',
                            thread_id: threadId,
                            conversation_id: conversationId,
                            mode,
                            has_preload: hasPreload,
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
                            threadId,
                            conversationId,
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

                    return socket;
                };

                if (mode === 'tars_roleplay') {
                    // ── Roleplay: preload FIRST, then connect socket ────────
                    // The socket must not open until the preload response is
                    // ready so init_session carries has_preload: true and the
                    // backend skips the duplicate LangGraph greeting.
                    let preloadHasMessage = false;
                    if (user_role && tars_role) {
                        try {
                            const preloadRes = await fetch(`${API_BASE}/preload_roleplay_message`, {
                                method: 'POST',
                                signal: controller.signal,
                                headers: {
                                    'Content-Type': 'application/json',
                                    ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
                                },
                                body: JSON.stringify({ user_role, tars_role }),
                            });
                            if (preloadRes.status === 401) {
                                clearAuth();
                                window.location.href = '/';
                                return;
                            }
                            const pmData = await preloadRes.json().catch(() => null);
                            if (!cancelled && pmData?.text) {
                                const pm: PreloadMessage = { text: pmData.text, audio_b64: pmData.audio_b64 ?? null };
                                sessionRef.current = {
                                    threadId, conversationId,
                                    socket: null as unknown as WebSocket,
                                    messages: [], audioQueue: [],
                                    isProcessing: true, currentAudioIndex: 0,
                                    preloadMessage: pm,
                                };
                                preloadHasMessage = true;
                            }
                        } catch { /* preload is cosmetic — never block on error */ }
                    }
                    if (cancelled) return;

                    connectSocket(preloadHasMessage);

                    // ── Snapshot ────────────────────────────────────────────
                    const snap: PreWarmedSession = {
                        threadId,
                        conversationId,
                        socket: socketRef.current!,
                        messages: [],
                        audioQueue: [],
                        isProcessing: true,
                        currentAudioIndex: 0,
                        preloadMessage: sessionRef.current?.preloadMessage ?? null,
                    };
                    sessionRef.current = snap;
                    setSession(snap);

                } else {
                    // ── Normal mode: connect immediately, preload in parallel ─
                    connectSocket(false);

                    // ── Phase 2: preload message (fire-and-forget) ─────────
                    let patchSent = false;
                    const preloadUrl = `${API_BASE}/preload_message`;
                    fetch(preloadUrl, {
                        signal: controller.signal,
                        headers: token ? { 'Authorization': `Bearer ${token}` } : {},
                    })
                        .then(r => {
                            if (r.status === 401) {
                                clearAuth();
                                window.location.href = '/';
                                return null;
                            }
                            return r.json();
                        })
                        .then(({ text, audio_b64 }: { text?: string; audio_b64?: string } | null) => {
                            if (patchSent || !text) return;
                            patchSent = true;
                            const pm: PreloadMessage = { text, audio_b64: audio_b64 ?? null };
                            if (sessionRef.current) {
                                const patched = { ...sessionRef.current, preloadMessage: pm };
                                sessionRef.current = patched;
                                setSession(patched);
                            }
                        })
                        .catch(() => { /* preload is cosmetic — never block on error */ });

                    // ── Snapshot ────────────────────────────────────────────
                    const snap: PreWarmedSession = {
                        threadId,
                        conversationId,
                        socket: socketRef.current!,
                        messages: [],
                        audioQueue: [],
                        isProcessing: true,
                        currentAudioIndex: 0,
                        preloadMessage: null,
                    };
                    sessionRef.current = snap;
                    setSession(snap);
                }

            } catch (err) {
                // Fetch can throw TypeError("NetworkError...") for CORS/TLS/mixed-content/offline.
                // Log the bases to make the root cause obvious.
                if (!cancelled) {
                    console.error('[PreWarm] Failed:', err, { API_BASE, WS_BASE, mode });
                }
            }
        };

        run();
        return () => {
            cancelled = true;
            controller.abort();
        };
    }, [enabled, mode, filename, user_role, tars_role]);

    return { session, reset };
}
