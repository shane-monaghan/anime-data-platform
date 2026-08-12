import duckdb


class DatabaseManager:
    """Abstraction layer for DuckDB operations.

    Provides convenience methods for managing a DuckDB connection, checking
    whether tables exist, creating tables from DataFrames, appending records,
    and executing arbitrary SQL.
    """

    def __init__(self, db_path):
        """Initialize the database manager with a DuckDB file path.

        Args:
            db_path: Path to the DuckDB database file.
        """
        self.conn = duckdb.connect(db_path)

    def close_conn(self):
        """Close the active DuckDB connection."""
        self.conn.close()

    def table_exists(self, table_name):
        """Return whether a DuckDB table exists.

        Args:
            table_name: Name of the table to check.

        Returns:
            True if the table exists, False otherwise.
        """
        query = """
            SELECT EXISTS (
                SELECT 1
                FROM duckdb_tables()
                WHERE table_name = $table_name
            );
        """
        exists = self.conn.execute(query, {"table_name": table_name}).fetchone()

        if exists is None:
            raise ValueError("Something went wrong with the query.")

        return True if exists[0] else False

    def create_table(self, table_name, df):
        """Create a new DuckDB table from a Polars DataFrame.

        Args:
            table_name: Name of the table to create.
            df: DataFrame whose schema and contents will define the table.

        Returns:
            Result of the DuckDB execute call.
        """
        query = f"CREATE TABLE IF NOT EXISTS {table_name} AS SELECT * FROM df"
        return self.conn.execute(query)

    def append(self, table_name, df, conflict_columns=None):
        """Append rows from a DataFrame into an existing DuckDB table.

        Args:
            table_name: Name of the target table.
            df: DataFrame containing rows to append.
            conflict_columns: Optional sequence of columns to use for conflict
                resolution when inserting rows.

        Returns:
            Result of the DuckDB execute call.
        """
        query = f"INSERT INTO {table_name} SELECT * FROM df"

        if conflict_columns:
            columns = ", ".join(conflict_columns)
            query += f" ON CONFLICT ({columns}) DO NOTHING"

        return self.conn.execute(query)

    def write(self, table_name, df, conflict_columns=None):
        """Create or append a DataFrame to a DuckDB table.

        Args:
            table_name: Name of the target table.
            df: DataFrame to write.
            conflict_columns: Optional conflict resolution columns for append.

        Returns:
            Result of either creating or appending to the table.
        """
        if self.table_exists(table_name):
            return self.append(table_name, df, conflict_columns=conflict_columns)
        else:
            return self.create_table(table_name, df)

    def execute(self, query):
        """Execute an arbitrary SQL query against the DuckDB connection.

        Args:
            query: SQL query string to execute.

        Returns:
            Result of the DuckDB execute call.
        """
        return self.conn.execute(query)
