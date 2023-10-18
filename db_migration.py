import sqlite3
from pymongo import MongoClient

# SQLite connection
sqlite_conn = sqlite3.connect('device_data.db')
sqlite_cursor = sqlite_conn.cursor()

# MongoDB connection
mongo_client = MongoClient('mongodb://localhost:27017/')
# create db
database_name = 'energy_api'
mongo_db = mongo_client[database_name]
# device_info = 'device_info'
device_response_data = 'device_response_data'
# device_stats_data = 'device_stats_data'
# collection_device_info = mongo_db[device_info]
collection_device_response_data = mongo_db[device_response_data]
# collection_device_stats_data = mongo_db[device_stats_data]

# Fetch data from SQLite
# sqlite_cursor.execute('SELECT * FROM registration_data')
sqlite_cursor.execute('SELECT * FROM device_data')
rows = sqlite_cursor.fetchall()

# Iterate through SQLite rows and insert into MongoDB
for row in rows:
    # Assuming a mapping of SQLite columns to MongoDB fields
    # document = {
    #     'device_id': row[1],
    #     'passcode': row[2],
    #     'bearer_token': row[8],
    #     'tariff': row[9],
    #     'notify_api': None,
    #     'notify_bearer_token': None,
    #     'geo_lat': None,
    #     'geo_log': None,
    #     'tag': None,
    #     'is_active': None,
    # }
    document = {
        'timestamp': row[1],
        'device_id': row[2],
        'online': row[3],
        'power': row[4],
        'voltage': row[5],
        'current': row[6],
    }

    # Insert the document into MongoDB
    collection_device_response_data.insert_one(document)
    print(document)
    
results = list(collection_device_response_data.find())
for result in results:
    print(result)


# # Close connections
sqlite_conn.close()
mongo_client.close()
