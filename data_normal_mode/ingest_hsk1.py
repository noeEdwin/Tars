import sys
import os
import pandas as pd
from dotenv import load_dotenv
import math

from agents.brain.chains import get_embeddings_model
from agents.dataBase.pool import get_db_connection

load_dotenv(os.path.abspath(os.path.join(os.path.dirname(__file__), '../.env')))

def setup_database(cur):
    print("Migrating Database Schema...")
    alter_queries = [
        "ALTER TABLE base_conocimiento ADD COLUMN IF NOT EXISTS lesson_id VARCHAR(50);",
        "ALTER TABLE base_conocimiento ADD COLUMN IF NOT EXISTS grammar_ref TEXT;",
        "ALTER TABLE base_conocimiento ADD COLUMN IF NOT EXISTS pos TEXT;",
        "ALTER TABLE base_conocimiento ADD COLUMN IF NOT EXISTS titulo_es_leccion TEXT;"
    ]
    for q in alter_queries:
        cur.execute(q)
        
    print("Cleaning up old HSK 1 test data...")
    cur.execute("DELETE FROM base_conocimiento WHERE nivel_hsk = 1 OR lesson_id IS NOT NULL;")
    print(f"Deleted old rows.")

def ingest_hsk1_knowledge_base(file_path):
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        setup_database(cur)
        conn.commit()
    except Exception as e:
        print(f"Error during schema migration: {e}")
        conn.rollback()
        cur.close()
        conn.close()
        return

    try:
        embedding_model = get_embeddings_model()
        df = pd.read_csv(file_path)
        df = df.fillna('')

        print(f"Starting BATCH semantic ingestion of {len(df)} rows...")

        batch_size = 100
        total_batches = math.ceil(len(df) / batch_size)

        for i in range(total_batches):
            start_idx = i * batch_size
            end_idx = min(start_idx + batch_size, len(df))
            batch_df = df.iloc[start_idx:end_idx]

            print(f"Processing batch {i+1}/{total_batches}...")

            # Prepare texts for batch embedding
            texts_to_embed = []
            for _, row in batch_df.iterrows():
                embed_text = f"{row['contenido_zh']} - {row['traduccion_es']} ({row['POS']})"
                texts_to_embed.append(embed_text)

            # Generate batch embeddings
            embeddings = embedding_model.embed_documents(texts_to_embed)

            # Insert batch
            query = """
                INSERT INTO base_conocimiento 
                (contenido_zh, pinyin, traduccion_es, nivel_hsk, categoria, tipo_item, embedding, lesson_id, grammar_ref, pos, titulo_es_leccion)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            for j, (_, row) in enumerate(batch_df.iterrows()):
                nivel_hsk = 1
                lesson_id = str(row['lesson_id']) if str(row['lesson_id']) != '0.0' else '0'
                if lesson_id.endswith('.0'):
                    lesson_id = lesson_id[:-2]
                    
                cur.execute(query, (
                    row['contenido_zh'], 
                    row['Pinyin'], 
                    row['traduccion_es'], 
                    nivel_hsk, 
                    "Vocabulary",
                    "Word", 
                    embeddings[j],
                    lesson_id,
                    row['grammar_ref'],
                    row['POS'],
                    row['titulo_es_leccion']
                ))

            conn.commit()
            print(f"Batch {i+1} inserted.")

        print("Semantic ingestion completed successfully in Postgres.")

    except Exception as e:
        print(f"Error during ingestion: {e}")
        conn.rollback()
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    csv_path = os.path.join(os.path.dirname(__file__), 'data/hsk1_knowledge_base.csv')
    ingest_hsk1_knowledge_base(csv_path)
