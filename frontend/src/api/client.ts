import { useAuthStore } from '../stores/authStore';

const DEFAULT_TIMEOUT = 10_000;

export class ApiError extends Error {
    status: number;

    constructor(status: number, message: string) {
        super(message);
        this.name = 'ApiError';
        this.status = status;
    }
}

class ApiClient {
    baseUrl: string;

    constructor(baseUrl: string) {
        this.baseUrl = baseUrl;
    }

    private getHeaders(isMultipart: boolean, extra?: HeadersInit): HeadersInit {
        const token = useAuthStore.getState().token;
        const headers: Record<string, string> = {};

        if (!isMultipart) {
            headers['Content-Type'] = 'application/json';
        }
        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }
        if (extra) {
            Object.assign(headers, extra);
        }
        return headers;
    }

    private async fetchWithTimeout<T>(
        path: string,
        init: RequestInit,
        isMultipart: boolean,
    ): Promise<T> {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), DEFAULT_TIMEOUT);

        try {
            const res = await fetch(`${this.baseUrl}${path}`, {
                ...init,
                headers: this.getHeaders(isMultipart, init.headers),
                signal: controller.signal,
            });

            if (!res.ok) {
                let detail = 'Unknown error';
                try {
                    const body = await res.json();
                    if (typeof body.detail === 'string') {
                        detail = body.detail;
                    } else if (Array.isArray(body.detail)) {
                        detail = body.detail.map((e: { msg: string }) => e.msg).join(' ');
                    }
                } catch {
                    detail = `HTTP ${res.status}`;
                }
                throw new ApiError(res.status, detail);
            }

            if (res.status === 204) {
                return undefined as T;
            }

            return res.json();
        } finally {
            clearTimeout(timeoutId);
        }
    }

    async get<T>(path: string, headers?: HeadersInit): Promise<T> {
        return this.fetchWithTimeout<T>(path, { method: 'GET', headers }, false);
    }

    async post<T>(path: string, body?: unknown, headers?: HeadersInit): Promise<T> {
        return this.fetchWithTimeout<T>(
            path,
            { method: 'POST', body: JSON.stringify(body), headers },
            false,
        );
    }

    async put<T>(path: string, body?: unknown, headers?: HeadersInit): Promise<T> {
        return this.fetchWithTimeout<T>(
            path,
            { method: 'PUT', body: JSON.stringify(body), headers },
            false,
        );
    }

    async delete<T>(path: string, headers?: HeadersInit): Promise<T> {
        return this.fetchWithTimeout<T>(path, { method: 'DELETE', headers }, false);
    }

    async upload<T>(path: string, formData: FormData): Promise<T> {
        return this.fetchWithTimeout<T>(
            path,
            { method: 'POST', body: formData },
            true,
        );
    }
}

export const api = new ApiClient(
    import.meta.env.VITE_API_BASE?.replace(/\/+$/, '') ?? '',
);
