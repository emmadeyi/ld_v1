import requests
import json
import time
import sqlite3
import csv
import getpass

class DeviceManager:
    def __init__(self, api_endpoint, authorization_token, sqlite_db_file, device_info_file, passcode_file):
        self.api_endpoint = api_endpoint
        self.authorization_token = authorization_token
        self.sqlite_db_file = sqlite_db_file
        self.device_info_file = device_info_file
        self.passcode_file = passcode_file

    def create_tables(self):
        # Create SQLite tables for storing device data and registration data
        connection = sqlite3.connect(self.sqlite_db_file)
        cursor = connection.cursor()

        create_device_table_query = '''
        CREATE TABLE IF NOT EXISTS device_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            device_id TEXT,
            online TEXT,
            power TEXT,
            voltage TEXT,
            current TEXT,
            name TEXT
        );
        '''
        cursor.execute(create_device_table_query)

        # Change tariff to float or decimal
        create_registration_table_query = '''
        CREATE TABLE IF NOT EXISTS registration_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_id TEXT,
            passcode TEXT,
            tariff INTEGER, 
            token TEXT,
            api TEXT,
            is_active BOOLEAN,
            bearer_token TEXT,
            tariff_value REAL,
        );
        '''
        cursor.execute(create_registration_table_query)

        connection.commit()
        cursor.close()
        connection.close()
    
    def alter_registration_table(self):
        # Create SQLite tables for storing device data and registration data
        connection = sqlite3.connect(self.sqlite_db_file)
        cursor = connection.cursor()

        # Example: Add a new column 'new_column' to the 'your_table' table

        add_column_query1 = """
            ALTER TABLE registration_data
            ADD COLUMN tariff_value REAL;
        """

        # Execute each ALTER TABLE query
        cursor.execute(add_column_query1)


        # Commit the changes to the database
        connection.commit()

        # Close the cursor and connection
        cursor.close()
        connection.close()

    def insert_device_data(self, device_data):
        # Insert data into the SQLite device_data table
        connection = sqlite3.connect(self.sqlite_db_file)
        cursor = connection.cursor()

        insert_query = '''
        INSERT INTO device_data (timestamp, device_id, online, power, voltage, current, name)
        VALUES (?, ?, ?, ?, ?, ?, ?);
        '''
        data_tuple = (
            device_data['Timestamp'],
            device_data['Device ID'],
            device_data['Online'],
            device_data['Power'],
            device_data['Voltage'],
            device_data['Current'],
            device_data['Name']
        )
        cursor.execute(insert_query, data_tuple)

        connection.commit()
        cursor.close()
        connection.close()

    def insert_registration_data(self, device_id, device_pass, device_tariff, device_api, device_token):
        try:
            # Insert registration data into the SQLite registration_data table
            connection = sqlite3.connect(self.sqlite_db_file)
            cursor = connection.cursor()

            insert_query = '''
            INSERT INTO registration_data (device_id, passcode, tariff, api, token)
            VALUES (?, ?, ?, ?, ?);
            '''
            data_tuple = (device_id, device_pass, device_tariff, device_api, device_token)
            result = cursor.execute(insert_query, data_tuple)
            connection.commit()
            return result
        except sqlite3.Error as e:
            print(f"SQLite Error: {e}")
        finally:
            cursor.close()
            connection.close()

    async def update_device_tariff(self, device_id, tariff):
        try:
            # Insert registration data into the SQLite registration_data table
            connection = sqlite3.connect(self.sqlite_db_file)
            cursor = connection.cursor()

            update_query = """
                UPDATE registration_data
                SET tariff = ?
                WHERE device_id = ?;
            """

            cursor.execute(update_query, (tariff, device_id))
            connection.commit()
            result = self.get_device_data(device_id)
            return result
        except sqlite3.Error as e:
            print(f"SQLite Error: {e}")
        finally:
            cursor.close()
            connection.close()

    async def update_device_api(self, device_id, api=None, token=None):
        try:
            # Insert registration data into the SQLite registration_data table
            connection = sqlite3.connect(self.sqlite_db_file)
            cursor = connection.cursor()

            update_query = """
                UPDATE registration_data
                SET api = ?, token = ?
                WHERE device_id = ?;
            """

            cursor.execute(update_query, (api, token, device_id))
            connection.commit()
            result = self.get_device_data(device_id)
            return result
        except sqlite3.Error as e:
            print(f"SQLite Error: {e}")
        finally:
            cursor.close()
            connection.close()

    async def update_device_passcode(self, device_id, passcode):
        try:
            # Insert registration data into the SQLite registration_data table
            connection = sqlite3.connect(self.sqlite_db_file)
            cursor = connection.cursor()

            update_query = """
                UPDATE registration_data
                SET passcode = ?
                WHERE device_id = ?;
            """

            cursor.execute(update_query, (passcode, device_id))
            connection.commit()
            result = self.get_device_data(device_id)
            
            return result
        except sqlite3.Error as e:
            print(f"SQLite Error: {e}")
        finally:
            cursor.close()
            connection.close()

    async def get_device_bearer_token(self, device_id, bearer_token=None):
        try:
            # Insert registration data into the SQLite registration_data table
            connection = sqlite3.connect(self.sqlite_db_file)
            cursor = connection.cursor()
            if device_id is not None and bearer_token is not None:
                query = "SELECT * FROM registration_data WHERE device_id = ? AND bearer_token = ?;"
                cursor.execute(query, (device_id, bearer_token,))
            elif device_id is not None:
                query = "SELECT bearer_token FROM registration_data WHERE device_id = ?;"
                cursor.execute(query, (device_id,))
                result = cursor.fetchone()                        
                return result
            else:
                return None
        except sqlite3.Error as e:
            print(f"SQLite Error: {e}")
        finally:
            cursor.close()
            connection.close()

    async def get_device_with_token(self, bearer_token):
        try:
            # Insert registration data into the SQLite registration_data table
            connection = sqlite3.connect(self.sqlite_db_file)
            cursor = connection.cursor()
            if bearer_token is not None:
                query = "SELECT * FROM registration_data WHERE bearer_token = ?;"
                cursor.execute(query, (bearer_token,))
                result = cursor.fetchone()                        
                return result
            else:
                return None
        except sqlite3.Error as e:
            print(f"SQLite Error: {e}")
        finally:
            cursor.close()
            connection.close()

    async def update_device_bearer_token(self, device_id, token):
        try:
            # Insert registration data into the SQLite registration_data table
            connection = sqlite3.connect(self.sqlite_db_file)
            cursor = connection.cursor()

            update_query = """
                UPDATE registration_data
                SET bearer_token = ?
                WHERE device_id = ?;
            """

            cursor.execute(update_query, (token, device_id))
            connection.commit()
            result = self.get_device_bearer_token(device_id)
            
            return result
        except sqlite3.Error as e:
            print(f"SQLite Error: {e}")
        finally:
            cursor.close()
            connection.close()


    def get_device_data(self, device_id, device_pass=None):
        # Insert registration data into the SQLite registration_data table
        connection = sqlite3.connect(self.sqlite_db_file)
        cursor = connection.cursor()
        # query = "SELECT * FROM registration_data;"
        if device_id is not None and device_pass is not None:
            query = "SELECT * FROM registration_data WHERE device_id = ? AND passcode = ?;"
            cursor.execute(query, (device_id, device_pass,))
        else:
            query = "SELECT * FROM registration_data WHERE device_id = ?;"
            cursor.execute(query, (device_id,))
            
        data = cursor.fetchone()
        cursor.close()
        connection.close()
        if data:
            return data
        else:
            return False
        
    async def get_devices(self):
        # Insert registration data into the SQLite registration_data table
        connection = sqlite3.connect(self.sqlite_db_file)
        cursor = connection.cursor()
        # query = "SELECT * FROM registration_data;"
        query = "SELECT * FROM registration_data ORDER BY id DESC;"
        cursor.execute(query)
        data = cursor.fetchall()
        cursor.close()
        connection.close()
        if data:
            return data
        else:
            return False

    def send_post_request(self, device_id):
        headers = {
            "Authorization": f"Bearer {self.authorization_token}",
            "Content-Type": "application/json"
        }

        payload = {
            "thingList": [
                {
                    "itemType": 1,
                    "id": device_id
                }
            ]
        }

        try:
            response = requests.post(self.api_endpoint, headers=headers, json=payload)
            response.raise_for_status()  # Raise an HTTPError for bad responses

            return response.json(), response.status_code
        except requests.RequestException as e:
            return {"error": f"Error: {e}"}, 500

    def log_device_data(self, device_data):
        try:
            timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
            device_info = device_data.get("data", {}).get("thingList", [{}])[0].get("itemData", {})
            device_id = device_info.get("deviceid", "N/A")
            online = device_info.get("online", "N/A")
            power = device_info.get("params", {}).get("power", "N/A")
            voltage = device_info.get("params", {}).get("voltage", "N/A")
            current = device_info.get("params", {}).get("current", "N/A")
            name = device_info.get("name", "N/A")

            data_dict = {
                "Timestamp": timestamp,
                "Device ID": device_id,
                "Online": online,
                "Power": power,
                "Voltage": voltage,
                "Current": current,
                "Name": name
            }

            self.insert_device_data(data_dict)
            # print(f"#{device_id} Device Data Logged. {data_dict}")
            return data_dict
        except Exception as e:
            print(f"Log Device Data: Exception - {e}")

    def register_device(self):
        device_id = input("Enter device ID: ")
        passcode = getpass.getpass("Enter passcode for API: ")

        device_info = {
            "device_id": device_id,
            "passcode": passcode
        }

        with open(self.device_info_file, "w", encoding='utf-8') as device_info_file:
            json.dump(device_info, device_info_file, ensure_ascii=False)

        with open(self.passcode_file, "w", encoding='utf-8') as passcode_file:
            passcode_file.write(passcode)

        self.insert_registration_data(device_info)

    def load_device_info(self):
        try:
            with open(self.device_info_file, "r", encoding='utf-8') as device_info_file:
                return json.load(device_info_file)
        except FileNotFoundError:
            return None

    def get_stored_data(self):
        connection = sqlite3.connect(self.sqlite_db_file)
        cursor = connection.cursor()

        select_query = "SELECT * FROM device_data;"
        cursor.execute(select_query)
        data = cursor.fetchall()

        cursor.close()
        connection.close()

        return data

    def print_stored_data(self):
        data = self.get_stored_data()
        for row in data:
            print(row)

    def export_to_csv(self):
        data = self.get_stored_data()

        with open('device_data.csv', 'w', newline='', encoding='utf-8') as csvfile:
            csv_writer = csv.writer(csvfile)
            csv_writer.writerow(['Timestamp', 'Device ID', 'Online', 'Power', 'Voltage', 'Current', 'Name'])
            csv_writer.writerows(data)

    def change_column_type(self, db_file, table_name, column_name, new_data_type):
        # Step 1: Create a new table with the desired data type
        new_table_name = f"{table_name}_temp"
        create_table_sql = f"""
            CREATE TABLE {new_table_name} AS
            SELECT * FROM {table_name} LIMIT 0;
        """

        # Step 2: Attach the new table to the database
        attach_sql = f"ATTACH DATABASE '{db_file}' AS temp_db;"

        # Step 3: Copy data from the old table to the new table
        copy_data_sql = f"""
            INSERT INTO {new_table_name} SELECT * FROM {table_name};
        """

        # Step 4: Detach the temporary database
        detach_sql = "DETACH DATABASE temp_db;"

        # Step 5: Drop the old table
        drop_old_table_sql = f"DROP TABLE {table_name};"

        # Step 6: Rename the new table to the old table's name
        rename_new_table_sql = f"ALTER TABLE {new_table_name} RENAME TO {table_name};"

        try:
            connection = sqlite3.connect(db_file)
            cursor = connection.cursor()

            # Step 1: Create a new table
            cursor.execute(create_table_sql)

            # Step 2: Attach the new table
            cursor.execute(attach_sql)

            # Step 3: Copy data
            cursor.execute(copy_data_sql)

            # Step 4: Detach temporary database
            cursor.execute(detach_sql)

            # Step 5: Drop old table
            cursor.execute(drop_old_table_sql)

            # Step 6: Rename new table
            cursor.execute(rename_new_table_sql)

            connection.commit()
            print("Column type changed successfully.")

        except sqlite3.Error as e:
            print(f"Error: {e}")
        finally:
            if connection:
                connection.close()
    
    def get_table_structure(self, table_name, database_path):
        connection = sqlite3.connect(database_path)
        cursor = connection.cursor()

        # Query to get table structure
        query = f"PRAGMA table_info({table_name});"

        try:
            cursor.execute(query)
            columns = cursor.fetchall()
            for column in columns:
                print(column)
            return columns
        except sqlite3.Error as e:
            print(f"SQLite error: {e}")
        finally:
            # Don't forget to close the cursor and connection
            cursor.close()
            connection.close()

    def clear_data(self):
        # Connect to SQLite database
        conn = sqlite3.connect('device_data.db')
        cursor = conn.cursor()

        # Delete all records from the table
        cursor.execute('DELETE FROM device_data;')

        # Commit the changes
        conn.commit()

        # Close the connection
        conn.close()

if __name__ == "__main__":
    # Create an instance of DeviceManager
    device_manager = DeviceManager(
        api_endpoint="https://eu-apia.coolkit.cc/v2/device/thing",
        authorization_token="616c8e6d436ec80abf5dc8874fb6c2bc8682b0e9",
        sqlite_db_file="device_data.db",
        device_info_file="device_info.json",
        passcode_file="passcode.txt"
    )

    device_manager.clear_data()
    # device_manager.change_column_type("device_data.db", "registration_data", "tariff", "FLOAT")
    # device_manager.get_table_structure("registration_data", "device_data.db")
    # device_manager.alter_registration_table()
    # # Create SQLite tables if not exists
    # device_manager.create_tables()

    # # Authenticate device
    # device_info = device_manager.load_device_info()

    # print(device_info)

    # if not device_info:
    #     device_manager.register_device()
    #     device_info = device_manager.load_device_info()

    # # Request passcode before running the script
    # passcode = getpass.getpass("Enter passcode for API: ")

    # device_manager.alter_registration_table()

