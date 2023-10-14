from fastapi import Depends, FastAPI, HTTPException, status, BackgroundTasks
from fastapi.security import OAuth2AuthorizationCodeBearer
from DeviceManager import DeviceManager
from DeviceStatusAnalyzerClass import DeviceStatusAnalyzer
import sqlite3
import secrets
from fastapi.responses import JSONResponse
import json
import requests
import asyncio
import subprocess
from dotenv import load_dotenv, dotenv_values

# load_dotenv() 
config = dotenv_values(".env")   

app = FastAPI()
# sqlite_db_file="device_data.db"
sqlite_db_file=config["SQLITE_DB_FILE"]
device_stats_file = config["DEVICE_STATS_FILE"]
api_endpoint=config["API_ENDPOINT"]
authorization_token=config["AUHTORIZATION_TOKEN"]
# device_info_file=config["DEVICE_STATS_FILE"]
passcode_file=config["PASSCODE_FILE"]

# Define a security dependency using OAuth2AuthorizationCodeBearer
oauth2_scheme = OAuth2AuthorizationCodeBearer(
    tokenUrl="token",
    authorizationUrl="authorize",  # Add the authorizationUrl argument
)

credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

async def get_device_bearer_token(device_id):
        try:
            # Insert registration data into the SQLite registration_data table
            connection = sqlite3.connect(sqlite_db_file)
            cursor = connection.cursor()
            if device_id is not None:
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

async def get_device_tariff_value(device_id):
        try:
            # Insert registration data into the SQLite registration_data table
            connection = sqlite3.connect(sqlite_db_file)
            cursor = connection.cursor()
            if device_id is not None:
                query = f"SELECT tariff_value FROM registration_data WHERE device_id = ?;"
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

async def update_device_tariff_value(device_id, tariff):
        try:
            # Insert registration data into the SQLite registration_data table
            connection = sqlite3.connect(sqlite_db_file)
            cursor = connection.cursor()
            if device_id is not None:
                query = '''
                UPDATE registration_data
                SET tariff_value = ?
                WHERE device_id = ?;'''
                cursor.execute(query, (tariff, device_id,)) 
                connection.commit()
                result = await get_device_tariff_value(device_id)
                return result
            else:
                return None
        except sqlite3.Error as e:
            print(f"SQLite Error: {e}")
        finally:
            cursor.close()
            connection.close()

async def get_device_with_id(device_id):
        try:
            # Insert registration data into the SQLite registration_data table
            connection = sqlite3.connect(sqlite_db_file)
            cursor = connection.cursor()
            if device_id is not None:
                query = "SELECT * FROM registration_data WHERE device_id = ?;"
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

async def get_device_with_bearer(bearer_token):
        try:
            # Insert registration data into the SQLite registration_data table
            connection = sqlite3.connect(sqlite_db_file)
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

async def update_device_bearer_token(device_id, token):
    try:
        # Insert registration data into the SQLite registration_data table
        connection = sqlite3.connect(sqlite_db_file)
        cursor = connection.cursor()
        update_query = """
            UPDATE registration_data
            SET bearer_token = ?
            WHERE device_id = ?;
        """
        cursor.execute(update_query, (token, device_id))
        connection.commit()
        result = await get_device_bearer_token(device_id)        
        return result
    except sqlite3.Error as e:
        print(f"SQLite Error: {e}")
    finally:
        cursor.close()
        connection.close()

def generate_bearer_token():
    # Generate a secure random string (you can customize the length)
    return secrets.token_urlsafe(64)

# Dependency to get the current device based on the bearer token
async def get_current_device(token: str = Depends(oauth2_scheme)):
    device = await get_device_with_bearer(token)
    if device is None:
        raise  credentials_exception
    return device

async def get_device_token(device_id: str):
    token = await get_device_bearer_token(device_id)
    if token is None:
        raise credentials_exception
    return token

async def get_device_tariff(device_id: str):
    result = await get_device_tariff_value(device_id)
    if result is None:
        raise credentials_exception
    return result

async def update_device_tariff(device_id: str):
    device = await get_device_with_id(device_id)
    if device is None:
        raise credentials_exception
    return device_id

