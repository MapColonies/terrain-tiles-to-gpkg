import sqlite3

MAX_BATCH_SIZE = 20000

class HistoryDatabase:
    def __init__(self, db_file_path: str):
        self.db_file_path = db_file_path
        self.conn = None
        self.cursor = None
        self.updates_batch = []
        self.init_history_db()

    def init_history_db(self):
        self.conn = sqlite3.connect(self.db_file_path)
        self.cursor = self.conn.cursor()

        create_history_table_query = """
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY,
            directory TEXT NOT NULL,
            tiles_count INTEGER NOT NULL
        );
        """
        self.cursor.execute(create_history_table_query)
        self.cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_directory ON history (directory);"
        )
        self.conn.commit()

    def update_history(self, directory):
        self.updates_batch.append(directory)

        if len(self.updates_batch) >= MAX_BATCH_SIZE:
            self.insert_or_update_history_entry_batch(self.updates_batch)
            self.updates_batch = []

    def insert_or_update_history_entry_batch(self, entries):
        try:
            self.conn.execute("BEGIN TRANSACTION;")
            for directory in entries:
                # Check if the record already exists
                existing_record = self.cursor.execute("SELECT * FROM history WHERE directory = ?", (directory,)).fetchone()
                
                if existing_record:
                    self.cursor.execute("UPDATE history SET tiles_count = tiles_count + 1 WHERE directory = ?", (directory,))
                else:
                    self.cursor.execute("INSERT INTO history (directory, tiles_count) VALUES (?, 1)", (directory,))
            
            self.conn.execute("COMMIT;")
        except Exception as e:
            self.conn.execute("ROLLBACK;")
            print(f"Error inserting or updating history entries: {e}")
            import traceback
            traceback.print_exc()

    def has_directory(self, directory):
      try:
          result = self.cursor.execute("SELECT 1 FROM history WHERE directory = ? LIMIT 1", (directory,)).fetchone()
          
          return result is not None

      except Exception as e:
          print(f"Error checking if directory exists: {e}")
          import traceback
          traceback.print_exc()
          return False

    def close_connection(self):
        if self.conn:
            if self.updates_batch:
                self.insert_or_update_history_entry_batch(self.updates_batch)
            self.conn.close()
            print("Closed SQLite database connection.")
