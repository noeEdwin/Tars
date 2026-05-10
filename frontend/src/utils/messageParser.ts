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

    let hasSeenPinyinOrTranslation = false;
    const hasChineseChar = (str: string) => /[\u4e00-\u9fa5]/.test(str);

    for (let i = 0; i < lines.length; i++) {
        const line = lines[i];
        const trimmed = line.trim();

        if (!trimmed) {
            if (explanationLines.length > 0) explanationLines.push('');
            continue;
        }

        if (trimmed.startsWith('(') && trimmed.endsWith(')')) {
            pinyinLines.push(trimmed.slice(1, -1));
            hasSeenPinyinOrTranslation = true;
        } else if (trimmed.startsWith('[') && trimmed.endsWith(']')) {
            translationLines.push(trimmed.slice(1, -1));
            hasSeenPinyinOrTranslation = true;
        } else {
            // Si la línea contiene caracteres chinos, siempre va a 'chinese'
            if (hasChineseChar(trimmed)) {
                chineseLines.push(trimmed);
            } 
            // Si aún no hemos visto pinyin ni traducción, asumimos que es texto principal/chino
            else if (!hasSeenPinyinOrTranslation) {
                chineseLines.push(trimmed);
            } 
            // Si ya vimos pinyin o traducción y no tiene caracteres chinos, es explicación
            else {
                explanationLines.push(trimmed);
            }
        }
    }

    // Fallback: Si no se encontró ni pinyin ni traducción, todo el texto es 'chinese' (o texto principal)
    if (pinyinLines.length === 0 && translationLines.length === 0) {
        return {
            original: text,
            chinese: chineseLines.join('\n') || explanationLines.join('\n'),
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
