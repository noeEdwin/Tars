import { api } from '../client';
import type {
    UserProfile,
    ProfileUpdateRequest,
    GreetingResponse,
    PreloadMessageResponse,
} from '../types';

export const profileApi = {
    getProfile: () => api.get<UserProfile>('/api/user/profile'),
    updateProfile: (data: ProfileUpdateRequest) => api.put<UserProfile>('/api/user/profile', data),
    getGreeting: () => api.get<GreetingResponse>('/greeting'),
    getPreloadMessage: () => api.get<PreloadMessageResponse>('/preload_message'),
    getRoleplayPreloadMessage: (tarsRole: string, filename: string) =>
        api.get<PreloadMessageResponse>(
            `/preload_message_roleplay?tars_role=${encodeURIComponent(tarsRole)}&filename=${encodeURIComponent(filename)}`,
        ),
};
