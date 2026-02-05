import pandas as pd
from dotenv import load_dotenv
from agents.brain.chains import get_embeddings_model
from agents.dataBase.connection import get_db_connection

load_dotenv()

def ingest_hsk_data(file_path):
    try:
        embedding_model = get_embeddings_model()
        df = pd.read_csv(file_path)
        conn = get_db_connection()
        cur = conn.cursor()

        print(f"🚀 Iniciando ingesta de {len(df)} filas...")

        for _, row in df.iterrows():
            # 2. Generar el embedding (1536 dimensiones para text-embedding-3-small)
            embedding_vector = embedding_model.embed_query(row['contenido_zh'])

            # 3. Insertar con Taxonomía completa
            query = """
                INSERT INTO base_conocimiento 
                (contenido_zh, pinyin, traduccion_es, nivel_hsk, categoria, tipo_item, embedding)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            cur.execute(query, (
                row['contenido_zh'], 
                row['pinyin'], 
                row['traduccion_es'], 
                int(row['nivel_hsk']), 
                row['categoria'], 
                row['tipo_item'], 
                embedding_vector
            ))

        conn.commit()
        cur.close()
        conn.close()
        print("✅ Ingesta completada con éxito en Postgres.")

    except Exception as e:
        print(f"❌ Error durante la ingesta: {e}")

if __name__ == "__main__":
    ingest_hsk_data('/home/lancelot/Personal_Studies/Chinese_studies/Chinese_Videos.csv')