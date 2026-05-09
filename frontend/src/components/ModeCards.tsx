import { BookOpen, MessageSquare, ChevronRight } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import './ModeCards.css';
import type { ViewState, SessionConfig } from '../App';

interface ModeCardsProps {
    setCurrentView: (view: ViewState) => void;
    startConversation: (config: SessionConfig) => void;
}

export default function ModeCards({ setCurrentView, startConversation }: ModeCardsProps) {
    const { t } = useTranslation();

    return (
        <div className="mode-cards-container">
            <div className="mode-card" onClick={() => startConversation({ mode: 'tars_normal' })}>
                <div className="mode-icon-box normal-mode">
                    <BookOpen strokeWidth={2.5} size={24} color="#f87171" className="mode-icon" />
                </div>
                <div className="mode-text">
                    <h3 className="mode-title">{t('modeCards.normalMode')}</h3>
                    <p className="mode-subtitle">{t('modeCards.normalSubtitle')}</p>
                </div>
                <div className="mode-arrow">
                    <ChevronRight size={20} color="#666666" />
                </div>
            </div>

            <div className="mode-card" onClick={() => setCurrentView('roleplay')}>
                <div className="mode-icon-box roleplay-mode">
                    <MessageSquare strokeWidth={2.5} size={24} color="#d946ef" className="mode-icon" />
                </div>
                <div className="mode-text">
                    <h3 className="mode-title">{t('modeCards.roleplayMode')}</h3>
                    <p className="mode-subtitle">{t('modeCards.roleplaySubtitle')}</p>
                </div>
                <div className="mode-arrow">
                    <ChevronRight size={20} color="#666666" />
                </div>
            </div>
        </div>
    );
}
