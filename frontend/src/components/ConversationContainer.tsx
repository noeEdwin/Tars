import { useState } from 'react';
import VoiceConversationScreen from './VoiceConversationScreen';
import ConversationScreen from './ConversationScreen';
import type { ViewState, SessionConfig } from '../App';
import type { PreWarmedSession, PreloadMessage } from '../utils/usePreWarmSession';
import useWebSocket from '../hooks/useWebSocket';

function getUserId(): number {
    const stored = localStorage.getItem('tars_user_id');
    return stored ? parseInt(stored, 10) : 1;
}

export interface Message {
    id: string;
    role: 'tars' | 'user';
    text: string;
    audio_b64?: string[];
    isTeaching?: boolean;
}

interface ConversationContainerProps {
    setCurrentView: (view: ViewState) => void;
    sessionConfig: SessionConfig;
    preWarmedSession?: PreWarmedSession | null;
    preloadMessage?: PreloadMessage | null;
    onSessionConsumed?: () => void;
}

export default function ConversationContainer({
    setCurrentView,
    sessionConfig,
    preWarmedSession,
    preloadMessage,
    onSessionConsumed,
}: ConversationContainerProps) {
    const { mode, filename, user_role, tars_role } = sessionConfig;
    const [subView, setSubView] = useState<'voice' | 'text'>('voice');

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
        userId: getUserId(),
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
                onBack={() => setCurrentView('home')}
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
