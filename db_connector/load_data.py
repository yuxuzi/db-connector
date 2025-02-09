import asyncio
import snowflake.connector
import duckdb
from snowflake.connector.errors import ProgrammingError

# Snowflake connection details
SNOWFLAKE_CONFIG = {
    "user": "your_user",
    "password": "your_password",
    "account": "your_account",
    "warehouse": "your_warehouse",
    "database": "your_database",
    "schema": "your_schema"
}

# Connect to DuckDB (Persistent DB)
DUCKDB_PATH = "quotes_data.duckdb"
duckdb_conn = duckdb.connect(DUCKDB_PATH)

# Asynchronous function to fetch data from Snowflake
async def fetch_and_store_quotes(query, table_name):
    """Fetches data from Snowflake and saves to DuckDB"""
    try:
        conn = snowflake.connector.connect(**SNOWFLAKE_CONFIG)
        cur = conn.cursor()
        
        # Run query asynchronously
        cur.execute_async(query)
        query_id = cur.sfqid  # Query ID

        # Wait for query completion
        while True:
            status = conn.get_query_status(query_id)
            if status == snowflake.connector.QueryStatus.COMPLETE:
                break
            elif status == snowflake.connector.QueryStatus.FAILED:
                raise RuntimeError(f"Query Failed: {query_id}")
            await asyncio.sleep(0.5)  # Non-blocking wait

        # Fetch results
        cur.execute(f"SELECT * FROM TABLE(RESULT_SCAN('{query_id}'))")
        df = cur.fetch_pandas_all()
        
        # Store in DuckDB
        if not df.empty:
            duckdb_conn.execute(f"CREATE TABLE IF NOT EXISTS {table_name} AS SELECT * FROM df")
            duckdb_conn.execute(f"INSERT INTO {table_name} SELECT * FROM df")
        
        cur.close()
        conn.close()
        return len(df)  # Return row count

    except ProgrammingError as e:
        print(f"Error: {e}")
        return 0

# Run multiple queries concurrently
async def main():
    securities = ["AAPL", "TSLA", "GOOGL"]
    queries = {
        sec: f"SELECT * FROM quotes WHERE security_id = '{sec}' AND timestamp >= CURRENT_TIMESTAMP - INTERVAL '30 seconds'"
        for sec in securities
    }

    # Run all queries asynchronously
    results = await asyncio.gather(*(fetch_and_store_quotes(q, sec) for sec, q in queries.items()))

    # Print summary
    print(f"✅ Data saved in DuckDB. Rows inserted per security: {dict(zip(securities, results))}")

# Execute async queries
asyncio.run(main())

# Close DuckDB connection
duckdb_conn.close()

import duckdb

duckdb_conn = duckdb.connect("quotes_data.duckdb")

# Query the latest quotes in DuckDB
df = duckdb_conn.execute("SELECT * FROM AAPL ORDER BY timestamp DESC LIMIT 10").fetchdf()
print(df)

duckdb_conn.close()