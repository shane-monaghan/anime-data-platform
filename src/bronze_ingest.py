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