async def refresh_device_token(device_id: str):
    device = await get_device_with_id(device_id)
    if device is None:
        raise credentials_exception
    
    token = generate_bearer_token()
    return await update_device_bearer_token(device_id, token)

# Get device bearer token
@app.get("/get_device_token/{device_id}")
async def get_device_token(token: str = Depends(get_device_token)):
    return {"message": "Device Token Fetched", "token": token}

# Get device tarrif
@app.get("/get_device_tariff/{device_id}")
async def get_device_tariff(device_id: str = Depends(get_device_tariff)):
    return {"message": "Device Token Fetched", "token": device_id}

# Get device tarrif
@app.get("/update_device_tariff/{device_id}")
async def update_device_tariff(tariff: str, device_id: str = Depends(update_device_tariff)):
    new_tariff = await update_device_tariff_value(device_id, tariff)
    # new_tariff = await get_device_tariff_value(device_id)
    return {"message": "Device Token Fetched", "parsed-token": tariff, "token": new_tariff}

# Refresh bearer token
@app.get("/refresh_device_token/{device_id}")
async def refresh_device_token(device_id: str = Depends(refresh_device_token)):
    return {"message": "Device Token Refreshed", "token": device_id}

# Get Current Device
@app.get("/device/")
async def read_current_device(current_device: str = Depends(get_current_device)):
    return JSONResponse(current_device)

# Get Device Current Status
@app.get("/device/current_status")
async def read_device_data(current_device: str = Depends(get_current_device)):                
    analyzer = DeviceStatusAnalyzer(current_device[1])  
    last_updated_status_data = await analyzer.analyze_current_status()
    responseData = {
        "device_id": current_device[1],
        "last_updated_status_data": last_updated_status_data
    }
    return JSONResponse(responseData)

# Get Device Current Status History
@app.get("/device/status/history")
async def read_device_day_statistics(current_device: str = Depends(get_current_device)):                
    analyzer = DeviceStatusAnalyzer(current_device[1])  
    last_updated_status_data = await analyzer.analyze_status()
    responseData = {
        "device_id": current_device[1],
        "device_status_history": last_updated_status_data
    }
    return JSONResponse(responseData)

# Get Device Current Day Statistics
@app.get("/device/current_day/statistics")
async def read_device_day_statistics(current_device: str = Depends(get_current_device)):                
    analyzer = DeviceStatusAnalyzer(current_device[1])  
    last_updated_statistics = await analyzer.get_statistics_of_day_range()
    responseData = {
        "device_id": current_device[1],
        "current_day_statistics": last_updated_statistics
    }
    return JSONResponse(responseData)

# Get Device Current Day Power Usage
@app.get("/device/current_day/power_usage")
async def read_device_day_power_usage(current_device: str = Depends(get_current_device)):                
    analyzer = DeviceStatusAnalyzer(current_device[1])  
    last_updated_power_usage = await analyzer.get_energy_statistics_of_day_range()
    responseData = {
        "device_id": current_device[1],
        "current_day_power_usage": last_updated_power_usage
    }
    return JSONResponse(responseData)

# Get Device Current Week Statistics
@app.get("/device/current_week/statistics")
async def read_device_week_statistics(current_device: str = Depends(get_current_device)):                
    analyzer = DeviceStatusAnalyzer(current_device[1]) 
    start_of_week = await analyzer.get_day_difference_from_start_of_week() 
    last_updated_statistics = await analyzer.get_statistics_of_day_range(start_of_week)
    responseData = {
        "device_id": current_device[1],
        "current_week_statistics": last_updated_statistics
    }
    return JSONResponse(responseData)

# Get Device Current Week Power Usage
@app.get("/device/current_week/power_usage")
async def read_device_week_power_usage(current_device: str = Depends(get_current_device)):                
    analyzer = DeviceStatusAnalyzer(current_device[1])  
    start_of_week = await analyzer.get_day_difference_from_start_of_week()
    last_updated_power_usage = await analyzer.get_energy_statistics_of_day_range(start_of_week)
    responseData = {
        "device_id": current_device[1],
        "current_week_power_usage": last_updated_power_usage
    }
    return JSONResponse(responseData)

