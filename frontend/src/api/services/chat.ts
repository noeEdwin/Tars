import { api } from '../client';
import type { StartSessionRequest, StartSessionResponse } from '../types';

export const chatApi = {
    startSession: (data: StartSessionRequest) =>
        api.post<StartSessionResponse>('/start_session', data),
};
