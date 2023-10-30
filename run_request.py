from DeviceStatusAnalyzerClass import DeviceStatusAnalyzer
from fastapi.responses import JSONResponse
import json
import requests
import asyncio
from dotenv import dotenv_values
from DatabaseClass import MongoDBClass
import datetime
import pytz
import httpx

config = dotenv_values(".env")
db_client = config['DATABASE_URL']
db_name = config['DATABASE_NAME']
device_info = config['DEVICE_INFO_COLLECTION']
device_response_data = config['DEVICE_RESPONSE_COLLECTION']
device_stats_data = config['DEVICE_STATS_COLLECTION']
device_stats_file = config["DEVICE_STATS_FILE"]
api_endpoint = config["API_ENDPOINT"]
gmt_plus_1_timezone = pytz.timezone(config['TIMEZONE'])

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
    print(api_response, status_code)
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

# def send_post_request(device):
#     headers = {
#         "Authorization": f"Bearer {device['request_token']}",
#         "Content-Type": "application/json"
#     }
#     payload = {
#         "thingList": [
#             {
#                 "itemType": 1,
#                 "id": device['device_id']
#             }
#         ]
#     }
#     try:
#         response = requests.post(config['API_ENDPOINT'], headers=headers, json=payload)
#         response.raise_for_status()  # Raise an HTTPError for bad responses
#         return response.json(), response.status_code
#     except requests.RequestException as e:
#         return {"error": f"Error: {e}"}, 500
    
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
            response = await client.post(config['API_ENDPOINT'], headers=headers, json=payload)
            response.raise_for_status()  # Raise an HTTPError for bad responses
            return response.json(), response.status_code
        except httpx.RequestError as e:
            return {"error": f"Error: {e}"}, 500

async def log_device_data(device_data, device_id=None):
    try:        
        current_time_gmt_plus_1 = datetime.datetime.now(gmt_plus_1_timezone)
        timestamp = current_time_gmt_plus_1.strftime('%Y-%m-%d %H:%M:%S')
        device_info = device_data.get("data", {}).get("thingList", [{}])[0].get("itemData", {})
        device_id = device_info.get("deviceid", "N/A")
        online = device_info.get("online", "N/A")
        power = device_info.get("params", {}).get("power", "N/A")
        voltage = device_info.get("params", {}).get("voltage", "N/A")
        current = device_info.get("params", {}).get("current", "N/A")
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

async def send_status_notification(data, notify_token=config['NOTIFY_STATUS_CHANGE_AUHTORIZATION_TOKEN'], api_endpoint=config['NOTIFY_STATUS_CHANGE_API_ENDPOINT']):
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
    while True:
        devices = await get_devices()
        active_devices = [device for device in devices if device.get("active", False)]
        tasks = [run_device_request(device) for device in active_devices]
        print(f"Number of devices running: {len(tasks)} - {datetime.datetime.now(gmt_plus_1_timezone)}")
        await asyncio.gather(*tasks)
        await asyncio.sleep(60)

if __name__ == "__main__":
    asyncio.run(main())
