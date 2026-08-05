import json
import polars as pl

from datetime import datetime
from mal_client import MALClient

def bronze_ingest_rankings(
        client: MALClient,
        connection: str,
        table_name: str,
        ranking_type: str,
        limit: int
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

    df = pl.DataFrame(
        {
            "ingested_at": [datetime.now()],
            "raw_json": [json.dumps(data)]
        }
    )

    df.write_database(
        table_name=table_name,
        connection=connection,
        if_table_exists="append"
    )
