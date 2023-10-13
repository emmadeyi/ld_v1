import sqlite3
import time

SQLITE_DB_FILE = "device_data.db"  # Same SQLite database file used in the main script

def query_device_data():
    while True:
        connection = sqlite3.connect(SQLITE_DB_FILE)
        cursor = connection.cursor()

        select_query = "SELECT * FROM device_data;"
        cursor.execute(select_query)
        data = cursor.fetchall()

        cursor.close()
        connection.close()

        print("\nQuery Result:")
        for row in data:
            print(row)

        time.sleep(60)  # Sleep for 60 seconds before querying again

if __name__ == "__main__":
    query_device_data()