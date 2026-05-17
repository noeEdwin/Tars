import { api } from '../client';
import type { LoginRequest, RegisterRequest, RegisterResponse, TokenResponse } from '../types';

export const authApi = {
    login: (data: LoginRequest) => api.post<TokenResponse>('/auth/login', data),
    register: (data: RegisterRequest) => api.post<RegisterResponse>('/auth/register', data),
};
