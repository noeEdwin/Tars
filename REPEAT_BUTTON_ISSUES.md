# Repeat Phrase Button - Issues & Requirements Document

## Problem Statement
User cannot repeat/hear again the 3-word phrase TARS teaches during lesson mode. Once the audio plays, it's gone.

## Requirements (from User)
- [x] Only repeat the CURRENT phrase being taught (3-word phrase)
- [x] Button appears in BOTH Voice and Text chat screens  
- [x] Cache audio (replay exact audio generated, no re-TTS)
- [x] Button visible ONLY after phrase was spoken
- [x] User can click repeatedly to hear multiple times
- [x] Replay EXACT audio that was generated (no re-generation)
- [x] ONLY works during "awaiting_answer" state
- [x] ONLY for tars_normal mode (lesson mode)
- [x] User prefers VoiceConversationScreen (prioritize this)

## Current Architecture
- **Frontend**: React + TypeScript + Vite
- **Audio**: Google Cloud TTS → base64 MP3 via WebSocket `audio_chunk`
- **Audio queue**: `audioQueue: string[]` - cleared on new message or interrupt
- **No caching** of audio with messages currently
- **Message format**: TARS messages contain target word in `**bold**` format

## Implementation Decisions
- **Frontend-only change** (no backend modification)
- Extend Message interface with optional `audio_b64: string[]`
- Cache audio when `audio_chunk` received during teaching mode
- Detect "awaiting_answer" state via message content heuristic
- Add repeat button to TARS message bubble (Voice + Text screens)
- Button visibility tied to teaching state detection

## Files Modified
1. `frontend/src/components/ConversationContainer.tsx` - Cache audio logic + detect teaching
2. `frontend/src/components/VoiceConversationScreen.tsx` - Add repeat button + replay
3. `frontend/src/components/ConversationScreen.tsx` - Add repeat button (text chat)
4. `REPEAT_BUTTON_ISSUES.md` - This document

## Teaching Mode Detection Heuristic
Since backend doesn't send `awaiting_answer` via WebSocket, detect teaching mode by:
- Message contains `**` pattern (target word in bold)
- Message contains "Palabra objetivo" or "INSTRUCCIÓN"
- Used for button visibility only

## Caching Strategy
- When `audio_chunk` received, check if current message is teaching
- If yes, append base64 audio to message's `audio_b64` array
- On repeat button click → replay all cached audio chunks in order
