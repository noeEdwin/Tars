// Si estamos en desarrollo local, Vite pone esta variable en true
const isDev = import.meta.env.DEV;

// Detectamos la IP actual desde donde se carga la página
const hostname = window.location.hostname;

// Construimos la URL base. 
// Si la página es HTTPS, el backend DEBE ser llamado por el mismo protocolo 
// o el navegador lo bloqueará (Mixed Content).
const protocol = window.location.protocol;

export const API_BASE = `${protocol}//${hostname}:8000`;

// URL para el túnel de WebSocket
const wsProtocol = protocol === 'https:' ? 'wss:' : 'ws:';
export const WS_BASE = `${wsProtocol}//${hostname}:8000`;

console.log("🚀 Tars API conectada a:", API_BASE);