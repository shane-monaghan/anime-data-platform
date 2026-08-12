import polars as pl

from database_manager import DatabaseManager


def read_bronze_data(db_manager: DatabaseManager, bronze_table: str) -> list[dict]:
    """
    Reads and decodes raw JSON responses from a Bronze DuckDB table.

    Assumes the table contains a raw_json column containing serialized
    MyAnimeList API response payloads.

    Args:
        db_manager: A DatabaseManager instance.
        bronze_table: Name of the Bronze table to read.

    Returns:
        List of decoded API response dictionaries.
    """
    query = f"SELECT * FROM {bronze_table}"
    bronze_df = db_manager.execute(query).pl()
    dict_data = bronze_df["raw_json"].str.json_decode().to_list()

    return [
        {"data": response, "ingested_at": timestamp}
        for response, timestamp in zip(dict_data, bronze_df["ingested_at"].to_list())
    ]


def extract_anime_records(responses: list[dict]) -> list[dict]:
    """
    Extracts individual anime records from MyAnimeList API responses.

    Assumes each response contains a data field containing a list of
    anime ranking records.

    Args:
        responses: Decoded MyAnimeList API responses.

    Returns:
        Flattened list of anime ranking dictionaries.
    """
    all_rows = []

    for response in responses:
        for anime_dict in response["data"]["data"]:
            anime_dict["ingested_at"] = response["ingested_at"]
            all_rows.append(anime_dict)

    return all_rows


def create_decoded_dataframe(all_rows: list[dict]) -> pl.DataFrame:
    """
    Converts nested anime records into a flattened Polars DataFrame.

    Assumes each record contains node, ranking, and main_picture
    nested dictionaries from the MyAnimeList API payload.

    Args:
        all_rows: List of individual anime ranking records.

    Returns:
        Flattened DataFrame containing anime and ranking fields.
    """
    parsed_df = pl.from_dicts(all_rows)
    parsed_df = parsed_df.unnest("node").unnest("ranking").unnest("main_picture")
    return parsed_df


def create_anime_dim_dataframe(parsed_df: pl.DataFrame) -> pl.DataFrame:
    """
    Creates the anime dimension table from parsed ranking data.

    Extracts anime identifiers and titles.

    Args:
        parsed_df: Flattened anime ranking DataFrame.

    Returns:
        DataFrame containing anime dimension records.
    """
    anime_dim_df = parsed_df.select("id", "title")
    return anime_dim_df


def create_fact_dataframe(parsed_df: pl.DataFrame) -> pl.DataFrame:
    """
    Creates the anime ranking fact table from parsed ranking data.

    Extracts anime identifiers and ranking measurements.

    Args:
        parsed_df: Flattened anime ranking DataFrame.

    Returns:
        DataFrame containing anime ranking records.
    """
    fact_df = parsed_df.select("id", "rank", "ingested_at")
    return fact_df


def silver_transform(
    db_manager: DatabaseManager,
    bronze_table: str,
) -> None:
    """
    Transforms Bronze API responses into Silver dimension and fact tables.

    Reads Bronze JSON payloads, flattens anime ranking records, and writes
    dim_anime and fact_rankings tables.

    Args:
        db_manager: a DatabaseManager instance
        bronze_table: Bronze table containing raw API responses.
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
