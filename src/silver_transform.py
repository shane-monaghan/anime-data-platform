import duckdb
import polars as pl


def read_bronze_data(database_path: str, bronze_table: str) -> list[dict]:
    """
    Reads and decodes raw JSON responses from a Bronze DuckDB table.

    Assumes the table contains a raw_json column containing serialized
    MyAnimeList API response payloads.

    Args:
        database_path: Path to the DuckDB database.
        bronze_table: Name of the Bronze table to read.

    Returns:
        List of decoded API response dictionaries.
    """
    con = duckdb.connect(database_path)
    bronze_df = con.sql(f"SELECT * FROM {bronze_table}").pl()
    dict_data = bronze_df["raw_json"].str.json_decode().to_list()
    con.close()
    return dict_data


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
        for anime_dict in response["data"]:
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
    fact_df = parsed_df.select("id", "rank")
    return fact_df


def silver_transform(
    database_path: str,
    connection: str,
    bronze_table: str,
) -> None:
    """
    Transforms Bronze API responses into Silver dimension and fact tables.

    Reads Bronze JSON payloads, flattens anime ranking records, and writes
    dim_anime and fact_rankings tables.

    Args:
        database_path: Path to the DuckDB database.
        connection: Database connection string for writing tables.
        bronze_table: Bronze table containing raw API responses.
    """
    dict_data = read_bronze_data(database_path=database_path, bronze_table=bronze_table)
    all_rows = extract_anime_records(dict_data)
    parsed_df = create_decoded_dataframe(all_rows)

    anime_dim_df = create_anime_dim_dataframe(parsed_df)
    fact_df = create_fact_dataframe(parsed_df)

    anime_dim_df.write_database(
        table_name="dim_anime", connection=connection, if_table_exists="append"
    )

    fact_df.write_database(
        table_name="fact_rankings", connection=connection, if_table_exists="append"
    )
