import duckdb

# Connect to DuckDB database
duckdb_conn = duckdb.connect("quotes_data.duckdb")

# 🔹 STEP 1: Ensure tables exist
duckdb_conn.execute("""
    CREATE TABLE IF NOT EXISTS quotes (
        security_id TEXT, 
        timestamp TIMESTAMP, 
        condition_code TEXT, 
        bid_price FLOAT, 
        ask_price FLOAT
    )
""")

duckdb_conn.execute("""
    CREATE TABLE IF NOT EXISTS orders (
        security_id TEXT, 
        mic_exchange TEXT, 
        fulfill_time TIMESTAMP
    )
""")

duckdb_conn.execute("""
    CREATE TABLE IF NOT EXISTS condition_filter (
        mic_exchange TEXT, 
        condition_code_to_drop TEXT
    )
""")

# 🔹 STEP 2: Filter Quotes & Compute Mid Price
query = """
WITH filtered_quotes AS (
    SELECT q.security_id, q.timestamp, q.bid_price, q.ask_price, q.condition_code
    FROM quotes q
    LEFT JOIN orders o ON q.security_id = o.security_id
    LEFT JOIN condition_filter cf 
        ON o.mic_exchange = cf.mic_exchange 
        AND q.condition_code = cf.condition_code_to_drop
    WHERE cf.condition_code_to_drop IS NULL  -- 🔥 Remove unwanted condition codes
),
closest_quotes AS (
    SELECT 
        f.security_id, 
        f.timestamp, 
        f.bid_price, 
        f.ask_price, 
        (f.bid_price + f.ask_price) / 2 AS mid_price,  -- ✅ Mid Price Calculation
        o.fulfill_time,
        ABS(strftime('%s', f.timestamp) - strftime('%s', o.fulfill_time)) AS time_diff
    FROM filtered_quotes f
    JOIN orders o 
        ON f.security_id = o.security_id
    WHERE f.timestamp <= o.fulfill_time -- 🔥 Only quotes BEFORE fulfill time
    AND time_diff <= 3  -- ✅ Closest quote within 3 sec
),
ranked_quotes AS (
    SELECT *, RANK() OVER (
        PARTITION BY security_id, fulfill_time ORDER BY time_diff ASC
    ) AS rank
    FROM closest_quotes
)
SELECT security_id, fulfill_time, mid_price
FROM ranked_quotes
WHERE rank = 1;  -- ✅ Select closest quote
"""

# Run Query
df = duckdb_conn.execute(query).fetchdf()
print(df)

# Close connection
duckdb_conn.close()

    def load_data(self, quotes_df, orders_df, condition_filter_df):
        """Load data into DuckDB tables"""
        self.conn.register("quotes_df", quotes_df)
        self.conn.register("orders_df", orders_df)
        self.conn.register("condition_filter_df", condition_filter_df)

        self.conn.execute("INSERT INTO quotes SELECT * FROM quotes_df")
        self.conn.execute("INSERT INTO orders SELECT * FROM orders_df")
        self.conn.execute("INSERT INTO condition_filter SELECT * FROM condition_filter_df")

    def compute_metrics(self):
        """Compute shortfall metrics and returns"""
        query = """
        WITH filtered_quotes AS (
            SELECT q.security_id, q.timestamp, q.trade_price, q.condition_code, q.volume,
                   (q.bid_price + q.ask_price) / 2 AS mid_price
            FROM quotes q
            LEFT JOIN orders o ON q.security_id = o.security_id
            LEFT JOIN condition_filter cf 
                ON o.mic_exchange = cf.mic_exchange 
                AND q.condition_code = cf.condition_code_to_drop
            WHERE cf.condition_code_to_drop IS NULL
        ),
        closest_quotes AS (
            SELECT f.security_id, f.timestamp, f.mid_price, f.trade_price, o.fulfill_time,
                   ABS(strftime('%s', f.timestamp) - strftime('%s', o.fulfill_time)) AS time_diff
            FROM filtered_quotes f
            JOIN orders o ON f.security_id = o.security_id
            WHERE f.timestamp <= o.fulfill_time AND time_diff <= 3
        ),
        ranked_quotes AS (
            SELECT *, RANK() OVER (
                PARTITION BY security_id, fulfill_time ORDER BY time_diff ASC
            ) AS rank
            FROM closest_quotes
        ),
        execution_prices AS (
            SELECT o.security_id, o.execution_price, o.order_start_time, o.order_end_time, o.fulfill_time,
                   q.mid_price AS pre_trade_price
            FROM ranked_quotes q
            JOIN orders o ON q.security_id = o.security_id
            WHERE q.rank = 1
        ),
        post_trade_returns AS (
            SELECT e.security_id, e.execution_price, e.order_end_time, 
                   q.timestamp, q.mid_price AS post_trade_price,
                   (q.mid_price - e.execution_price) / e.execution_price * 100 AS return_bps,
                   ABS(strftime('%s', q.timestamp) - strftime('%s', e.order_end_time)) AS time_diff
            FROM execution_prices e
            JOIN quotes q ON e.security_id = q.security_id
            WHERE q.timestamp >= e.order_end_time
            ORDER BY e.security_id, time_diff
        ),
        vwap_calc AS (
            SELECT security_id, 
                   SUM(trade_price * volume) / SUM(volume) AS vwap_price
            FROM quotes
            WHERE timestamp BETWEEN (SELECT MIN(order_start_time) FROM orders)
                              AND (SELECT MAX(order_end_time) FROM orders)
            GROUP BY security_id
        ),
        final_metrics AS (
            SELECT e.security_id,
                   e.execution_price,
                   e.pre_trade_price,
                   v.vwap_price,
                   p.post_trade_price AS end_price,
                   (e.execution_price - e.pre_trade_price) / e.pre_trade_price * 100 AS arrival_shortfall_bps,
                   (e.execution_price - v.vwap_price) / v.vwap_price * 100 AS vwap_shortfall_bps,
                   (e.execution_price - p.post_trade_price) / p.post_trade_price * 100 AS settlement_shortfall_bps,
                   p.return_bps AS return_after_execution_bps
            FROM execution_prices e
            JOIN vwap_calc v ON e.security_id = v.security_id
            JOIN post_trade_returns p ON e.security_id = p.security_id
            WHERE p.time_diff = 10  -- 10 seconds after order execution
        )
        SELECT * FROM final_metrics;
        """

        return self.conn.execute(query).fetchdf()
    
    
    
