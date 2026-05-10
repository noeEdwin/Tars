function trimTrailingSlashes(url: string) {
    return url.replace(/\/+$/, '');
}

const hostname = window.location.hostname;
const protocol = window.location.protocol;

const envApiBase = import.meta.env.VITE_API_BASE as string | undefined;
const envWsBase = import.meta.env.VITE_WS_BASE as string | undefined;

export const API_BASE = trimTrailingSlashes(
    envApiBase ?? '',
);

const wsProtocol = protocol === 'https:' ? 'wss:' : 'ws:';
export const WS_BASE = trimTrailingSlashes(
    envWsBase ?? `${wsProtocol}//${hostname}:${window.location.port}`,
);

console.log('🚀 API de Tars conectada a:', API_BASE || '(same origin via proxy)');
