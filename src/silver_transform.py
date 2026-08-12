import polars as pl

from database_manager import DatabaseManager


def read_bronze_data(db_manager: DatabaseManager, bronze_table: str) -> list[dict]:
    """Read raw Bronze JSON responses from DuckDB and decode them.

    Args:
        db_manager: DatabaseManager instance used to query DuckDB.
        bronze_table: Name of the Bronze table containing raw JSON payloads.

    Returns:
        List of decoded API response dictionaries,
        each paired with its ingestion timestamp.
    """
    query = f"SELECT * FROM {bronze_table}"
    bronze_df = db_manager.execute(query).pl()
    dict_data = bronze_df["raw_json"].str.json_decode().to_list()

    return [
        {"data": response, "ingested_at": timestamp}
        for response, timestamp in zip(dict_data, bronze_df["ingested_at"].to_list())
    ]


def extract_anime_records(responses: list[dict]) -> list[dict]:
    """Extract individual anime records from decoded Bronze responses.

    Args:
        responses: List of decoded Bronze records, each containing a serialized
            MAL API response and ingestion timestamp.

    Returns:
        Flat list of anime ranking dictionaries with the source ingestion timestamp
        copied into each record.
    """
    all_rows = []

    for response in responses:
        for anime_dict in response["data"]["data"]:
            anime_dict["ingested_at"] = response["ingested_at"]
            all_rows.append(anime_dict)

    return all_rows


def create_decoded_dataframe(all_rows: list[dict]) -> pl.DataFrame:
    """Convert flattened anime records into a Polars DataFrame.

    Args:
        all_rows: List of individual anime ranking records.

    Returns:
        Polars DataFrame with nested MAL payload fields unnested into columns.
    """
    parsed_df = pl.from_dicts(all_rows)
    parsed_df = parsed_df.unnest("node").unnest("ranking").unnest("main_picture")
    return parsed_df


def create_anime_dim_dataframe(parsed_df: pl.DataFrame) -> pl.DataFrame:
    """Create a dimension DataFrame for anime metadata.

    Args:
        parsed_df: Flattened DataFrame containing anime ranking data.

    Returns:
        DataFrame with anime id and title columns.
    """
    anime_dim_df = parsed_df.select("id", "title")
    return anime_dim_df


def create_fact_dataframe(parsed_df: pl.DataFrame) -> pl.DataFrame:
    """Create a fact DataFrame for anime rankings.

    Args:
        parsed_df: Flattened DataFrame containing anime ranking data.

    Returns:
        DataFrame with anime id, rank, and ingestion timestamp.
    """
    fact_df = parsed_df.select("id", "rank", "ingested_at")
    return fact_df


def silver_transform(
    db_manager: DatabaseManager,
    bronze_table: str,
) -> None:
    """Transform Bronze ranked anime payloads into Silver tables.

    Reads raw JSON ranking payloads from the specified Bronze table,
    normalizes the nested records into a flat DataFrame, and writes the
    resulting dimension and fact tables to DuckDB.

    Args:
        db_manager: DatabaseManager instance used to query and write DuckDB tables.
        bronze_table: Name of the Bronze table containing raw ranking payloads.

    Returns:
        None. Creates or updates dim_anime and fact_rankings tables.
    """
    dict_data = read_bronze_data(db_manager=db_manager, bronze_table=bronze_table)
    all_rows = extract_anime_records(dict_data)
    parsed_df = create_decoded_dataframe(all_rows)

    anime_dim_df = create_anime_dim_dataframe(parsed_df)
    fact_df = create_fact_dataframe(parsed_df)

    db_manager.execute(
        """
            CREATE TABLE IF NOT EXISTS dim_anime (
                id INTEGER PRIMARY KEY,
                title VARCHAR
            )
        """
    )

    db_manager.execute(
        """
            CREATE TABLE IF NOT EXISTS fact_rankings (
                id INTEGER,
                rank INTEGER,
                ingested_at TIMESTAMP,
                PRIMARY KEY (id, ingested_at)
            )
        """
    )

    db_manager.write("dim_anime", anime_dim_df, conflict_columns=["id"])
    db_manager.write("fact_rankings", fact_df, conflict_columns=["id", "ingested_at"])
