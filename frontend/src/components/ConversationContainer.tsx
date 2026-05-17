import { useState } from 'react';
import VoiceConversationScreen from './VoiceConversationScreen';
import ConversationScreen from './ConversationScreen';
import type { SessionConfig } from '../stores/sessionStore';
import type { PreWarmedSession, PreloadMessage } from '../utils/usePreWarmSession';
import useWebSocket from '../hooks/useWebSocket';
import { useAuthStore } from '../stores/authStore';
import { useSessionStore } from '../stores/sessionStore';

export interface Message {
    id: string;
    role: 'tars' | 'user';
    text: string;
    audio_b64?: string[];
    isTeaching?: boolean;
}

interface ConversationContainerProps {
    sessionConfig: SessionConfig;
    preWarmedSession?: PreWarmedSession | null;
    preloadMessage?: PreloadMessage | null;
    onSessionConsumed?: () => void;
}

export default function ConversationContainer({
    sessionConfig,
    preWarmedSession,
    preloadMessage,
    onSessionConsumed,
}: ConversationContainerProps) {
    const { mode, filename, user_role, tars_role } = sessionConfig;
    const [subView, setSubView] = useState<'voice' | 'text'>('voice');

    const userId = useAuthStore((s) => s.userId) || 1;
    const setView = useSessionStore((s) => s.setView);

    const {
        sessionReady,
        messages,
        audioQueue,
        currentAudioIndex,
        setCurrentAudioIndex,
        isProcessing,
        sendMessage,
        interruptTars,
    } = useWebSocket({
        userId,
        mode,
        filename,
        user_role,
        tars_role,
        preWarmedSession,
        preloadMessage,
        onSessionConsumed,
    });

    if (subView === 'voice') {
        return (
            <VoiceConversationScreen
                mode={mode}
                messages={messages}
                sessionReady={sessionReady}
                isProcessing={isProcessing}
                audioQueue={audioQueue}
                currentAudioIndex={currentAudioIndex}
                setCurrentAudioIndex={setCurrentAudioIndex}
                onSendMessage={sendMessage}
                onInterrupt={interruptTars}
                onBack={() => setView('home')}
                onSwitchToText={() => setSubView('text')}
            />
        );
    }

    return (
        <ConversationScreen
            mode={mode}
            messages={messages}
            sessionReady={sessionReady}
            isProcessing={isProcessing}
            onSendMessage={sendMessage}
            onBack={() => setSubView('voice')}
        />
    );
}
