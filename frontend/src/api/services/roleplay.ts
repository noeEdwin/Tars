import { api } from '../client';
import type { RoleplayFilesResponse } from '../types';

export const roleplayApi = {
    listFiles: () => api.get<RoleplayFilesResponse>('/roleplay/files'),
    uploadFile: (formData: FormData) => api.upload<void>('/roleplay/upload', formData),
    deleteFile: (filename: string) =>
        api.delete<void>(`/roleplay/files/${encodeURIComponent(filename)}`),
};
