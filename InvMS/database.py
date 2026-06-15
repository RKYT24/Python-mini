import sqlite3
from datetime import datetime

class Database:
    
    def __init__(self, db_name="inventory.db"):
        self.conn = sqlite3.connect(
            db_name,
            check_same_thread=False
        )

        self.conn.execute("PRAGMA journal_mode=WAL")        # WAL mode = much faster concurrent reads/writes
        self.conn.execute("PRAGMA synchronous=NORMAL")        # Relaxed sync — safe for local inventory use
        self.conn.execute("PRAGMA cache_size=-65536")        # Larger cache = fewer disk reads (64 MB)
        self.conn.execute("PRAGMA temp_store=MEMORY")        # Store temp tables in memory
        self.cursor = self.conn.cursor()

    # CREATE TABLE

    def create_table(self, table_name, columns):
        cleaned_columns = []

        for col in columns:

            col = col.strip().replace(" ", "_")

            cleaned_columns.append(f'"{col}" TEXT')

        query = f'''
        CREATE TABLE IF NOT EXISTS "{table_name}" (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            {",".join(cleaned_columns)},
            last_modified TEXT
        )
        '''

        self.cursor.execute(query)
        self.conn.commit()

    # INSERT ROW  (single row)
    def insert_row(self, table_name, data):
        columns = []
        values  = []

        for key, value in data.items():
            columns.append(f'"{key.replace(" ", "_")}"')
            values.append(value)

        columns.append("last_modified")
        values.append(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

        placeholders = ",".join(["?"] * len(values))

        query = f'''
        INSERT INTO "{table_name}"
        ({",".join(columns)})
        VALUES ({placeholders})
        '''

        self.cursor.execute(query, values)
        self.conn.commit()

    # INSERT MANY ROWS  ← NEW (bulk import)
    # rows - list of dicts, all with identical keys. Wraps the entire batch in ONE transaction and uses executemany(), which is 10-50x faster than looping insert_row() one at a time.
    def insert_many_rows(self, table_name, rows):

        if not rows:
            return

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Build column list from first row
        sample_keys = list(rows[0].keys())

        columns = [f'"{k.replace(" ", "_")}"' for k in sample_keys]
        columns.append("last_modified")

        placeholders = ",".join(["?"] * len(columns))

        query = f'''
        INSERT INTO "{table_name}"
        ({",".join(columns)})
        VALUES ({placeholders})
        '''

        # Convert each dict to a flat tuple (values + timestamp)
        data = [
            tuple(row[k] for k in sample_keys) + (timestamp,)
            for row in rows
        ]

        with self.conn:          # single atomic transaction
            self.cursor.executemany(query, data)

    # FETCH ALL
    def fetch_all(self, table_name):
        self.cursor.execute(
            f'SELECT * FROM "{table_name}" ORDER BY id'
        )

        return self.cursor.fetchall()

    # FETCH PAGE  ← NEW (virtual scrolling)
    def fetch_page(self, table_name, offset=0, limit=500):
        # Return one page of rows for lazy UI loading.

        self.cursor.execute(
            f'SELECT * FROM "{table_name}" ORDER BY id LIMIT ? OFFSET ?',
            (limit, offset)
        )

        return self.cursor.fetchall()

    # COUNT ROWS  ← NEW
    def count_rows(self, table_name):
        self.cursor.execute(
            f'SELECT COUNT(*) FROM "{table_name}"'
        )
        return self.cursor.fetchone()[0]

    # GET COLUMNS
    def get_columns(self, table_name):
        self.cursor.execute(
            f'PRAGMA table_info("{table_name}")'
        )

        return [row[1] for row in self.cursor.fetchall()]

    # UPDATE ROW
    def update_row(self, table_name, record_id, updated_data):
        updates = []
        values  = []

        for key, value in updated_data.items():
            updates.append(f'"{key.replace(" ", "_")}"=?')
            values.append(value)

        updates.append("last_modified=?")
        values.append(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        values.append(record_id)

        query = f'''
        UPDATE "{table_name}"
        SET {",".join(updates)}
        WHERE id=?
        '''

        self.cursor.execute(query, values)
        self.conn.commit()

    # DELETE ROW
    def delete_row(self, table_name, record_id):
        self.cursor.execute(
            f'DELETE FROM "{table_name}" WHERE id=?',
            (record_id,)
        )

        self.conn.commit()

    # SEARCH
    def search(self, table_name, search_text):
        columns = self.get_columns(table_name)
        searchable = [
            col for col in columns
            if col not in ("id", "last_modified")
        ]

        if not searchable:
            return []

        conditions = [f'"{col}" LIKE ?' for col in searchable]
        values     = [f"%{search_text}%"] * len(searchable)

        query = f'''
        SELECT * FROM "{table_name}"
        WHERE {" OR ".join(conditions)}
        ORDER BY id
        '''

        self.cursor.execute(query, values)
        return self.cursor.fetchall()

    # GET TABLES
    def get_tables(self):
        self.cursor.execute(
            """
            SELECT name FROM sqlite_master
            WHERE type='table'
            AND name NOT LIKE 'sqlite_%'
            """
        )
        return [row[0] for row in self.cursor.fetchall()]

    # DROP TABLE
    def drop_table(self, table_name):
        self.cursor.execute(
            f'DROP TABLE IF EXISTS "{table_name}"'
        )

        self.conn.commit()

    # ENSURE INDEX  ← NEW
    def ensure_index(self, table_name, column):
        # Create an index on a column if it doesn't exist yet.
        index_name = f"idx_{table_name}_{column}"
        self.cursor.execute(
            f'CREATE INDEX IF NOT EXISTS "{index_name}" '
            f'ON "{table_name}" ("{column}")'
        )

        self.conn.commit()

    # CLOSE CONNECTION
    def close(self):
        self.conn.close()