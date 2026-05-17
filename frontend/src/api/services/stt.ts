import { api } from '../client';
import type { STTResponse } from '../types';

export const sttApi = {
    transcribe: (audioBlob: Blob) => {
        const formData = new FormData();
        formData.append('audio', audioBlob, 'recording.webm');
        return api.upload<STTResponse>('/stt', formData);
    },
};
