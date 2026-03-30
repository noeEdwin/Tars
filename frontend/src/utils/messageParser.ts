export interface ParsedMessage {
    original: string;
    chinese: string;
    pinyin: string | null;
    translation: string | null;
    explanation: string | null;
}

export function parseTarsMessage(text: string): ParsedMessage {
    const lines = text.split('\n');
    const chineseLines: string[] = [];
    const pinyinLines: string[] = [];
    const translationLines: string[] = [];
    const explanationLines: string[] = [];

    for (let i = 0; i < lines.length; i++) {
        const line = lines[i];
        const trimmed = line.trim();

        if (!trimmed) {
            // Preserve empty lines in explanation if we've started collecting it
            if (explanationLines.length > 0) explanationLines.push('');
            continue;
        }

        if (trimmed.startsWith('(') && trimmed.endsWith(')')) {
            pinyinLines.push(trimmed.slice(1, -1)); // Remove the parentheses for cleaner rendering
        } else if (trimmed.startsWith('[') && trimmed.endsWith(']')) {
            translationLines.push(trimmed.slice(1, -1)); // Remove the brackets
        } else {
            // If we haven't seen pinyin or translation yet, it's Chinese. Otherwise, it's explanation.
            if (pinyinLines.length === 0 && translationLines.length === 0) {
                chineseLines.push(trimmed);
            } else {
                explanationLines.push(trimmed);
            }
        }
    }

    // Fallback: If no pinyin or translation found, assume everything is just text (could be all Spanish or Chinese)
    if (pinyinLines.length === 0 && translationLines.length === 0) {
        return {
            original: text,
            chinese: chineseLines.join('\n'), // It's safer to map everything to chinese/primary text
            pinyin: null,
            translation: null,
            explanation: null
        };
    }

    return {
        original: text,
        chinese: chineseLines.join('\n'),
        pinyin: pinyinLines.length > 0 ? pinyinLines.join('\n') : null,
        translation: translationLines.length > 0 ? translationLines.join('\n') : null,
        explanation: explanationLines.length > 0 ? explanationLines.join('\n') : null
    };
}
