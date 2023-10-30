from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import dotenv_values
from pymongo import ReturnDocument
import asyncio

# load_dotenv()
config = dotenv_values(".env")
db_client = config['DATABASE_URL']
db_name = config['DATABASE_NAME']

class MongoDBClass:
    def __init__(self, database_url, database_name):
        self.client = AsyncIOMotorClient(database_url)
        self.db = self.client[database_name]

    async def register_device(self, device_data, collection_name):
        devices_collection = self.db[collection_name]
        result = await devices_collection.insert_one(device_data)

        # Check if the insertion was successful
        if result.acknowledged:
            # Fetch the inserted document using the inserted_id
            inserted_document = await devices_collection.find_one({"_id": result.inserted_id})

            # Convert ObjectId to string for serialization
            inserted_document["_id"] = str(inserted_document["_id"])

            return inserted_document

        # Handle the case where insertion failed
        return None  # You might want to raise an exception or handle this differently

    async def insert_device_response(self, device_data, collection_name):
        devices_collection = self.db[collection_name]
        result = await devices_collection.insert_one(device_data)

        # Check if the insertion was successful
        if result.acknowledged:
            # Fetch the inserted document using the inserted_id
            inserted_document = await devices_collection.find_one({"_id": result.inserted_id})

            # Convert ObjectId to string for serialization
            inserted_document["_id"] = str(inserted_document["_id"])
            return inserted_document

        # Handle the case where insertion failed
        return None  # You might want to raise an exception or handle this differently

    async def store_statistics(self, stats, collection_name):
        collection = self.db[collection_name]

        # Define the filter criteria (in this case, we use the device_id)
        filter_criteria = {"device_id": stats["device_id"]}

        print(f"storing stats for #{stats['device_id']}")
        # Replace the existing record or insert a new one if it doesn't exist
        result = await collection.replace_one(filter_criteria, stats, upsert=True)

        # Optionally, you can check the result
        if result.modified_count > 0:
            print(f"Updated existing stats record for device {stats['device_id']}")
        else:
            print(f"Inserted a new stats record for device {stats['device_id']}")
            
    async def get_statistics_record(self, collection_name, device_id):
        collection = self.db[collection_name]

        # Define the filter criteria (in this case, we use the device_id)
        filter_criteria = {"device_id": device_id}

        # Find one device record based on the filter
        device_record = await collection.find_one(filter_criteria, {"_id": 0})
        if device_id:
            # Convert ObjectId to string for JSON serialization
            if '_id' in device_record:
                device_record['_id'] = str(device_record['_id'])
        
            
        return device_record


    async def get_single_device(self, device_id, collection_name):
        devices_collection = self.db[collection_name]
        device = await devices_collection.find_one({'device_id': device_id})

        # Convert ObjectId to string for serialization
        if device and '_id' in device:
            device['_id'] = str(device['_id'])

        return device

    async def get_device(self, filter, collection_name):
        devices_collection = self.db[collection_name]
        device = await devices_collection.find_one(filter)

        # Convert ObjectId to string for serialization
        if device and '_id' in device:
            device['_id'] = str(device['_id'])

        return device

    async def get_device_info(self, filter, collection_name, condition=None):
        devices_collection = self.db[collection_name]
        device = await devices_collection.find_one(filter, condition)

        # Convert ObjectId to string for serialization
        if device and '_id' in device:
            device['_id'] = str(device['_id'])

        return device

    async def get_all_devices(self, collection_name):
        devices_collection = self.db[collection_name]

        # Fetch all devices
        devices = await devices_collection.find().to_list(None)

        # Convert ObjectId to string for serialization in each document
        for device in devices:
            if '_id' in device:
                device['_id'] = str(device['_id'])

        return devices

    async def get_device_data(self, query_filter, condition, collection_name, sort):
        data_collection = self.db[collection_name]

        # Fetch all devices
        data = await data_collection.find(query_filter, condition).sort(sort).to_list(None)

        # Convert ObjectId to string for serialization in each document
        for d in data:
            if '_id' in d:
                d['_id'] = str(d['_id'])

        return data

    async def get_last_device_data(self, query_filter, collection_name, condition):
        data_collection = self.db[collection_name]

        # Fetch all devices
        data = await data_collection.find(query_filter, condition).sort("timestamp", -1).limit(1).to_list(None)

        # Convert ObjectId to string for serialization in each document
        for d in data:
            if '_id' in d:
                d['_id'] = str(d['_id'])

        return data

    async def device_exists(self, device_id, collection_name):
        devices_collection = self.db[collection_name]
        return await devices_collection.count_documents({'device_id': device_id}) > 0

    async def update_device(self, filter_query, update_query, collection_name):
        # Get the specified collection
        collection = self.db[collection_name]

        # Perform the update and return the modified document
        updated_document = await collection.find_one_and_update(
            filter_query,
            {'$set': update_query},
            return_document=ReturnDocument.AFTER  # Specify that the modified document should be returned
        )

        if updated_document:
            # Convert ObjectId to string for serialization
            updated_document['_id'] = str(updated_document['_id'])
            return updated_document

        return f"Device not found"

    async def delete_device(self, device_id, collection_name):
        devices_collection = self.db[collection_name]
        result = await devices_collection.delete_one({'device_id': device_id})
        return result.deleted_count > 0

    async def clear_database(self):
        # List all collections in the database
        collections = await self.db.list_collection_names()

        # Iterate through collections and delete all documents
        for collection_name in collections:
            collection = self.db[collection_name]
            await collection.delete_many({})

        print(f"All documents in the database '{self.db.name}' have been deleted.")

    async def clear_collection(self, collection_name):
        # Get the specified collection
        collection = self.db[collection_name]

        # Delete all documents in the collection
        await collection.delete_many({})

        print(f"All documents in the collection '{collection_name}' have been deleted.")

    async def initialize_database(self, collection_name):
        # Get the specified collection
        collection = self.db[collection_name]

        # Clear (delete all documents from) the existing collection
        await collection.delete_many({})

        print(f"Collection '{collection_name}' cleared.")

        # Print a message indicating the initialization
        print(f"Database '{self.db.name}' and collection '{collection_name}' initialized.")

    def close_connection(self):
        self.client.close()

async def init_database():
    db = MongoDBClass(db_client, db_name)
    # init DEVICE_INFO_COLLECTION
    # collection_name = config['DEVICE_INFO_COLLECTION']
    # await db.initialize_database(collection_name)
    # init DEVICE_RESPONSE_COLLECTION
    # collection_name = config['DEVICE_RESPONSE_COLLECTION']
    # await db.initialize_database(collection_name)
    # init DEVICE_STATS_COLLECTION
    # collection_name = config['DEVICE_STATS_COLLECTION']
    # await db.initialize_database(collection_name)

    # Close the database connection
    db.close_connection()

# Example Usage:
if __name__ == "__main__":
    asyncio.run(init_database())
