import pandas as pd
import json
from deep_translator import GoogleTranslator

def build_hsk_master(csv_path, json_path, output_path):
    print("Loading data...")
    # Load CSV and filter to HSK 1 only (based on ID prefix)
    df_all = pd.read_csv(csv_path)
    df = df_all[df_all['ID'].astype(str).str.startswith('L1-')].copy()
    
    with open(json_path, 'r', encoding='utf-8') as f:
        json_data = json.load(f)

    # Hardcoded Grammar Mapping based on previous review of hsk30-grammar.csv
    grammar_lookup = {
        "疑问代词": "G1.4",
        "指示代词": "G1.6",
        "用“多、多少、几、哪、哪儿、哪里、哪些、什么、谁、怎么”提问": "G1.46",
        "能愿动词": "G1.2",
        "时间表示法（1）年、月、日、星期表示法": "G1.44",
        "名量词": "G1.8",
        "方位名词": "G1.1",
        "存现句": "G1.37",
        "用“吗”提问": "G1.45",
        "时间表示法（2）钟点表示法": "G1.44",
        "进行态": "G1.42",
        "用“吧”提问": "G1.22",
        "完成态": "G1.41",
        "引出时间、处所": "G1.15",
        "“是……的”句1：强调时间、地点、方式、动作者": "G1.36"
    }
    
    # Initialize columns
    df['lesson_id'] = 0
    df['grammar_ref'] = None
    df['titulo_es_leccion'] = "Vocabulario General"
    
    print("Mapping Vocabulary to Lessons...")
    for idx, row in df.iterrows():
        variants = str(row['contenido_zh']).split('|')
        found = False
        
        for var in variants:
            var = var.strip()
            for lesson in json_data.get('lecciones', []):
                # Using broad search within string just in case, but strict match is safer for short Hanzi
                if var in lesson.get('vocabulario_extraido', []):
                    df.at[idx, 'lesson_id'] = lesson['lesson_id']
                    df.at[idx, 'titulo_es_leccion'] = lesson.get('titulo_es', '')
                    
                    # Map Grammar
                    refs = []
                    for g in lesson.get('gramatica_claves', []):
                        if g in grammar_lookup:
                            refs.append(grammar_lookup[g])
                    if refs:
                        df.at[idx, 'grammar_ref'] = " | ".join(refs)
                        
                    found = True
                    break
            if found:
                break
                
    # Balance Cognitive Load (Split lessons with > 15 words)
    print("Balancing Cognitive Load...")
    # Because we want to store floats or strings like '1.1', we change type to object
    df['lesson_id'] = df['lesson_id'].astype(object)
    
    for l_id in range(1, 16):
        mask = df['lesson_id'] == l_id
        indices = df[mask].index.tolist()
        if len(indices) > 15:
            chunk_size = 15
            for i, chunk_idx in enumerate(range(0, len(indices), chunk_size)):
                sub_lesson = f"{l_id}.{i+1}"
                chunk = indices[chunk_idx:chunk_idx + chunk_size]
                df.loc[chunk, 'lesson_id'] = sub_lesson

    # Translate Vocabulary to Spanish
    print("Translating Vocabulary to Spanish...")
    translator = GoogleTranslator(source='zh-CN', target='es')
    # Use first variant for translation
    words_to_translate = [str(x).split('|')[0].strip() for x in df['contenido_zh'].values]
    
    try:
        # Batch translation
        translations = translator.translate_batch(words_to_translate)
        df['traduccion_es'] = [t.lower() if t else '' for t in translations]
    except Exception as e:
        print(f"Batch translation failed: {e}. Falling back to single queries...")
        translations = []
        for w in words_to_translate:
            try:
                translations.append(translator.translate(w).lower())
            except:
                translations.append('')
        df['traduccion_es'] = translations

    # Reorder parameters for clarity
    cols = ['ID', 'lesson_id', 'contenido_zh', 'Pinyin', 'traduccion_es', 'POS', 'grammar_ref', 'titulo_es_leccion']
    # If Level exists, keep it, though our filter removes it earlier. Let's just output the specified ones.
    available_cols = [c for c in cols if c in df.columns]
    
    df_out = df[available_cols]
    
    df_out.to_csv(output_path, index=False)
    print(f"Successfully generated Master Knowledge Base at: {output_path}")

if __name__ == '__main__':
    build_hsk_master('data/hsk_30_clean.csv', 'data/hsk1_map_clean.json', 'data/hsk1_knowledge_base.csv')
