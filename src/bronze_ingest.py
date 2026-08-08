import json
from datetime import datetime

import polars as pl

from mal_client import MALClient
from database_manager import DatabaseManager


def bronze_ingest_rankings(
    client: MALClient, db_manager: DatabaseManager, table_name: str, ranking_type: str, limit: int
) -> None:
    """
    Ingests anime ranking data from the MyAnimeList API into a Bronze table.

    Retrieves anime ranking data, serializes the
    raw API response to JSON, and appends it to the specified Bronze table along
    with the current ingestion timestamp.

    ranking_type: the type of ranking requested(all, airing, etc)
    limit: the number of anime to return (limit of 500)
    """
    response = client.get_rankings(ranking_type, limit)
    data = response.json()

    df = pl.DataFrame({"ingested_at": [datetime.now()], "raw_json": [json.dumps(data)]})

    db_manager.write(table_name=table_name, df=df)
