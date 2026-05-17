// ─── Auth ───────────────────────────────────────────────────────────────────

export interface RegisterRequest {
    username: string;
    first_name: string;
    last_name: string;
    email: string;
    password: string;
    password_confirm: string;
    hsk_level: number;
    native_language: string;
    learning_goals: string;
    interests: string;
}

export interface RegisterResponse {
    message: string;
    user_id: number;
    username: string;
}

export interface LoginRequest {
    username: string;
    password: string;
}

export interface TokenResponse {
    access_token: string;
    token_type: string;
    user_id: number;
    username: string;
    first_name: string;
    hsk_level: number;
}

// ─── Profile ────────────────────────────────────────────────────────────────

export interface UserProfile {
    id: number;
    username: string;
    first_name: string;
    last_name: string;
    email: string;
    hsk_level: number;
    native_language: string;
    learning_goals: string;
    interests: string;
}

export interface ProfileUpdateRequest {
    first_name: string;
    last_name: string;
    hsk_level: number;
    native_language: string;
    learning_goals: string;
    interests: string;
}

export interface GreetingResponse {
    greeting: string;
    username: string;
}

export interface PreloadMessageResponse {
    text: string;
    audio_b64: string | null;
}

// ─── Roleplay ───────────────────────────────────────────────────────────────

export interface RoleplayFilesResponse {
    files: string[];
}

// ─── STT ────────────────────────────────────────────────────────────────────

export interface STTResponse {
    text: string;
}

// ─── Chat / Session ─────────────────────────────────────────────────────────

export interface StartSessionRequest {
    mode: string;
    filename?: string;
    user_role?: string;
    tars_role?: string;
}

export interface StartSessionResponse {
    thread_id: string;
    conversation_id: number;
}