# Get Device Current month Statistics
@app.get("/device/current_month/statistics")
async def read_device_month_statistics(current_device: str = Depends(get_current_device)):                
    analyzer = DeviceStatusAnalyzer(current_device[1]) 
    start_of_month = await analyzer.get_day_difference_from_start_of_month() 
    last_updated_statistics = await analyzer.get_statistics_of_day_range(start_of_month)
    responseData = {
        "device_id": current_device[1],
        "current_month_statistics": last_updated_statistics
    }
    return JSONResponse(responseData)

# Get Device Current month Power Usage
@app.get("/device/current_month/power_usage")
async def read_device_month_power_usage(current_device: str = Depends(get_current_device)):                
    analyzer = DeviceStatusAnalyzer(current_device[1])  
    start_of_month = await analyzer.get_day_difference_from_start_of_month()
    last_updated_power_usage = await analyzer.get_energy_statistics_of_day_range(start_of_month)
    responseData = {
        "device_id": current_device[1],
        "current_month_power_usage": last_updated_power_usage
    }
    return JSONResponse(responseData)

# Get Device Current year Statistics
@app.get("/device/current_year/statistics")
async def read_device_year_statistics(current_device: str = Depends(get_current_device)):                
    analyzer = DeviceStatusAnalyzer(current_device[1]) 
    start_of_year = await analyzer.get_day_difference_from_start_of_year() 
    last_updated_statistics = await analyzer.get_statistics_of_day_range(start_of_year)
    responseData = {
        "device_id": current_device[1],
        "current_year_statistics": last_updated_statistics
    }
    return JSONResponse(responseData)

# Get Device Current year Power Usage
@app.get("/device/current_year/power_usage")
async def read_device_year_power_usage(current_device: str = Depends(get_current_device)):                
    analyzer = DeviceStatusAnalyzer(current_device[1])  
    start_of_year = await analyzer.get_day_difference_from_start_of_year()
    last_updated_power_usage = await analyzer.get_energy_statistics_of_day_range(start_of_year)
    responseData = {
        "device_id": current_device[1],
        "current_year_power_usage": last_updated_power_usage
    }
    return JSONResponse(responseData)

# Get Device Current year Statistics
@app.get("/device/complete_statistics")
async def read_device_year_statistics(current_device: str = Depends(get_current_device)):                
    analyzer = DeviceStatusAnalyzer(current_device[1]) 
    last_updated_status_data = await analyzer.get_total_status_statistics()
    responseData = {
        "device_id": current_device[1],
        "total_statistics": last_updated_status_data
    }
    return JSONResponse(responseData)

# Get Device Current year Power Usage
@app.get("/device/total_power_usage")
async def read_device_year_power_usage(current_device: str = Depends(get_current_device)):                
    analyzer = DeviceStatusAnalyzer(current_device[1])  
    last_updated_status_data = await analyzer.get_total_energy_statistics()
    responseData = {
        "device_id": current_device[1],
        "total_power_usage": last_updated_status_data
    }
    return JSONResponse(responseData)

# Get Device Current day_diff Statistics
@app.get("/device/day_diff/{day_diff}/statistics")
async def read_device_day_diff_statistics(day_diff: int, current_device: str = Depends(get_current_device)):                
    analyzer = DeviceStatusAnalyzer(current_device[1]) 
    last_updated_statistics = await analyzer.get_statistics_of_day_range(day_diff)
    responseData = {
        "device_id": current_device[1],
        "last_updated_statistics": last_updated_statistics
    }
    return JSONResponse(responseData)

# Get Device Current day_diff Power Usage
@app.get("/device/day_diff/{day_diff}/power_usage")
async def read_device_day_diff_power_usage(day_diff: int, current_device: str = Depends(get_current_device)):                
    analyzer = DeviceStatusAnalyzer(current_device[1])  
    last_updated_power_usage = await analyzer.get_energy_statistics_of_day_range(day_diff)
    responseData = {
        "device_id": current_device[1],
        "last_updated_power_usage": last_updated_power_usage
    }
    return JSONResponse(responseData)

