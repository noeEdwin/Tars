import { create } from 'zustand';

export type ViewState =
    | 'home'
    | 'roleplay'
    | 'profile'
    | 'settings'
    | 'personal-info'
    | 'sign-in'
    | 'sign-up'
    | 'forgot-password'
    | 'conversation'
    | 'loading'
    | 'loading-conversation';

export interface SessionConfig {
    mode: 'tars_normal' | 'tars_roleplay';
    filename?: string;
    tars_role?: string;
    user_role?: string;
}

interface SessionState {
    currentView: ViewState;
    sessionConfig: SessionConfig;
    roleplayConfig: SessionConfig | null;
    isLightMode: boolean;

    setView: (view: ViewState) => void;
    toggleTheme: () => void;
    startNormalSession: (config: SessionConfig) => void;
    startRoleplaySession: (config: SessionConfig) => void;
    prepareRoleplaySession: (config: SessionConfig) => void;
    consumeSession: () => void;
    resetToHome: () => void;
    resetToSignIn: () => void;
}

export const useSessionStore = create<SessionState>()((set) => ({
    currentView: 'loading',
    sessionConfig: { mode: 'tars_normal' },
    roleplayConfig: null,
    isLightMode: false,

    setView: (view) => set({ currentView: view }),

    toggleTheme: () => set((state) => ({ isLightMode: !state.isLightMode })),

    startNormalSession: (config) => {
        set({
            sessionConfig: config,
            currentView: 'conversation',
        });
    },

    startRoleplaySession: (config) => {
        set({
            sessionConfig: config,
            currentView: 'conversation',
        });
    },

    prepareRoleplaySession: (config) => {
        set({
            roleplayConfig: config,
            sessionConfig: config,
            currentView: 'loading-conversation',
        });
    },

    consumeSession: () => {
        set({ roleplayConfig: null });
    },

    resetToHome: () => {
        set({ currentView: 'home' });
    },

    resetToSignIn: () => {
        set({
            currentView: 'sign-in',
            sessionConfig: { mode: 'tars_normal' },
            roleplayConfig: null,
        });
    },
}));
