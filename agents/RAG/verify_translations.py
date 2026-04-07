import asyncio
import json
from openai import AsyncOpenAI
import psycopg2 # Asumo que usas psycopg2 en connection.py
from agents.dataBase.connection import get_db_connection
from agents.brain.chains import get_embeddings_model
import os

# Configuración
API_KEY = os.environ.get("DEEPSEEK_API_KEY")
CONCURRENCY_LIMIT = 20 

async def procesar_dialogo(sem, client, embedder, row):
    row_id, es_text = row
    
    # El semáforo evita que hagamos 3000 peticiones de golpe y nos bloqueen
    async with sem:
        try:
            # 1. Obtener Emoción y Contexto
            prompt = f"""
            Analiza este diálogo: "{es_text}".
            Devuelve SOLO un JSON con dos claves:
            - "emocion": (sarcástico, motivacional, directo, inseguro, seductor, neutro)
            - "contexto": (presentacion, rechazo, consejo, pregunta, exclamacion)
            """
            
            response = await client.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                temperature=0.0
            )
            
            metadata = json.loads(response.choices[0].message.content)
            
            # 2. Generar Embedding (Esta llamada es síncrona, pero rápida)
            vector = embedder.embed_query(es_text)
            
            return (row_id, metadata.get('emocion', 'neutro'), metadata.get('contexto', 'general'), vector)
            
        except Exception as e:
            print(f"Error en ID {row_id}: {e}")
            return None

async def main():
    print("Conectando a la base de datos...")
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("SELECT id, es FROM translations_mvp WHERE embedding IS NULL")
    rows = cur.fetchall()
    
    if not rows:
        print("Todos los diálogos ya están procesados.")
        return

    print(f"Iniciando procesamiento de {len(rows)} diálogos asíncronamente...")
    
    client = AsyncOpenAI(api_key=API_KEY, base_url="https://api.deepseek.com")
    embedder = get_embeddings_model()
    sem = asyncio.Semaphore(CONCURRENCY_LIMIT)
    
    # Crear todas las tareas asíncronas
    tareas = [procesar_dialogo(sem, client, embedder, row) for row in rows]
    
    # Ejecutarlas y esperar resultados (con una pequeña barra de progreso en consola)
    resultados = []
    for f in asyncio.as_completed(tareas):
        res = await f
        if res:
            resultados.append(res)
            print(f"Procesado ID: {res[0]} | Emoción: {res[1]}")

    # Guardar en base de datos en bloque (mucho más eficiente)
    print("\nGuardando resultados en Postgres...")
    update_query = """
        UPDATE translations_mvp 
        SET emocion = %s, contexto = %s, embedding = %s 
        WHERE id = %s
    """
    
    for res in resultados:
        row_id, emocion, contexto, vector = res
        cur.execute(update_query, (emocion, contexto, vector, row_id))
        
    conn.commit()
    cur.close()
    conn.close()
    print("¡Base de datos de estilo actualizada con éxito!")

if __name__ == "__main__":
    asyncio.run(main())