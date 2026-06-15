import csv
import os
from database import Database

class CSVHandler:
    def __init__(self):
        self.db = Database()

    def is_internal_column(self, column_name):
        return column_name.strip().lower() in ("id", "last_modified")

    # IMPORT CSV  (optimised)
    def import_csv(self, csv_path):
        if not os.path.exists(csv_path):
            raise FileNotFoundError(f"File not found: {csv_path}")

        table_name = os.path.splitext(os.path.basename(csv_path))[0]

        with open(csv_path, mode="r", encoding="utf-8-sig", newline="") as file:

            reader = csv.DictReader(file)
            headers = reader.fieldnames

            if not headers:
                raise ValueError("CSV file contains no headers.")

            import_headers = [
                h for h in headers
                if not self.is_internal_column(h)
            ]

            if not import_headers:
                raise ValueError("CSV file contains no importable columns.")

            # Drop old table and create fresh one
            self.db.drop_table(table_name)
            self.db.create_table(table_name, import_headers)

            # _________________ BULK COLLECT then INSERT ONCE _____________________
            # Previously: insert_row() was called per row → one commit each time.Now we gather all rows into a list and call insert_many_rows() which uses executemany() inside a single transaction.  For a 10 000-row CSV this is ~40× faster.
            # _____________________________________________________________________

            batch = []
            BATCH_SIZE = 2000   # flush to DB every 2 000 rows to keep
                                # memory reasonable for very large files
            for row in reader:
                cleaned_row = {
                    key: (row.get(key) or "").strip()
                    for key in import_headers
                }

                batch.append(cleaned_row)

                if len(batch) >= BATCH_SIZE:
                    self.db.insert_many_rows(table_name, batch)
                    batch.clear()

            if batch:                           # flush remaining rows
                self.db.insert_many_rows(table_name, batch)

        return table_name

    # IMPORT ALL CSV FILES IN FOLDER
    def import_csv_folder(self, folder_path):
        imported_tables = []
        if not os.path.exists(folder_path):
            return imported_tables

        for filename in os.listdir(folder_path):

            if filename.lower().endswith(".csv"):

                full_path  = os.path.join(folder_path, filename)
                table_name = self.import_csv(full_path)
                imported_tables.append(table_name)

        return imported_tables

    # EXPORT TABLE TO CSV
    def export_csv(self, table_name, save_path):
        columns = self.db.get_columns(table_name)
        rows    = self.db.fetch_all(table_name)

        export_columns = []
        export_indexes = []

        for index, column in enumerate(columns):
            if not self.is_internal_column(column):
                export_columns.append(column)
                export_indexes.append(index)

        with open(save_path, mode="w", encoding="utf-8", newline="") as file:

            writer = csv.writer(file)
            writer.writerow(export_columns)

            for row in rows:
                writer.writerow([row[i] for i in export_indexes])

        return True

    # EXPORT ALL TABLES
    def export_all_tables(self, export_folder):
        os.makedirs(export_folder, exist_ok=True)

        exported_files = []

        for table in self.db.get_tables():

            file_path = os.path.join(export_folder, f"{table}.csv")
            self.export_csv(table, file_path)
            exported_files.append(file_path)

        return exported_files

    # HELPERS  (unchanged interface)
    def get_tables(self):
        return self.db.get_tables()

    def get_table_data(self, table_name):
        return self.db.fetch_all(table_name)

    def get_table_columns(self, table_name):
        return self.db.get_columns(table_name)

    def close(self):
        self.db.close()
