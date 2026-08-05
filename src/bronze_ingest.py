import json
import polars as pl

from datetime import datetime
from mal_client import MALClient

def bronze_ingest(
    client: MALClient,
    connection: str,
    table_name: str,
    year: int,
    season: str
):
    """
    Ingests seasonal anime data from the MyAnimeList API into a Bronze table.

    Retrieves seasonal anime data for the specified year and season, serializes the
    raw API response to JSON, and appends it to the specified Bronze table along
    with the current ingestion timestamp.

    year: The year of the seasonal anime to retrieve (e.g., 2026).
    season: The anime season to retrieve. Expected values are
        "winter", "spring", "summer", or "fall".
    """
    response = client.get_seasonal_anime(year, season)
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
