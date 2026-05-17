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
| `frontend/src/stores/chatStore.ts` | **Deleted** — dead code, never imported anywhere |
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

---

## Step 5.3: Create Typed API Client Layer

### Problem

12 `fetch()` calls scattered across 7 files with:
- **No TypeScript types** for API responses — everything was `any`
- **Duplicated auth headers** — `Authorization: Bearer ${token}` repeated 6 times
- **Inconsistent error handling** — some checked `res.ok`, some didn't, some swallowed errors
- **No request timeouts** — network failures could hang indefinitely
- **No request/response validation** — backend Pydantic schemas weren't mirrored on frontend

### Solution

#### 1. TypeScript Types Mirroring Backend Pydantic Schemas

**`src/api/types.ts`** — 10 interfaces matching `auth/schemas.py` and route response models:
- `RegisterRequest`, `RegisterResponse`, `LoginRequest`, `TokenResponse`
- `UserProfile`, `ProfileUpdateRequest`, `GreetingResponse`, `PreloadMessageResponse`
- `RoleplayFilesResponse`, `STTResponse`, `StartSessionRequest`, `StartSessionResponse`

#### 2. API Client with Auth Interceptor + Timeout

**`src/api/client.ts`** — Centralized `ApiClient` class:
- **Automatic token injection** — reads `useAuthStore.getState().token` per request
- **10-second timeout** on all requests via `AbortController`
- **Unified error handling** — parses `detail` from both string and Pydantic array formats
- **Multipart support** — `upload()` skips `Content-Type: application/json` for `FormData`
- **204 handling** — returns `undefined` for no-content responses

```typescript
class ApiError extends Error {
    status: number;  // HTTP status code
}

const api = new ApiClient(API_BASE);

api.get<T>(path)       // GET with auth
api.post<T>(path, body) // POST with JSON + auth
api.put<T>(path, body)  // PUT with JSON + auth
api.delete<T>(path)     // DELETE with auth
api.upload<T>(path, formData) // POST multipart with auth
```

#### 3. Typed Service Layer

**`src/api/services/auth.ts`** — `authApi.login()`, `authApi.register()`
**`src/api/services/profile.ts`** — `profileApi.getProfile()`, `updateProfile()`, `getGreeting()`, `getPreloadMessage()`, `getRoleplayPreloadMessage()`
**`src/api/services/roleplay.ts`** — `roleplayApi.listFiles()`, `uploadFile()`, `deleteFile()`
**`src/api/services/stt.ts`** — `sttApi.transcribe(audioBlob)`
**`src/api/services/chat.ts`** — `chatApi.startSession()`

**`src/api/index.ts`** — Barrel export for all services, types, and `ApiError`.

#### 4. Migrated All 12 Fetch Calls

| File | Before | After |
|------|--------|-------|
| `SignInScreen.tsx` | `fetch('/auth/login')` + manual JSON + error parsing | `authApi.login()` |
| `SignUpScreen.tsx` | `fetch('/auth/register')` + manual JSON + Pydantic array handling | `authApi.register()` |
| `PersonalInfoScreen.tsx` | `fetch('/api/user/profile')` × 2 + manual headers | `profileApi.getProfile()`, `profileApi.updateProfile()` |
| `LoadingScreen.tsx` | `fetch('/greeting')` + manual 401 handling | `profileApi.getGreeting()` |
| `usePreWarmSession.ts` | `fetch('/start_session')` + `fetch('/preload_message')` + manual auth | `chatApi.startSession()`, `profileApi.getPreloadMessage()` |
| `useWebSocket.ts` | `fetch('/start_session')` + manual auth | `chatApi.startSession()` |
| `RoleplayScreen.tsx` | `fetch('/roleplay/files')` × 3 + manual FormData + auth | `roleplayApi.listFiles()`, `uploadFile()`, `deleteFile()` |
| `VoiceConversationScreen.tsx` | `fetch('/stt')` + manual FormData + error parsing | `sttApi.transcribe()` |

### Bugs Fixed

| # | Bug | Fix |
|---|-----|-----|
| 1 | No request timeouts — could hang indefinitely | 10s `AbortController` timeout on every request |
| 2 | Auth headers duplicated 6× across files | Single `getHeaders()` method in `ApiClient` |
| 3 | Inconsistent error parsing (string vs Pydantic array) | Unified in `fetchWithTimeout()` |
| 4 | `RoleplayScreen` depended on `token` in effect deps | Removed — auth now automatic via interceptor |
| 5 | `LoadingScreen` depended on `token` in effect deps | Removed — auth now automatic via interceptor |
| 6 | `PersonalInfoScreen` profile fetch re-ran on token change | Removed `token` dependency — auth automatic |

### Files Created

| File | Description |
|------|-------------|
| `frontend/src/api/types.ts` | 10 TypeScript interfaces mirroring backend Pydantic schemas |
| `frontend/src/api/client.ts` | `ApiClient` class with auth interceptor + 10s timeout |
| `frontend/src/api/services/auth.ts` | Auth endpoint wrappers |
| `frontend/src/api/services/profile.ts` | Profile endpoint wrappers |
| `frontend/src/api/services/roleplay.ts` | Roleplay endpoint wrappers |
| `frontend/src/api/services/stt.ts` | STT endpoint wrapper |
| `frontend/src/api/services/chat.ts` | Chat/session endpoint wrapper |
| `frontend/src/api/index.ts` | Barrel export for all services, types, and `ApiError` |

### Files Modified

| File | Change |
|------|--------|
| `frontend/src/components/auth/SignInScreen.tsx` | `authApi.login()` replaces `fetch()` |
| `frontend/src/components/auth/SignUpScreen.tsx` | `authApi.register()` replaces `fetch()` |
| `frontend/src/components/profile/PersonalInfoScreen.tsx` | `profileApi.getProfile()`, `updateProfile()` replace 2× `fetch()` |
| `frontend/src/screens/LoadingScreen.tsx` | `profileApi.getGreeting()` replaces `fetch()` |
| `frontend/src/components/roleplay/RoleplayScreen.tsx` | `roleplayApi.*` replaces 3× `fetch()` |
| `frontend/src/components/chat/VoiceConversationScreen.tsx` | `sttApi.transcribe()` replaces `fetch()` |
| `frontend/src/hooks/usePreWarmSession.ts` | `chatApi.startSession()`, `profileApi.getPreloadMessage()` replace `fetch()` |
| `frontend/src/hooks/useWebSocket.ts` | `chatApi.startSession()` replaces `fetch()` |

### Build Status

✅ TypeScript + Vite production build passes clean. Zero `fetch()` calls remain outside `api/client.ts`.
