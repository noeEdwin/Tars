# Phase 5: Frontend — Changelog

## Step 5.1: Add Zustand for State Management

### Problem

The frontend had **zero state management library**. All state was managed through:
- **80 `useState` calls** across 11 files
- **27 `useRef` calls** (many for state-like purposes)
- **29 `localStorage` reads/writes** across 10 files
- **Zero `useContext`**, zero `useReducer`
- **Heavy props drilling** — `setCurrentView` passed through 12+ components

This caused:
1. **No reactive auth state** — Header/ProfileScreen didn't re-render when user updated profile
2. **Stale user name** — read from localStorage only on mount
3. **Duplicated logout logic** — SettingsScreen duplicated 4 `removeItem()` calls instead of using `clearAuth()`
4. **Chat state props drilling** — 8 values drilled through 3 component levels
5. **Race condition** — late preload patch raced with incoming WebSocket tokens

### Solution

#### 1. Created 3 Zustand Stores

**`authStore`** — Authentication state with `persist` middleware for localStorage:
```typescript
interface AuthState {
    isAuthenticated: boolean;
    token: string | null;
    userId: number | null;
    username: string | null;
    firstName: string | null;
    login: (token, userId, username, firstName) => void;
    logout: () => void;
    updateFirstName: (firstName: string) => void;
    checkAuth: () => boolean;  // validates token, auto-logout if expired
}
```

**`sessionStore`** — Navigation and session lifecycle:
```typescript
interface SessionState {
    currentView: ViewState;
    sessionConfig: SessionConfig;
    roleplayConfig: SessionConfig | null;
    isLightMode: boolean;
    setView: (view: ViewState) => void;
    toggleTheme: () => void;
    startNormalSession: (config: SessionConfig) => void;
    prepareRoleplaySession: (config: SessionConfig) => void;
    consumeSession: () => void;
    resetToSignIn: () => void;
}
```

**`chatStore`** — Chat and WebSocket state (created, ready for Phase D migration):
```typescript
interface ChatState {
    messages: Message[];
    audioQueue: string[];
    isProcessing: boolean;
    sessionReady: boolean;
    threadId: string | null;
    conversationId: number | null;
    preloadMessage: PreloadMessage | null;
    // Actions: addMessage, pushAudio, setProcessing, clearChat, etc.
}
```

#### 2. Migrated Auth State (Phase B)

| File | Before | After |
|------|--------|-------|
| `SignInScreen.tsx` | `localStorage.setItem()` × 4 | `authStore.login()` |
| `SettingsScreen.tsx` | `localStorage.removeItem()` × 4 | `authStore.logout()` |
| `Header.tsx` | Mount-only `useEffect` reading localStorage | `useAuthStore()` selector (reactive) |
| `ProfileScreen.tsx` | Same as Header | Same as Header |
| `PersonalInfoScreen.tsx` | `localStorage.setItem('tars_first_name')` | `authStore.updateFirstName()` |
| `LoadingScreen.tsx` | `clearAuth()` + `window.location.href` | `authStore.logout()` + `setView('sign-in')` |
| `usePreWarmSession.ts` | `localStorage.getItem('tars_token')` | `useAuthStore.getState().token` |
| `useWebSocket.ts` | `localStorage.getItem('tars_token')` | `useAuthStore.getState().token` |
| `RoleplayScreen.tsx` | `localStorage.getItem('tars_token')` × 3 | `useAuthStore((s) => s.token)` |

#### 3. Migrated Session State (Phase C)

