import pytesseract
from pdf2image import convert_from_path
import pandas as pd
import json
import re
import fitz

def extract_hsk1_layered(pdf_path, output_json, ref_csv):
    print("--- Phase A: Structure Detection (Index) ---")
    doc = fitz.open(pdf_path)
    toc = doc.get_toc()
    
    lessons_meta = []
    # Find lessons 1 to 15
    for item in toc:
        level, title, page = item
        # Example title: '1 你好'
        match = re.match(r'^(\d+)\s+(.+)', title)
        if match:
            lesson_id = int(match.group(1))
            if 1 <= lesson_id <= 15:
                lessons_meta.append({
                    "lesson_id": lesson_id,
                    "titulo_original": match.group(2).strip(),
                    "start_page": page
                })
                
    # Calculate end pages
    for i in range(len(lessons_meta)):
        if i < len(lessons_meta) - 1:
            lessons_meta[i]['end_page'] = lessons_meta[i+1]['start_page'] - 1
        else:
            # Find the end by looking at the next TOC item after lesson 15 (e.g., '词语总表' at page 140)
            next_page = 140
            for item in toc:
                if item[1] == '词语总表':
                    next_page = item[2]
            lessons_meta[i]['end_page'] = next_page - 1
            
    print(f"Detected {len(lessons_meta)} lessons.")

    print("\n--- Phase B & C: Vocabulary & Grammar Extraction ---")
    # Load reference vocabulary to filter Hanzi effectively
    df_ref = pd.read_csv(ref_csv)
    valid_hanzi = set()
    for item in df_ref['contenido_zh'].dropna():
        for variant in str(item).split('|'):
            clean_var = re.sub(r'[^\u4e00-\u9fff]', '', variant.strip())
            if clean_var: valid_hanzi.add(clean_var)
    
    book_data = {
        "metadatos": {
            "libro": "HSK 1 Standard Course",
            "total_lecciones": len(lessons_meta)
        },
        "lecciones": []
    }

    # Iterate through lessons
    for meta in lessons_meta:
        l_id = meta['lesson_id']
        print(f"\nProcessing Lesson {l_id}: {meta['titulo_original']} (Pages {meta['start_page']} - {meta['end_page']})")
        
        vocab_set = set()
        grammar_list = []
        
        # Convert only the pages for this lesson
        # fitz pages are 1-indexed in TOC, pdf2image uses 1-based indexing for first_page and last_page
        images = convert_from_path(pdf_path, first_page=meta['start_page'], last_page=meta['end_page'], dpi=200)
        
        grammar_section = False
        vocab_section = False
        
        for pnum, img in enumerate(images, start=meta['start_page']):
            # For grammar, uniform blocks work better (psm 3 or 6). For vocab tables, psm 4 or 6. 
            text = pytesseract.image_to_string(img, lang='chi_sim+eng', config='--psm 3')
            lines = text.split('\n')
            
            for line in lines:
                line = line.strip()
                if not line: continue
                
                # Check for section markers
                if re.search(r'(New Words|词汇|生词)', line, re.IGNORECASE):
                    vocab_section = True
                    grammar_section = False
                    continue
                if re.search(r'(Grammar|Language Points|语法|注释)', line, re.IGNORECASE):
                    grammar_section = True
                    vocab_section = False
                    continue
                if re.search(r'(Exercises|练习|运用|Characters|汉字|Application)', line, re.IGNORECASE):
                    vocab_section = False
                    grammar_section = False
                    continue
                
                # Phase C: Grammar title extraction
                if grammar_section:
                    # Looking for numbered items like "1. The Modal Verb 会" or "1. 疑问代词"
                    # But ignoring pure english if we only want Chinese grammar concepts, or keep the english title.
                    match = re.match(r'^[\(]?\d+[\.\)]?\s*([^\.]+.*)$', line)
                    if match:
                        point = match.group(1).strip()
                        # Filter out basic noise
                        if len(point) < 40 and point not in grammar_list:
                            # A good grammar point usually contains some Chinese chars, or is a clear title
                            if any('\u4e00' <= c <= '\u9fff' for c in point) or "The " in point:
                                grammar_list.append(point)
                
                # Phase B: Vocab chunk finding (Can happen anywhere since tables are tricky)
                # Instead of strictly requiring vocab_section (which may fail if OCR misses "New Words"),
                # we just scan all lines that aren't grammar/exercises for valid hanzi strings.
                if vocab_section or not grammar_section:
                    chars = [c for c in line if '\u4e00' <= c <= '\u9fff']
                    if chars:
                        # Extract all contiguous blocks of hanzi
                        hanzi_blocks = re.findall(r'[\u4e00-\u9fff]+', line)
                        for block in hanzi_blocks:
                            if block in valid_hanzi:
                                # We enforce that the line shouldn't be too long (to avoid grammar/sentences)
                                if len(line) < 50:
                                    vocab_set.add(block)

        lesson_data = {
            "lesson_id": l_id,
            "titulo_original": meta['titulo_original'],
            "vocabulario_extraido": list(vocab_set),
            "gramatica_claves": grammar_list
        }
        book_data['lecciones'].append(lesson_data)

    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump(book_data, f, ensure_ascii=False, indent=2)
    print(f"\nExtraction complete! Saved to {output_json}")

if __name__ == '__main__':
    extract_hsk1_layered('data/HSK-1-Textbook.pdf', 'data/hsk1_map.json', 'data/hsk_30_clean.csv')
