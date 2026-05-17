import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { jwtDecode } from 'jwt-decode';

interface JwtPayload {
    exp: number;
    sub: string;
    user_id: number;
}

interface AuthState {
    isAuthenticated: boolean;
    token: string | null;
    userId: number | null;
    username: string | null;
    firstName: string | null;

    login: (token: string, userId: number, username: string, firstName: string) => void;
    logout: () => void;
    updateFirstName: (firstName: string) => void;
    checkAuth: () => boolean;
}

export const useAuthStore = create<AuthState>()(
    persist(
        (set, get) => ({
            isAuthenticated: false,
            token: null,
            userId: null,
            username: null,
            firstName: null,

            login: (token, userId, username, firstName) => {
                set({
                    isAuthenticated: true,
                    token,
                    userId,
                    username,
                    firstName,
                });
            },

            logout: () => {
                set({
                    isAuthenticated: false,
                    token: null,
                    userId: null,
                    username: null,
                    firstName: null,
                });
            },

            updateFirstName: (firstName) => {
                set({ firstName });
            },

            checkAuth: () => {
                const { token } = get();
                if (!token) return false;
                try {
                    const decoded = jwtDecode<JwtPayload>(token);
                    const isValid = decoded.exp * 1000 > Date.now();
                    if (!isValid) {
                        get().logout();
                    }
                    return isValid;
                } catch {
                    get().logout();
                    return false;
                }
            },
        }),
        {
            name: 'tars-auth',
            partialize: (state) => ({
                isAuthenticated: state.isAuthenticated,
                token: state.token,
                userId: state.userId,
                username: state.username,
                firstName: state.firstName,
            }),
        }
    )
);
