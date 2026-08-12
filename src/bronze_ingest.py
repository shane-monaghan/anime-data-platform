import json
from datetime import datetime

import polars as pl

from database_manager import DatabaseManager
from mal_client import MALClient


def bronze_ingest_rankings(
    client: MALClient,
    db_manager: DatabaseManager,
    table_name: str,
    ranking_type: str,
    limit: int,
) -> None:
    """Ingest anime ranking data from the MyAnimeList API into a Bronze table.

    Args:
        client: MALClient instance used to call the MAL API.
        db_manager: DatabaseManager instance used to write data to DuckDB.
        table_name: Name of the Bronze table to write raw payloads into.
        ranking_type: Ranking type to request (for example, "all" or "airing").
        limit: Number of anime records to request from the API.

    Returns:
        None. Writes the raw JSON payload and ingestion timestamp to the
        specified Bronze table.
    """
    response = client.get_rankings(ranking_type, limit)
    data = response.json()

    df = pl.DataFrame({"ingested_at": [datetime.now()], "raw_json": [json.dumps(data)]})

    db_manager.write(table_name=table_name, df=df)
