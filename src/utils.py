from fnmatch import fnmatchcase
import os,logging, sqlite3
from tabulate import tabulate
from scripts import ogr2ogr

def patterns_match(path, patterns):
    return any(fnmatchcase(path, p) for p in patterns)

def gpkg_dump(destination_gpkg, source_gpkg):
    logger = logging.getLogger(__name__)

    destination_gpkg = os.path.join(os.getcwd(), destination_gpkg)
    source_gpkg = os.path.join(os.getcwd(), source_gpkg)

    result = ogr2ogr.main(['ogr2ogr', '-f', 'GPKG', '-append', destination_gpkg, source_gpkg])
    
    logger.info(f"Merging {source_gpkg} to {destination_gpkg}...")

    if result:
        logger.debug(f"Successfully merged {source_gpkg} to {destination_gpkg}!")
    else:
        logger.error("Error executing ogr2ogr command:")

    # result True -> exit(0) | False -> exit(1)
    return not result

def execute_sql(sql_statement, db_path):
    logger = logging.getLogger(__name__)
    db_connection = None

    try:
        # Connect to the SQLite database in read-only mode
        db_connection = sqlite3.connect(f'file:{db_path}?mode=rw', uri=True, isolation_level=None)
        db_connection.row_factory = sqlite3.Row  # Use the Row factory for dictionary-like access
        db_cursor = db_connection.cursor()

        # Execute the SQL statement
        db_cursor.execute(sql_statement)

        # Fetch the result if it's a SELECT statement
        if sql_statement.strip().upper().startswith("SELECT"):
            result = db_cursor.fetchall()
            if result:
                headers = result[0].keys() if isinstance(result[0], sqlite3.Row) else None
                print(tabulate(result, headers=headers, tablefmt="fancy_grid"))
            else:
                db_connection.commit()
                print("No results found.")
        else:
            print("SQL statement executed successfully")
        return 0
    except sqlite3.OperationalError as e:
       logger.error(e)
       return 1

    except Exception as e:
        logger.error(f"Error executing SQL statement: {e}")
        return 1
    finally:
        if db_connection:
            db_connection.close()