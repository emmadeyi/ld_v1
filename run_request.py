from DeviceStatusAnalyzerClass import DeviceStatusAnalyzer
from fastapi.responses import JSONResponse
import json
import requests
import asyncio
from dotenv import load_dotenv  
from DatabaseClass import MongoDBClass
import datetime
import pytz
import httpx
import os

# Load environment variables from .env file
load_dotenv()

db_client = os.environ['DATABASE_URL']
db_name = os.environ['DATABASE_NAME']
device_info = os.environ['DEVICE_INFO_COLLECTION']
device_response_data = os.environ['DEVICE_RESPONSE_COLLECTION']
device_stats_data = os.environ['DEVICE_STATS_COLLECTION']
device_stats_file = os.environ["DEVICE_STATS_FILE"]
api_endpoint = os.environ["API_ENDPOINT"]
gmt_plus_1_timezone = pytz.timezone(os.environ['TIMEZONE'])

database = MongoDBClass(db_client, db_name)

async def get_devices():
    devices = await database.get_all_devices(device_info)
    return devices

async def run_device_request(device):
    query = {"device_id": device['device_id']}
    projection = {"_id": 0}
    result = await database.get_last_device_data(query, device_response_data, projection)
    if result:
        previous_status = result[0].get('online')
    else:
        previous_status = None

    current_time_gmt_plus_1 = datetime.datetime.now(gmt_plus_1_timezone)
    print(f"..............Processing #{device['device_id']}...........{current_time_gmt_plus_1.strftime('%Y-%m-%d %H:%M:%S')}")
    api_response, status_code = await send_post_request(device)    
    print(f"{device['device_id']} status - {status_code}")
    # if api_response is NA, use previous data
    if result:
        logged_data = await log_device_data(api_response, device['device_id'], result)
    else:
        logged_data = await log_device_data(api_response, device['device_id'])

    if logged_data and logged_data.get('online') is not None:
        if logged_data['online'] != previous_status:
            print(f"\nStatus change detected for device {device['device_id']}. New Status: {logged_data['online']}")
            previous_status = logged_data['online']
            status_data = {
                "status": logged_data['online'],
                "device_id": logged_data['device_id'],
                "start_date": logged_data['timestamp']
            }
            await send_status_notification(status_data)
        await get_statistics(device['device_id'])
    else: 
        print(f"API Response Status Code: {status_code}")
    print(f".............End Processing #{device['device_id']}...........\n")
    
async def send_post_request(device):
    headers = {
        "Authorization": f"Bearer {device['request_token']}",
        "Content-Type": "application/json"
    }
    payload = {
        "thingList": [
            {
                "itemType": 1,
                "id": device['device_id']
            }
        ]
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(os.environ['API_ENDPOINT'], headers=headers, json=payload)
            response.raise_for_status()  # Raise an HTTPError for bad responses
            return response.json(), response.status_code
        except httpx.RequestError as e:
            return {"error": f"Error: {e}"}, 500

async def log_device_data(device_data, device_id=None, prev_data=None):
    try:
        current_time_gmt_plus_1 = datetime.datetime.now(gmt_plus_1_timezone)
        timestamp = current_time_gmt_plus_1.strftime('%Y-%m-%d %H:%M:%S')
        device_info = device_data.get("data", {}).get("thingList", [{}])[0].get("itemData", {})
        if device_info.get("online", 'N/A') == 'N/A':
            print(f"No response from device {device_id}, replacing data with previous data")
        if prev_data:        
            device_id = device_info.get("deviceid", prev_data[0]['device_id'])
            online = device_info.get("online", prev_data[0]['online'])
            power = device_info.get("params", {}).get("power", prev_data[0]['power'])
            voltage = device_info.get("params", {}).get("voltage", prev_data[0]['voltage'])
            current = device_info.get("params", {}).get("current", prev_data[0]['current'])
        else:
            device_id = device_info.get("deviceid", 'N/A')
            online = device_info.get("online", 'N/A')
            power = device_info.get("params", {}).get("power", 'N/A')
            voltage = device_info.get("params", {}).get("voltage", 'N/A')
            current = device_info.get("params", {}).get("current", 'N/A')


        data_dict = {
            "timestamp": timestamp,
            "device_id": device_id,
            "online": online,
            "power": power,
            "voltage": voltage,
            "current": current,
        }            

        result = await database.insert_device_response(data_dict, device_response_data)
        print(f"#{device_id} Data Logged.\n{result}")
        return result
    except Exception as e:
        print(f"Log Device Data: Exception - {e}")

async def get_statistics(device_id):
    analyzer = DeviceStatusAnalyzer(device_id)
    stats = await analyzer.get_statistics()
    return stats

async def load_device_info(stats, stats_file, device_id=None):
    try:
        with open(stats_file, "w", encoding='utf-8') as stats_file:
            json.dump(stats, stats_file, ensure_ascii=False, indent=2)
    except FileNotFoundError:
        return None

async def send_status_notification(data, notify_token=os.environ['NOTIFY_STATUS_CHANGE_AUHTORIZATION_TOKEN'], api_endpoint=os.environ['NOTIFY_STATUS_CHANGE_API_ENDPOINT']):
    print(f'Sending Status change notification for {data["device_id"]}')
    headers = {
        "Authorization": f"Bearer {notify_token}",
        "Content-Type": "application/json"
    }

    payload = {
        "start_time": data['start_date'],
        "device_id": data['device_id'],
        "status": data['status']
    }
    try:
        response = requests.post(api_endpoint, headers=headers, json=payload)
        response.raise_for_status()  # Raise an HTTPError for bad responses

        return response.json(), response.status_code
    except requests.RequestException as e:
        return {"error": f"Error: {e}"}, 500

async def main():
    devices = await get_devices()
    active_devices = [device for device in devices if device.get("active", False)]
    tasks = [run_device_request(device) for device in active_devices]
    print(f"Number of devices running: {len(tasks)} - {datetime.datetime.now(gmt_plus_1_timezone)}")
    await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(main())
