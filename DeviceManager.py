import requests
import json
import time
import sqlite3
import csv
import getpass
import asyncio
from dotenv import dotenv_values
from DatabaseClass import MongoDBClass
# from DeviceStatusAnalyzerClass import DeviceStatusAnalyzer


config = dotenv_values(".env")   

class DeviceManager:
    def __init__(self, device_id, authorization_token, notify_token):
        self.device_id = device_id
        self.authorization_token = authorization_token
        self.notify_token = notify_token

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

    async def send_post_request(self, device_id, auth_token):
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
            response = requests.post(config['API_ENDPOINT'], headers=headers, json=payload)
            response.raise_for_status()  # Raise an HTTPError for bad responses
            print(response.json(), response.status_code)
            return response.json(), response.status_code
        except requests.RequestException as e:
            return {"error": f"Error: {e}"}, 500
    
    async def send_status_notification(data, authorization_token):
        headers = {
            "Authorization": f"Bearer {authorization_token}",
            "Content-Type": "application/json"
        }

        payload = {
                    "start_time": data['start_date'],
                    "device_id": data['device_id'],
                    "status": data['status']
                }
        try:
            response = requests.post(config['NOTIFY_STATUS_CHANGE_API_ENDPOINT'], headers=headers, json=payload)
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

    def export_to_csv(self):
        data = self.get_stored_data()

        with open('device_data.csv', 'w', newline='', encoding='utf-8') as csvfile:
            csv_writer = csv.writer(csvfile)
            csv_writer.writerow(['Timestamp', 'Device ID', 'Online', 'Power', 'Voltage', 'Current', 'Name'])
            csv_writer.writerows(data)

    async def run_device_request(self, device_id):
        global stop_api_request
        call_count = 0
        previous_status = None    
        
        while not stop_api_request.is_set():
            print(f"Sending request for Device: #{device_id}...")
            api_response, status_code = self.send_post_request(device_id, self.authorization_token)
            logged_data = self.log_device_data(api_response)
            print(json.dumps(logged_data, indent=2))
            # check for status change function here
            if logged_data['Online'] != previous_status:
                print(f"\nStatus change detected for device {device_id}. New Status: {logged_data['Online']}")
                previous_status = logged_data['Online']
                status_data = {
                    "status": logged_data['Online'],
                    "device_id": logged_data['Device ID'],
                    "start_date": logged_data['Timestamp']
                }
                print(json.dumps(status_data, indent=2))
                # send post notification
                notification_response = await self.send_status_notification(status_data)
                await self.send_status_notification(status_data)
                print(notification_response)
            # Calculate analysis and put in json file for easy extractions
            print(f"API Response Status Code: {status_code}")
            # await self.get_statistics(device_id)
            # call_count += 1
            # if call_count >= 30:
            #     await get_statistics(device_id)
            #     call_count = 0
            await asyncio.sleep(60)  # Use asyncio.sleep instead of time.sleep

    # async def get_statistics(self, device_id):    
    #     analyzer = DeviceStatusAnalyzer(device_id, config["SQLITE_DB_FILE"])
    #     stats = await analyzer.get_statistics()
    #     # print(stats) save statistics to jsonfile
    #     result = await self.load_device_info(stats, "device_stats_file.json")
    #     return result
    
    async def load_device_info(stats, stats_file):
        try:
            with open(stats_file, "w", encoding='utf-8') as stats_file:
                json.dump(stats, stats_file, ensure_ascii=False, indent=2)
        except FileNotFoundError:
            return None
    

    
async def main():
    # Create an instance of DeviceManager
    device_manager = DeviceManager("1001e2b96d", config['AUHTORIZATION_TOKEN'], config['NOTIFY_STATUS_CHANGE_AUHTORIZATION_TOKEN'])

    response = asyncio.create_task(device_manager.run_device_request("1001e2b96d"))
    await response
    print("loading...")
    # print(response)

asyncio.run(main())

