import asyncio
import json
import os
import psycopg2
from openai import AsyncOpenAI
from dotenv import load_dotenv
from agents.dataBase.pool import get_db_connection
from agents.brain.chains import get_embeddings_model

load_dotenv()

# Configuración      
API_KEY = os.environ.get("DEEPSEEK_API_KEY")
CONCURRENCY_LIMIT = 10 

async def procesar_fila(sem, client, embedder, row):
    row_id, es_text, current_emocion, current_contexto, current_embedding = row
    
    async with sem:
        try:
            nueva_emocion = current_emocion
            nuevo_contexto = current_contexto
            nuevo_embedding = current_embedding

            # 1. Si falta emoción o contexto, llamar a DeepSeek
            if not current_emocion or not current_contexto:
                prompt = f"""Analiza: "{es_text}". Devuelve SOLO JSON: {{"emocion": "...", "contexto": "..."}}"""
                response = await client.chat.completions.create(
                    model="deepseek-chat",
                    messages=[{"role": "user", "content": prompt}],
                    response_format={"type": "json_object"},
                    temperature=0.0
                )
                metadata = json.loads(response.choices[0].message.content)
                nueva_emocion = metadata.get('emocion', 'neutro')
                nuevo_contexto = metadata.get('contexto', 'general')

            # 2. Si falta el embedding, generarlo
            if current_embedding is None:
                nuevo_embedding = embedder.embed_query(es_text)

            return (row_id, nueva_emocion, nuevo_contexto, nuevo_embedding)
            
        except Exception as e:
            print(f"❌ Error en ID {row_id}: {e}")
            return None

async def main():
    print("🔗 Conectando a Supabase...")
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Buscamos filas donde FALTE ALGO (OR)
    query_select = """
        SELECT id, es, emocion, contexto, embedding 
        FROM translations_mvp 
        WHERE emocion IS NULL OR contexto IS NULL OR embedding IS NULL
    """
    cur.execute(query_select)
    rows = cur.fetchall()
    
    if not rows:
        print("✨ ¡Todo está al 100%! No hay NULLs en emoción, contexto o embeddings.")
        return

    print(f"🚀 Procesando {len(rows)} filas que tienen datos faltantes...")
    client = AsyncOpenAI(api_key=API_KEY, base_url="https://api.deepseek.com")
    embedder = get_embeddings_model()
    sem = asyncio.Semaphore(CONCURRENCY_LIMIT)
    
    tareas = [procesar_fila(sem, client, embedder, row) for row in rows]
    resultados = []

    for f in asyncio.as_completed(tareas):
        res = await f
        if res:
            resultados.append(res)
            print(f"✅ ID {res[0]} completado.")

    print("\n💾 Guardando cambios en la base de datos...")
    update_query = """
        UPDATE translations_mvp 
        SET emocion = %s, contexto = %s, embedding = %s 
        WHERE id = %s
    """
    for res in resultados:
        cur.execute(update_query, (res[1], res[2], res[3], res[0]))
        
    conn.commit()
    cur.close()
    conn.close()
    print("🎊 ¡Base de datos sincronizada y completa!")

if __name__ == "__main__":
    asyncio.run(main())