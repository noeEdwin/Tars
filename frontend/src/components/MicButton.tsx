import { Mic } from 'lucide-react';
import './MicButton.css';

export default function MicButton() {
    return (
        <div className="mic-container">
            <div className="mic-ring">
                <div className="mic-inner">
                    <div className="mic-icon-wrapper">
                        <Mic size={48} color="#ffffff" strokeWidth={2} className="mic-icon-svg" />
                    </div>
                    <div className="audio-bars">
                        <span className="bar bar-1"></span>
                        <span className="bar bar-2"></span>
                        <span className="bar bar-3"></span>
                        <span className="bar bar-4"></span>
                    </div>
                </div>
            </div>

            <div className="mic-text-container">
                <h1 className="mic-title">TAP TO SPEAK</h1>
                <p className="mic-subtitle">START A NEW CONVERSATION</p>
            </div>
        </div>
    );
}
