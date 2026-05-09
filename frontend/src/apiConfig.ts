function trimTrailingSlashes(url: string) {
    return url.replace(/\/+$/, '');
}

const hostname = window.location.hostname;
const protocol = window.location.protocol; // includes trailing ':'

// Prefer explicit env overrides so deployments can point to the correct backend.
// Example:
// - VITE_API_BASE=http://127.0.0.1:8000
// - VITE_WS_BASE=ws://127.0.0.1:8000
const envApiBase = import.meta.env.VITE_API_BASE as string | undefined;
const envWsBase = import.meta.env.VITE_WS_BASE as string | undefined;

export const API_BASE = trimTrailingSlashes(
    envApiBase ?? `${protocol}//${hostname}:8000`,
);

const wsProtocol = protocol === 'https:' ? 'wss:' : 'ws:';
export const WS_BASE = trimTrailingSlashes(
    envWsBase ?? `${wsProtocol}//${hostname}:8000`,
);

console.log('🚀 API de Tars conectada a:', API_BASE);