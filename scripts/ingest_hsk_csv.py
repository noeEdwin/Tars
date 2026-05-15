"""
Ingest HSK knowledge base from a CSV file into base_conocimiento.

Usage:
    python scripts/ingest_hsk_csv.py <path_to_csv>
"""
import sys
import logging

import pandas as pd
from dotenv import load_dotenv

from agents.brain.chains import get_embeddings_model
from dataBase.pool import get_db_connection

load_dotenv()

logger = logging.getLogger(__name__)


def ingest_hsk_data(file_path: str):
    """Read a CSV of HSK data, generate embeddings, and insert into base_conocimiento."""
    try:
        embedding_model = get_embeddings_model()
        df = pd.read_csv(file_path)

        logger.info("Starting ingestion of %d rows...", len(df))

        with get_db_connection() as conn:
            cur = conn.cursor()

            for _, row in df.iterrows():
                embedding_vector = embedding_model.embed_query(row["contenido_zh"])

                query = """
                    INSERT INTO base_conocimiento
                    (contenido_zh, pinyin, traduccion_es, nivel_hsk, categoria, tipo_item, embedding)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """
                cur.execute(query, (
                    row["contenido_zh"],
                    row["pinyin"],
                    row["traduccion_es"],
                    int(row["nivel_hsk"]),
                    row["categoria"],
                    row["tipo_item"],
                    embedding_vector,
                ))

            conn.commit()

        logger.info("Ingestion completed successfully in Postgres.")

    except Exception as e:
        logger.error("Error during ingestion: %s", e)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    if len(sys.argv) < 2:
        print("Usage: python scripts/ingest_hsk_csv.py <path_to_csv>")
        sys.exit(1)

    ingest_hsk_data(sys.argv[1])
