import duckdb

class DatabaseManager:
    """
    This class creates a database manager in order to abstract away repetitive database operations
    such as managing the connection, checking whether a table exists in DuckDB, appending to a table, etc. 
    """
    def __init__(self, db_path):
        self.conn = duckdb.connect(db_path)

    def close_conn(self):
        self.conn.close()

    def table_exists(self, table_name):
        query = """
            SELECT EXISTS (
                SELECT 1
                FROM duckdb_tables()
                WHERE table_name = $table_name
            );
        """
        exists = self.conn.execute(query, {"table_name": table_name}).fetchone()
        return True if exists[0] else False

    def create_table(self, table_name, df):
        query = f"CREATE TABLE IF NOT EXISTS {table_name} AS SELECT * FROM df"
        return self.conn.execute(query)

    def append(self, table_name, df):
        query = f"INSERT INTO {table_name} SELECT * FROM df"
        return self.conn.execute(query)

    def write(self, table_name, df):
        if self.table_exists(table_name):
            return self.append(table_name, df)
        else:
            return self.create_table(table_name, df)
    
    def execute(self, query):
        return self.conn.execute(query)
