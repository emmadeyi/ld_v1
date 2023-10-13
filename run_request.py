import requests
import json
import getpass
import asyncio
import sys
import subprocess
from passlib.context import CryptContext
# import classes
from DeviceManager import DeviceManager
from DeviceStatusAnalyzerClass import DeviceStatusAnalyzer
import os
# from dotenv import load_dotenv

sqlite_db_file = "device_data.db"
device_stats_file = "device_stats.json"
passcode_file = "passcode.txt"
api_endpoint = "https://eu-apia.coolkit.cc/v2/device/thing"
authorization_token = "616c8e6d436ec80abf5dc8874fb6c2bc8682b0e9"

# sqlite_db_file = os.environ.get('SQLITE_DB_FILE')
# device_stats_file = os.environ.get('DEVICE_STATS_FILE')
# passcode_file = os.environ.get('PASSCODE_FILE')
# api_endpoint = os.environ.get('API_ENDPOINT')
# authorization_token = os.environ.get('AUHTORIZATION_TOKEN')

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_pass, hashed_pass):
    return pwd_context.verify(plain_pass, hashed_pass)


def get_password_hash(password):
    return pwd_context.hash(password)

async def start_api_call(device_manager, stop_event):
    device_id = input("Enter Device ID for API: ")
    device_pass = getpass.getpass("Enter passcode for API: ")
    device = device_manager.get_device_data(device_id)
    previous_status = None

    if device:
        if verify_password(device_pass, device[2]):
            call_count = 0
            await get_statistics(device[1])
            while not stop_event.is_set():
                print(f"Sending request for Device: #{device[1]}...")
                api_response, status_code = device_manager.send_post_request(device[1])
                logged_data = device_manager.log_device_data(api_response)
                print(json.dumps(logged_data, indent=2))

                # check for status change function here
                if logged_data['Online'] != previous_status:
                    print(f"\nStatus change detected for device {device[1]}. New Status: {logged_data['Online']}")
                    previous_status = logged_data['Online']
                    status_data = {
                        "status": logged_data['Online'],
                        "device_id": logged_data['Device ID'],
                        "start_date": logged_data['Timestamp']
                    }
                    print(json.dumps(status_data, indent=2))
                    # send post notification
                    notification_response = await send_status_notification(status_data)
                    print(notification_response)

                # Calculate analysis and put in json file for easy extractions
                print(f"API Response Status Code: {status_code}")
                call_count += 1
                if call_count >= 3:
                    await get_statistics(device[1])
                    call_count = 0
                await asyncio.sleep(2)  # Use asyncio.sleep instead of time.sleep
        else:
            print("Invalid Credentials")
    else:
        print("Device Not Found")

async def get_statistics(device_id):    
    analyzer = DeviceStatusAnalyzer(device_id)
    stats = await analyzer.get_statistics()
    # print(stats) save statistics to jsonfile
    result = await load_device_info(stats, "device_stats_file.json")
    return result

async def load_device_info(stats, stats_file):
    try:
        with open(stats_file, "w", encoding='utf-8') as stats_file:
            json.dump(stats, stats_file, ensure_ascii=False, indent=2)
    except FileNotFoundError:
        return None

async def get_user_input(stop_event):
    while True:
        print("Select an option:")
        print("1. Start Device API Call")
        print("2. Start FastAPI Sever")
        print("3. Exit")

        choice = input("Enter your choice (1-2): ")

        if choice == "1":
            # Run the API call asynchronously
            await start_api_call(device_manager, stop_event)
        elif choice == "2":
            restart_fastapi_server()
        elif choice == "3":
            exit_program(stop_event)
        else:
            print("Invalid choice. Select enter from options 1-3.")

def restart_fastapi_server():
    try:
        subprocess.run(["uvicorn", "api:app", "--reload"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error while restarting FastAPI server: {e}")

async def send_status_notification(data):
        # api_endpoint = "https://lightdey.bubbleapps.io/version-test/api/1.1/wf/update_status_change/initialize"
        api_endpoint = "https://lightdey.bubbleapps.io/version-test/api/1.1/wf/update_status_change/"
        # api_endpoint = "https://lytdey.com/version-test/api/1.1/wf/update_status_change"
        authorization_token = "d7dcde50cf4771acfbf36e28a4c58e96"
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
            response = requests.post(api_endpoint, headers=headers, json=payload)
            response.raise_for_status()  # Raise an HTTPError for bad responses

            return response.json(), response.status_code
        except requests.RequestException as e:
            return {"error": f"Error: {e}"}, 500

def exit_program(stop_event):
    print("Exiting the program.")
    stop_event.set()  # Set the event to signal tasks to stop
    sys.exit()

if __name__ == "__main__":
    device_manager = DeviceManager(
        api_endpoint=api_endpoint,
        authorization_token=authorization_token,
        sqlite_db_file=sqlite_db_file,
        device_info_file="device_info.json",
        passcode_file=passcode_file
    )

    stop_event = asyncio.Event()

    # Run the user input loop in the main thread
    asyncio.run(get_user_input(stop_event))