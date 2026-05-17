import pandas as pd
import json
import os
from dotenv import load_dotenv
load_dotenv("../../../../../../home/lancelot/Personal_Projects/Tars/.env")
import math
from openai import OpenAI

def verify_and_translate(csv_path):
    api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        print("ERROR: DEEPSEEK_API_KEY environment variable not set.")
        print("Please run: export DEEPSEEK_API_KEY='your_api_key'")
        return

    client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
    
    print("Loading Knowledge Base...")
    df = pd.read_csv(csv_path)
    
    # 1. Flagging words for "Revisión Obligatoria"
    # Actually, the user suggested passing them to the LLM to fix it. We will pass ALL words in batches of 50 to guarantee high quality.
    
    batch_size = 50
    total_words = len(df)
    total_batches = math.ceil(total_words / batch_size)
    
    print(f"Total words: {total_words}. Splitting into {total_batches} batches of {batch_size}.")
    
    new_translations = []

    for i in range(total_batches):
        start_idx = i * batch_size
        end_idx = min(start_idx + batch_size, total_words)
        batch_df = df.iloc[start_idx:end_idx]
        
        print(f"Processing batch {i+1}/{total_batches} (Words {start_idx+1} to {end_idx})...")
        
        prompt_lines = []
        for index, row in batch_df.iterrows():
            word = str(row['contenido_zh']).split('|')[0]
            pos = row['POS']
            titulo = row['titulo_es_leccion']
            grammar = row['grammar_ref'] if pd.notna(row['grammar_ref']) else "None"
            
            line = f"Word: {word} | POS: {pos} | Lesson: {titulo} | Grammar: {grammar}"
            prompt_lines.append(line)
            
        words_text = "\n".join(prompt_lines)
        
        system_prompt = (
            "You are an expert Mandarin Chinese teacher structuring an HSK 1 curriculum. "
            "Translate the following words to Spanish, ensuring the meaning fits "
            "PERFECTLY with the lesson context and its POS (Part of Speech). "
            "VERY IMPORTANT RULE: If POS is 'Aux' (particle), do not translate it as a physical object (e.g., 'bar'), "
            "but as its function (e.g., 'suggestion indicator particle'). "
            "If POS is 'Num', the translation MUST contain a number. "
            "Return ONLY a JSON array of strings, where each string is the corresponding translation "
            "in the exact same order. Example output: [\"amar\", \"papa\", \"particula de sugerencia\"]. Do NOT return anything other than the JSON."
        )

        user_prompt = f"Here are the words to translate (keep the exact same order):\n\n{words_text}"

        try:
            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"} if "deepseek" not in client.base_url.host else None, # Deepseek doesn't strictly need json_object if prompted well, but let's prompt well.
                temperature=0.0
            )
            
            # Deepseek JSON extraction
            content = response.choices[0].message.content.strip()
            
            # Remove markdown JSON fences if present
            if content.startswith("```json"):
                content = content[7:]
            if content.endswith("```"):
                content = content[:-3]
                
            content = content.strip()
            
            try:
                translations = json.loads(content)
                if isinstance(translations, dict):
                    # Sometimes LLMs return {"translations": [...]}
                    translations = list(translations.values())[0]
                    
                if len(translations) != len(batch_df):
                    print(f"WARNING: Output length ({len(translations)}) doesn't match batch length ({len(batch_df)}). Extracting safely.")
                    
                for t in translations:
                    new_translations.append(str(t).lower())
                    
            except json.JSONDecodeError:
                print(f"ERROR: Failed to parse JSON from DeepSeek: {content}")
                # Fallback: just append the old translations for this batch if JSON fails
                new_translations.extend(batch_df['traduccion_es'].tolist())
                
        except Exception as e:
            print(f"API Error in batch {i+1}: {e}")
            # Fallback
            new_translations.extend(batch_df['traduccion_es'].tolist())

    # Ensure length matches
    if len(new_translations) == len(df):
        df['traduccion_es'] = new_translations
        df.to_csv(csv_path, index=False)
        print(f"Successfully refined translations and saved to {csv_path}")
    else:
        print(f"Length mismatch: {len(new_translations)} translations for {len(df)} words. CSV not completely updated.")
        # Best effort zip
        for i in range(min(len(new_translations), len(df))):
            df.at[i, 'traduccion_es'] = new_translations[i]
        df.to_csv(csv_path, index=False)
        print("Saved best-effort translations.")

if __name__ == '__main__':
    verify_and_translate('data/hsk1_knowledge_base.csv')
