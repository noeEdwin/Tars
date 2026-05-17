import { create } from 'zustand';

export interface Message {
    id: string;
    role: 'user' | 'assistant';
    text: string;
    audioB64?: string;
    timestamp: number;
}

export interface PreloadMessage {
    text: string;
    audioB64?: string;
}

interface ChatState {
    messages: Message[];
    audioQueue: string[];
    currentAudioIndex: number;
    isProcessing: boolean;
    sessionReady: boolean;
    threadId: string | null;
    conversationId: number | null;
    preloadMessage: PreloadMessage | null;

    addMessage: (msg: Message) => void;
    pushAudio: (b64: string) => void;
    advanceAudio: () => void;
    setCurrentAudioIndex: (index: number) => void;
    setProcessing: (val: boolean) => void;
    setSessionReady: (val: boolean) => void;
    setSessionIds: (threadId: string, conversationId: number) => void;
    setPreloadMessage: (msg: PreloadMessage | null) => void;
    clearChat: () => void;
}

export const useChatStore = create<ChatState>()((set) => ({
    messages: [],
    audioQueue: [],
    currentAudioIndex: 0,
    isProcessing: false,
    sessionReady: false,
    threadId: null,
    conversationId: null,
    preloadMessage: null,

    addMessage: (msg) => set((state) => ({ messages: [...state.messages, msg] })),

    pushAudio: (b64) => set((state) => ({ audioQueue: [...state.audioQueue, b64] })),

    advanceAudio: () => set((state) => ({ currentAudioIndex: state.currentAudioIndex + 1 })),

    setCurrentAudioIndex: (index) => set({ currentAudioIndex: index }),

    setProcessing: (val) => set({ isProcessing: val }),

    setSessionReady: (val) => set({ sessionReady: val }),

    setSessionIds: (threadId, conversationId) => set({ threadId, conversationId }),

    setPreloadMessage: (msg) => set({ preloadMessage: msg }),

    clearChat: () => set({
        messages: [],
        audioQueue: [],
        currentAudioIndex: 0,
        isProcessing: false,
        sessionReady: false,
        threadId: null,
        conversationId: null,
        preloadMessage: null,
    }),
}));
