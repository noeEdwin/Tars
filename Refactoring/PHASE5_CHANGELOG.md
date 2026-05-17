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

**`chatStore`** — Created but **never imported anywhere**. Deleted as dead code. Chat state remains in `useWebSocket` hook via internal `useState`.

### Step 5.2: Reorganize Components into Folders

#### Problem

All 15 components lived flat in `src/components/` with no grouping. Imports were verbose and unclear about component purpose.

#### Solution

##### 1. Folder Structure

```
frontend/src/
├── components/
│   ├── auth/
│   │   ├── index.ts                    # barrel export
│   │   ├── SignInScreen.tsx + .css
│   │   ├── SignUpScreen.tsx + .css
│   │   └── ForgotPasswordScreen.tsx + .css
│   ├── chat/
│   │   ├── index.ts                    # barrel export
│   │   ├── ConversationContainer.tsx
│   │   ├── ConversationScreen.tsx + .css
│   │   └── VoiceConversationScreen.tsx + .css
│   ├── roleplay/
│   │   ├── index.ts                    # barrel export
│   │   └── RoleplayScreen.tsx + .css
│   ├── profile/
│   │   ├── index.ts                    # barrel export
│   │   ├── ProfileScreen.tsx + .css
│   │   ├── SettingsScreen.tsx + .css
│   │   └── PersonalInfoScreen.tsx + .css
│   └── layout/
│       ├── index.ts                    # barrel export
│       ├── Header.tsx + .css
│       ├── MicButton.tsx + .css
│       ├── ModeCards.tsx + .css
│       └── BottomNav.tsx + .css
├── screens/
│   ├── index.ts                        # barrel export
│   └── LoadingScreen.tsx + .css
├── types/
│   └── message.ts                      # extracted Message interface
├── hooks/
│   ├── usePreWarmSession.ts            # moved from utils/
│   └── useWebSocket.ts
├── utils/
│   └── messageParser.ts
└── stores/
    ├── authStore.ts
    └── sessionStore.ts
```

##### 2. Barrel Exports

Each subfolder has an `index.ts` re-exporting its components:
```typescript
// components/auth/index.ts
export { default as SignInScreen } from './SignInScreen';
export { default as SignUpScreen } from './SignUpScreen';
export { default as ForgotPasswordScreen } from './ForgotPasswordScreen';
```

##### 3. Updated `App.tsx` Imports

Before:
```typescript
import Header from './components/Header';
import SignInScreen from './components/SignInScreen';
import LoadingScreen from './components/LoadingScreen';
```

After:
```typescript
import { Header, MicButton, ModeCards, BottomNav } from './components/layout';
import { SignInScreen, SignUpScreen, ForgotPasswordScreen } from './components/auth';
import { LoadingScreen } from './screens';
```

##### 4. Extracted `Message` Type

Moved from `ConversationContainer.tsx` to `types/message.ts`:
```typescript
export interface Message {
    id: string;
    role: 'tars' | 'user';
    text: string;
    audio_b64?: string[];
    isTeaching?: boolean;
}
```

##### 5. Deleted Dead Code

| File | Reason |
|------|--------|
| `stores/chatStore.ts` | Never imported — chat state managed by `useWebSocket` hook |
| `utils/auth.ts` | Never imported — replaced by `authStore` |

### Files Modified

| File | Action |
|------|--------|
| `frontend/src/components/auth/` | Created, 3 components moved + barrel export |
| `frontend/src/components/chat/` | Created, 3 components moved + barrel export |
| `frontend/src/components/roleplay/` | Created, 1 component moved + barrel export |
| `frontend/src/components/profile/` | Created, 3 components moved + barrel export |
| `frontend/src/components/layout/` | Created, 4 components moved + barrel export |
| `frontend/src/screens/` | Created, `LoadingScreen` moved + barrel export |
| `frontend/src/types/message.ts` | Created — extracted `Message` interface |
| `frontend/src/hooks/usePreWarmSession.ts` | Moved from `utils/`, fixed imports |
| `frontend/src/hooks/useWebSocket.ts` | Fixed imports |
| `frontend/src/App.tsx` | Updated to barrel imports |
| `frontend/stores/chatStore.ts` | **Deleted** — dead code |
| `frontend/utils/auth.ts` | **Deleted** — dead code |

### Build Status

✅ TypeScript + Vite production build passes clean.

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
