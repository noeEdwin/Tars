import { jwtDecode } from 'jwt-decode';

interface JwtPayload {
    exp: number;
    sub: string;
    user_id: number;
}

export function isTokenValid(): boolean {
    const token = localStorage.getItem('tars_token');
    if (!token) return false;
    try {
        const decoded = jwtDecode<JwtPayload>(token);
        return decoded.exp * 1000 > Date.now();
    } catch {
        return false;
    }
}

export function clearAuth(): void {
    localStorage.removeItem('tars_token');
    localStorage.removeItem('tars_user_id');
    localStorage.removeItem('tars_username');
    localStorage.removeItem('tars_first_name');
}
