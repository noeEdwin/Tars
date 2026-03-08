import json
import re

def clean_and_map_hsk1(input_json, output_json):
    with open(input_json, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 1. Stop words to remove from vocabulary
    stop_words = {
        "一", "二", "三", "四", "五", "六", "七", "八", "九", "十", "百", "千",
        "例如", "课文", "加", "注意", "变为", "情况", "本", "书", "方式", "标准", "句", "相似", 
        "文化", "比如", "地点", "出", "全", "中", "地", "上", "下", "左", "右", "对", "是", "不",
        "有", "没", "在", "大", "小", "多", "少", "好", "来", "去", "回", "想", "能", "会", "都",
        "很", "太", "就", "才", "和", "让", "把", "给", "从", "到", "由于", "为", "比", "这", "那",
        "哪", "谁", "什么", "怎么", "的", "了", "吗", "呢", "啊", "吧"
    }
    
    # We want to keep core vocabulary but remove technical/noise words.
    # Actually, many words above like "这", "哪", "上" ARE HSK 1 VOCABULARY.
    # Let's ONLY filter out the specific technical noise words requested by the user.
    technical_stop_words = {
        "例如", "课文", "加", "注意", "变为", "情况", "方式", "标准", "相似", "文化", "比如", "全"
    }

    # 2. Spanish Translations for Titles
    title_translations = {
        1: "Hola",
        2: "Gracias",
        3: "¿Cómo te llamas?",
        4: "Ella es mi profesora de chino",
        5: "Su hija tiene veinte años este año",
        6: "Sé hablar chino",
        7: "¿A qué estamos hoy?",
        8: "Quiero beber té",
        9: "¿Dónde trabaja tu hijo?",
        10: "¿Puedo sentarme aquí?",
        11: "¿Qué hora es ahora?",
        12: "¿Qué tiempo hará mañana?",
        13: "Él está aprendiendo a cocinar comida china",
        14: "Ella compró bastante ropa",
        15: "Vine en avión"
    }

    # 3. Grammar mapping dictionary
    # Maps specific lesson identifiers or keywords from raw text to standard `hsk30-grammar.csv` rules.
    # The grammar_keywords uses simple substring matching.
    grammar_keywords = {
        "什么": "疑问代词",
        "哪国人": "疑问代词",
        "呢": "用“呢”构成的省略式疑问句“代词/名词+呢？”提问",
        "几": "用“多、多少、几、哪、哪儿、哪里、哪些、什么、谁、怎么”提问",
        "多大": "疑问代词",
        "会": "能愿动词",
        "怎么": "疑问代词",
        "号": "（1）年、月、日、星期表示法",
        "星期": "（1）年、月、日、星期表示法",
        "想": "能愿动词",
        "多少": "疑问代词",
        "个": "名量词",
        "哪儿": "疑问代词",
        "里没有": "存现句",
        "上没有": "存现句",
        "下没有": "存现句",
        "上有": "存现句",
        "前没有": "存现句",
        "能坐这儿吗": "能愿动词",
        "请": "祈使句",
        "几点": "（2）钟点表示法",
        "几分": "（2）钟点表示法",
        "前": "引出时间、处所",
        "怎么样": "疑问代词",
        "太冷了": "程度副词",
        "在做": "进行态",
        "在学": "进行态",
        "吧": "用“吧”提问",
        "后": "引出时间、处所",
        "张": "名量词",
        "这是": "指示代词",
        "都是": "程度副词"
    }
    
    # Specific hardcoded mappings per lesson (more precise than keywords)
    lesson_grammar_map = {
        1: [],
        2: [],
        3: ["疑问代词"],
        4: ["疑问代词", "指示代词"],
        5: ["疑问代词", "用“多、多少、几、哪、哪儿、哪里、哪些、什么、谁、怎么”提问"],
        6: ["能愿动词"],
        7: ["时间表示法（1）年、月、日、星期表示法"],
        8: ["能愿动词", "用“多、多少、几、哪、哪儿、哪里、哪些、什么、谁、怎么”提问", "名量词"],
        9: ["疑问代词", "方位名词"],
        10: ["方位名词", "存现句", "能愿动词", "用“吗”提问"],
        11: ["时间表示法（2）钟点表示法"],
        12: ["疑问代词"],
        13: ["进行态", "用“吧”提问"],
        14: ["完成态", "引出时间、处所"],
        15: ["“是……的”句1：强调时间、地点、方式、动作者"]
    }

    for lesson in data.get("lecciones", []):
        lesson_id = lesson.get("lesson_id")
        
        # Translate title
        lesson["titulo_es"] = title_translations.get(lesson_id, lesson.get("titulo_original"))

        # Clean vocabulary
        original_vocab = lesson.get("vocabulario_extraido", [])
        clean_vocab = [word for word in original_vocab if word not in technical_stop_words]
        lesson["vocabulario_extraido"] = clean_vocab

        # Map Grammar
        # Since the OCR text was messy, we will just apply the highly accurate hardcoded map per lesson
        # based on the HSK 1 curriculum map.
        mapped_grammar = lesson_grammar_map.get(lesson_id, [])
        lesson["gramatica_claves"] = mapped_grammar

    # Save cleaned JSON
    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"Data cleaned and mapped. Saved to {output_json}")

if __name__ == '__main__':
    clean_and_map_hsk1('data/hsk1_map.json', 'data/hsk1_map_clean.json')