| File | Before | After |
|------|--------|-------|
| `App.tsx` | 4 `useState` + props drilling to 12+ components | `useSessionStore()` selectors |
| `ModeCards.tsx` | `setCurrentView` prop | `useSessionStore((s) => s.setView)` |
| `MicButton.tsx` | `setCurrentView` prop | `useSessionStore((s) => s.setView)` |
| `BottomNav.tsx` | `currentView` + `setCurrentView` props | `useSessionStore()` selectors |
| `RoleplayScreen.tsx` | `setCurrentView` + `startConversation` props | `useSessionStore()` actions |
| `ConversationContainer.tsx` | `setCurrentView` prop | `useSessionStore((s) => s.setView)` |
| `ProfileScreen.tsx` | `setCurrentView` prop | `useSessionStore((s) => s.setView)` |
| `SettingsScreen.tsx` | `setCurrentView` + `isLightMode` + `toggleTheme` props | `useSessionStore()` selectors |
| `SignInScreen.tsx` | `setCurrentView` + `isLightMode` props | `useSessionStore()` selectors |
| `SignUpScreen.tsx` | `setCurrentView` + `isLightMode` props | `useSessionStore()` selectors |
| `ForgotPasswordScreen.tsx` | `setCurrentView` prop | `useSessionStore((s) => s.setView)` |
| `PersonalInfoScreen.tsx` | `setCurrentView` prop | `useSessionStore((s) => s.setView)` |

#### 4. Fixed `useWebSocket` Options Interface

Added missing `preloadMessage` to `UseWebSocketOptions` interface — previously passed from `ConversationContainer` but silently ignored.

### Bugs Fixed

| # | Bug | Fix |
|---|-----|-----|
| 1 | Logout bypassed `clearAuth()` utility | `authStore.logout()` replaces duplicated code |
| 2 | User name read independently by Header + ProfileScreen | Single `useAuthStore()` selector, reactive updates |
| 3 | Stale user name after profile update | `authStore.updateFirstName()` triggers re-render everywhere |
| 4 | No reactive auth state | Zustand store with `persist` middleware |
| 5 | `setCurrentView` drilled through 12+ components | `useSessionStore((s) => s.setView)` in each component |
| 6 | `preloadMessage` prop silently ignored | Added to `UseWebSocketOptions` interface |

### Files Modified

| File | Action |
|------|--------|
| `frontend/src/stores/authStore.ts` | **Created** — Auth state with persist middleware |
| `frontend/src/stores/sessionStore.ts` | **Created** — Session/navigation state |
| `frontend/src/stores/chatStore.ts` | **Created** — Chat state (ready for future migration) |
| `frontend/src/App.tsx` | Replaced 4 `useState` with store selectors, removed props drilling |
| `frontend/src/components/SignInScreen.tsx` | Uses `authStore.login()`, `sessionStore` selectors |
| `frontend/src/components/SignUpScreen.tsx` | Uses `sessionStore` selectors |
| `frontend/src/components/ForgotPasswordScreen.tsx` | Uses `sessionStore.setView()` |
| `frontend/src/components/SettingsScreen.tsx` | Uses `authStore.logout()`, `sessionStore` selectors |
| `frontend/src/components/Header.tsx` | Uses `authStore` + `sessionStore` selectors (reactive) |
| `frontend/src/components/ProfileScreen.tsx` | Uses `authStore` + `sessionStore` selectors (reactive) |
| `frontend/src/components/PersonalInfoScreen.tsx` | Uses `authStore.updateFirstName()`, `sessionStore` |
| `frontend/src/components/ModeCards.tsx` | Uses `sessionStore` actions |
| `frontend/src/components/MicButton.tsx` | Uses `sessionStore.setView()` |
| `frontend/src/components/BottomNav.tsx` | Uses `sessionStore` selectors |
| `frontend/src/components/RoleplayScreen.tsx` | Uses `authStore.token`, `sessionStore` actions |
| `frontend/src/components/ConversationContainer.tsx` | Uses `authStore.userId`, `sessionStore.setView()` |
| `frontend/src/components/LoadingScreen.tsx` | Uses `authStore.logout()`, `sessionStore.setView()` |
| `frontend/src/hooks/useWebSocket.ts` | Uses `authStore.getState().token`, added `preloadMessage` to interface |
| `frontend/src/utils/usePreWarmSession.ts` | Uses `authStore.getState()` for token and userId |
