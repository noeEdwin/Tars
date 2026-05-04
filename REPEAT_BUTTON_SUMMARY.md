# Repeat Button - Implementation Summary

## What Was Implemented

A "Repeat Phrase" button that allows users to replay the exact audio of the current teaching phrase (3-word structure) during lesson mode.

## Requirements Met

- ✅ Only repeats the CURRENT phrase being taught (3-word phrase)
- ✅ Button appears in BOTH Voice and Text chat screens  
- ✅ Audio is cached (replays exact audio generated, no re-TTS)
- ✅ Button visible ONLY after phrase was spoken
- ✅ User can click repeatedly to hear multiple times
- ✅ Replays EXACT audio that was generated
- ✅ ONLY works during "teaching" state
- ✅ ONLY for tars_normal mode (lesson mode)
- ✅ Frontend-only change (no backend modification)

## Files Modified

### 1. `frontend/src/components/ConversationContainer.tsx`
**Changes:**
- Extended `Message` interface with `audio_b64?: string[]` and `isTeaching?: boolean`
- Added `currentTeachingMsgId` ref to track current teaching message
- Modified all 3 WebSocket handlers (pre-warm, cold path, reconnect) to:
  - Detect teaching messages (contains `**` and `Palabra objetivo`)
  - Cache audio chunks in `audio_b64` array when message is teaching
  - Track `currentTeachingMsgId` for caching

**Key Code:**
```typescript
// Detect teaching mode
const isTeaching = updatedText.includes('**') && updatedText.includes('Palabra objetivo');

// Cache audio for teaching messages
if (currentTeachingMsgId.current) {
    setMessages(prev => prev.map(msg => 
        msg.id === currentTeachingMsgId.current 
            ? { ...msg, audio_b64: [...(msg.audio_b64 || []), data.audio_b64] }
            : msg
    ));
}
```

### 2. `frontend/src/components/VoiceConversationScreen.tsx`
**Changes:**
- Added `teachingMsg` derivation (finds last teaching message with audio)
- Added `isReplaying` state and replay refs
- Added `replayTeachingAudio()` function to replay cached audio
- Added repeat button (🔁 icon) to footer controls
- Button only shows when `teachingMsg` exists
- Button disabled while replaying

**Key Code:**
```typescript
const teachingMsg = tarsMessages.filter(m => m.isTeaching && m.audio_b64).pop();

const replayTeachingAudio = () => {
    if (!teachingMsg?.audio_b64 || isReplaying) return;
    replayAudioRef.current = teachingMsg.audio_b64;
    replayIndexRef.current = 0;
    setIsReplaying(true);
    playNextReplayChunk();
};
```

### 3. `frontend/src/components/ConversationScreen.tsx`
**Changes:**
- Added `isReplaying` state (Record for per-message tracking)
- Added `replayTeachingAudio()` and `playNextReplayChunk()` functions
- Added repeat button to TARS message bubble (in toggle menu)
- Button shows "🔁 Repeat" and "Replaying..." while playing
- Button only appears for teaching messages with cached audio

**Key Code:**
```typescript
{isActive && m.isTeaching && m.audio_b64 && (
    <button 
        className={`toggle-btn ${isReplaying[m.id] ? 'btn-on' : ''}`}
        onClick={(e) => {
            e.stopPropagation();
            replayTeachingAudio(m.audio_b64!, m.id);
        }}
        disabled={isReplaying[m.id]}
    >
        {isReplaying[m.id] ? 'Replaying...' : '🔁 Repeat'}
    </button>
)}
```

### 4. `frontend/src/components/VoiceConversationScreen.css`
**Changes:**
- Added `.voice-repeat-btn` styles (red theme to match teaching context)
- Added hover/active states
- Added disabled state styling
- Added gap between repeat and history buttons in footer

### 5. `frontend/src/components/ConversationScreen.css`
**Changes:**
- Added `.toggle-btn:disabled` styling
- Added hover state for repeat button (red tint)

## How It Works

### Detection
- Backend sends messages with `**target_word**` pattern and "Palabra objetivo" text
- Frontend detects this pattern to mark messages as `isTeaching = true`
- Only these messages get the repeat button

### Caching
1. When `audio_chunk` received via WebSocket during teaching message
2. Audio `base64` is appended to `message.audio_b64[]`
3. When user clicks repeat, all chunks are played in sequence
4. Same audio data that was originally generated is replayed

### User Flow
1. TARS teaches a 3-word phrase (e.g., "我是老师")
2. Audio plays automatically
3. Repeat button appears (voice screen footer OR text chat bubble menu)
4. User clicks → exact audio replays
5. User can click multiple times
6. Next teaching phrase → old button disappears, new one appears

## Build Verification

```bash
cd frontend && npm run build
# ✅ Build successful - 1782 modules transformed
# ✅ TypeScript compilation passed
# ✅ No errors
```

## Testing Checklist

- [ ] Start lesson mode session
- [ ] Verify 3-word phrase is spoken with audio
- [ ] Verify repeat button appears after phrase is spoken
- [ ] Click repeat button → should replay exact audio
- [ ] Click multiple times → should replay each time
- [ ] Answer correctly (advance to next word) → repeat button for OLD phrase should disappear
- [ ] Verify button only shows in lesson mode (tars_normal)
- [ ] Test in both Voice and Text chat screens