# Get Device Aggregated Stats
@app.get("/device/aggregated/statistics")
async def read_device_aggregated_stats(bg: BackgroundTasks, current_device: str = Depends(get_current_device)):     
    try:
        with open(device_stats_file, "r") as json_file:
            try:
                json_data = json.load(json_file)
                if 'status_statistics' in json_data:
                    status_statistics_data = json_data['status_statistics']
                    return JSONResponse(content=status_statistics_data)
                else:
                    # run calculation
                    bg.add_task(get_statistics, current_device[1])
                    return JSONResponse({"data": {}, "Error": f""})
            except json.decoder.JSONDecodeError as e:
                bg.add_task(get_statistics, current_device[1])
                return JSONResponse({"data": {}, "Error": f"Stats File is empty. {e}"})
    except FileNotFoundError:
            return JSONResponse({"data": {}, "Error": f"Stats File error. {e}"})
    
@app.get("/device/aggregated/power_usage")
async def read_device_aggregated_stats(bg: BackgroundTasks, current_device: str = Depends(get_current_device)): 
    try:
        with open(device_stats_file, "r") as json_file:
            try:
                json_data = json.load(json_file)
                if 'energy_statistics' in json_data:
                    energy_statistics_data = json_data['energy_statistics']
                    return JSONResponse(content=energy_statistics_data)
                else:
                    # run calculation
                    bg.add_task(get_statistics, current_device[1])
                    return JSONResponse({"data": {}, "Error": f""})
            except json.decoder.JSONDecodeError as e:
                bg.add_task(get_statistics, current_device[1])
                return JSONResponse({"data": {}, "Error": f"Stats File is empty. {e}"})
    except FileNotFoundError:
            return JSONResponse({"data": {}, "Error": f"Stats File error. {e}"})


# ##############################
stop_api_request = asyncio.Event()

@app.get("/device_request/{action}")
async def start_api_call(action: str, background_tasks: BackgroundTasks, device: str = Depends(get_current_device)):
    device_manager = DeviceManager(
        api_endpoint=api_endpoint,
        authorization_token=authorization_token,
        sqlite_db_file=sqlite_db_file,
        device_info_file=device_stats_file,
        passcode_file=passcode_file
    )
    # Start the asynchronous API request 
    if action == '0':
        stop_api_request.set() # to stop the request
        return {"message": "Device request stopped", "device": device[1]}
    if action == '1':
        # api_task = asyncio.create_task(run_device_request(device_manager, device[1]))
        # await api_task
        background_tasks.add_task(run_device_request,device_manager, device[1])
    # if action == '2':
    #     restart_fastapi_server()
    #     return {"message": "Restarting Server..."}

    return {"message": "API Call to Devices Stated", "device": device[1]}

def restart_fastapi_server():
    try:
        subprocess.run(["uvicorn", "api:app", "--reload"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error while restarting FastAPI server: {e}")

async def run_device_request(device_manager, device_id):
    global stop_api_request
    call_count = 0
    previous_status = None    
    
    while not stop_api_request.is_set():
        print(f"Sending request for Device: #{device_id}...")
        api_response, status_code = device_manager.send_post_request(device_id)
        logged_data = device_manager.log_device_data(api_response)
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
            notification_response = await send_status_notification(status_data)
            await send_status_notification(status_data)
            print(notification_response)
        # Calculate analysis and put in json file for easy extractions
        print(f"API Response Status Code: {status_code}")
        call_count += 1
        if call_count >= 30:
            await get_statistics(device_id)
            call_count = 0
        await asyncio.sleep(60)  # Use asyncio.sleep instead of time.sleep

def send_post_request(device_id):
    headers = {
        "Authorization": f"Bearer {authorization_token}",
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
        response = requests.post(api_endpoint, headers=headers, json=payload)
        response.raise_for_status()  # Raise an HTTPError for bad responses
        return response.json(), response.status_code
    except requests.RequestException as e:
        return {"error": f"Error: {e}"}, 500

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
    
async def send_status_notification(data, api_endpoint=config['NOTIFY_STATUS_CHANGE_API_ENDPOINT'], authorization_token=config['NOTIFY_STATUS_CHANGE_AUHTORIZATION_TOKEN']):
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