# setup table

## 🏗 **3️⃣ DuckDB Database Setup (src/db.py)**
```python
import duckdb

def connect_db(db_path="tca_data.duckdb"):
    """Establish DuckDB connection."""
    return duckdb.connect(db_path)

def setup_tables(conn):
    """Create necessary tables in DuckDB."""
    conn.execute("""
        CREATE TABLE IF NOT EXISTS quotes (
            security_id TEXT, 
            timestamp TIMESTAMP, 
            condition_code TEXT, 
            bid_price FLOAT, 
            ask_price FLOAT, 
            trade_price FLOAT,
            volume FLOAT
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            security_id TEXT, 
            mic_exchange TEXT, 
            fulfill_time TIMESTAMP, 
            order_start_time TIMESTAMP,
            order_end_time TIMESTAMP,
            order_size FLOAT, 
            execution_price FLOAT
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS condition_filter (
            mic_exchange TEXT, 
            condition_code_to_drop TEXT
        )
    """)
    
import pandas as pd

def load_data(conn, quotes_df, orders_df, condition_filter_df):
    """Load data into DuckDB tables."""
    conn.register("quotes_df", quotes_df)
    conn.register("orders_df", orders_df)
    conn.register("condition_filter_df", condition_filter_df)

    conn.execute("INSERT INTO quotes SELECT * FROM quotes_df")
    conn.execute("INSERT INTO orders SELECT * FROM orders_df")
    conn.execute("INSERT INTO condition_filter SELECT * FROM condition_filter_df") 
    
def filter_quotes(conn):
    """Filter out quotes based on invalid condition codes."""
    query = """
        SELECT q.security_id, q.timestamp, q.trade_price, q.condition_code, q.volume,
               (q.bid_price + q.ask_price) / 2 AS mid_price
        FROM quotes q
        LEFT JOIN orders o ON q.security_id = o.security_id
        LEFT JOIN condition_filter cf 
            ON o.mic_exchange = cf.mic_exchange 
            AND q.condition_code = cf.condition_code_to_drop
        WHERE cf.condition_code_to_drop IS NULL
    """
    return conn.execute(query).fetchdf()

def compute_shortfall_metrics(conn):
    """Compute shortfall metrics such as arrival, VWAP, and settlement shortfall."""
    query = """
        WITH execution_prices AS (
            SELECT o.security_id, o.execution_price, o.order_start_time, o.order_end_time, o.fulfill_time,
                   (SELECT mid_price FROM quotes 
                    WHERE security_id = o.security_id 
                    AND timestamp <= o.fulfill_time 
                    ORDER BY timestamp DESC LIMIT 1) AS pre_trade_price
            FROM orders o
        ),
        vwap_calc AS (
            SELECT security_id, 
                   SUM(trade_price * volume) / SUM(volume) AS vwap_price
            FROM quotes
            WHERE timestamp BETWEEN (SELECT MIN(order_start_time) FROM orders)
                              AND (SELECT MAX(order_end_time) FROM orders)
            GROUP BY security_id
        )
        SELECT e.security_id,
               e.execution_price,
               e.pre_trade_price,
               v.vwap_price,
               (e.execution_price - e.pre_trade_price) / e.pre_trade_price * 100 AS arrival_shortfall_bps,
               (e.execution_price - v.vwap_price) / v.vwap_price * 100 AS vwap_shortfall_bps
        FROM execution_prices e
        JOIN vwap_calc v ON e.security_id = v.security_id;
    """
    return conn.execute(query).fetchdf()   