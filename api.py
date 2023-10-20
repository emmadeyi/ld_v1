from fastapi import Depends, FastAPI, HTTPException, status, BackgroundTasks
from fastapi.security import OAuth2AuthorizationCodeBearer
from DeviceStatusAnalyzerClass import DeviceStatusAnalyzer
import time
import secrets
from fastapi.responses import JSONResponse
import json
import requests
import asyncio
import subprocess
from dotenv import load_dotenv, dotenv_values
from DatabaseClass import MongoDBClass
import datetime
import pytz
import get_device_auth_token

# load_dotenv() 
config = dotenv_values(".env")   

app = FastAPI()
db_client = config['DATABASE_URL']
db_name = config['DATABASE_NAME']
device_info = config['DEVICE_INFO_COLLECTION']
device_response_data = config['DEVICE_RESPONSE_COLLECTION']
device_stats_data = config['DEVICE_STATS_COLLECTION']
device_stats_file = config["DEVICE_STATS_FILE"]
api_endpoint=config["API_ENDPOINT"]
authorization_token=config["AUHTORIZATION_TOKEN"]

database = MongoDBClass(db_client, db_name)

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

async def get_device_tariff_value(device_id):
        device =  await database.get_single_device(device_id, device_info)
        if not device:
            return None
        return device['tariff']

async def get_device_with_id(device_id):
    device =  await database.get_single_device(device_id, device_info)
    if not device:
        raise credentials_exception
    return device    

async def get_device_with_bearer(token):
    filter_query = {'bearer_token': token}
    device =  await database.get_device(filter_query, device_info)
    if not device:
        raise credentials_exception
    return device

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
    device =  await database.get_single_device(device_id, device_info)
    if not device:
        raise credentials_exception
    return device['bearer_token']

async def get_device_tariff(device_id: str):
    device =  await database.get_single_device(device_id, device_info)
    if not device:
        raise credentials_exception
    return device['tariff']    

async def refresh_device_token(device_id: str):
    device = await get_device_with_id(device_id)
    if device is None:
        raise credentials_exception
    
    token = generate_bearer_token()
    filter_query = {'device_id': device["device_id"]} 
    update_query = {"bearer_token": token}
    return await update_device_data(filter_query, update_query)

async def update_device_data(filter_query, update_query):
    modified_data =  await database.update_device(filter_query, update_query, device_info)
    if modified_data:
        return modified_data
    raise False

async def remove_device(device_id):
    result =  await database.delete_device(device_id, device_info)
    return result

# Register new device
@app.post("/register/")
async def register_device(device_id: str, tariff: float, app_id: str = None, app_secret: str = None,
                          app_code: str = None, refresh_token: str = None, 
                          access_token: str = None, notify_token = None):
    if await database.device_exists(device_id, device_info):
        raise HTTPException(status_code=400, detail="Device already registered")
    print()
    request_token = access_token
    appid = app_id
    # appid = "ZoyNpbjbUyPRa2Uy4I2iEa362mKzOf3N"
    nonce = get_device_auth_token.generate_random_string(8)
    api_endpoint = "https://lytdey.proxy.beeceptor.com/v2/user/oauth/token"
    code = app_code
    # code = "79f9cb91-a621-4613-88e5-faa9caa8dedc"
    data = {
            "code":f"{code}",
            "redirectUrl":"https://lytdey.com/redirect_url",
            "grantType":"authorization_code"
        }
    secret = app_secret
    # secret = 'k6qjuyjeHHsIpluEmvsPVAvzoKIzQY96'
    if request_token is not None:
        device_auth_token = request_token
    elif request_token is None and app_id is not None and app_code is not None and app_secret is not None:
        signature = get_device_auth_token.get_signature(secret, data)
        device_request_token = get_device_auth_token.get_auth_token(signature, appid, nonce, api_endpoint, data)
        if device_request_token[0].get('data'):
            device_auth_token = device_request_token[0].get('data')
        else:
            return {"message": "Error getting request auth token. You can input it manually if generated", "data": device_request_token[0].get('data')}
    else:
        return {"message": "Invalid access auth token"}
    # Register the device
    device_data = {
        "device_id": device_id, 
        "tariff": tariff, 
        "app_id": app_id, 
        "app_secret": app_secret, 
        "app_code": app_code, 
        "bearer_token": generate_bearer_token(),
        "request_token": device_auth_token,
        "notify_token": notify_token,
        "refresh_token": refresh_token,
        "active": True,
        }
    result =  await database.register_device(device_data, device_info)
    return {"message": "Device registered successfully", "device": result}

# Get device
@app.get("/devices/{device_id}")
async def get_device(device_id: str):
    device =  await database.get_single_device(device_id, device_info)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    return device

# Get devices
@app.get("/devices")
async def get_all_devices():
    result =  await database.get_all_devices(device_info)
    if not result:
        raise HTTPException(status_code=404, detail="No Device not found")
    return result

# Get device bearer token
@app.get("/device_token/{device_id}")
async def get_device_token(device_id: str = Depends(get_device_token)):
    token = device_id
    return {"message": "Device Token Fetched", "token": token}

# Get device tarrif
@app.get("/device_tariff/{device_id}")
async def get_device_tariff(device_id: str = Depends(get_device_tariff)):
    tariff = device_id
    return {"message": "Device Tariff Fetched", "Tariff": tariff}

# Protected Routes
# Get device tarrif
@app.put("/update_device_tariff/")
async def update_device_tariff(tariff: float, device: str = Depends(get_current_device)):
    filter_query = {'device_id': device["device_id"]} 
    update_query = {"tariff": tariff}
    modified_data = await update_device_data(filter_query, update_query)
    if modified_data:
        return JSONResponse({"previous_data": device,"updated_data": modified_data})
    raise HTTPException(status_code=404, detail=f"Device with ID {device} not found")

# Update device data
@app.put("/update_device")
async def update_device(tariff: float = None, active: float = None, request_token: str = None, refresh_token: str = None, notify_token = None, device: str = Depends(get_current_device)):
    filter_query = {'device_id': device["device_id"]} 
    update_query = {
        "tariff": tariff if tariff is not None else device["tariff"],
        "request_token": request_token if request_token is not None else device["request_token"],
        "refresh_token": refresh_token if refresh_token is not None else device["refresh_token"],
        "notify_token": notify_token if notify_token is not None else device["notify_token"],
        "active": active if active is not None else device["active"],
        }
    modified_data = await update_device_data(filter_query, update_query)
    if modified_data:
        return JSONResponse({"previous_data": device,"updated_data": modified_data})
    raise HTTPException(status_code=404, detail=f"Device with ID {device} not found")

# Refresh bearer token
@app.put("/refresh_device_token/{device_id}")
async def refresh_device_token(device_id: str = Depends(refresh_device_token)):
    return {"message": "Device Token Refreshed", "token": device_id}

# Get Current Device
@app.get("/device/")
async def read_current_device(current_device: str = Depends(get_current_device)):
    return JSONResponse(current_device)

# Get Device Current Status
@app.get("/device/current_status")
async def read_device_data(current_device: str = Depends(get_current_device)):                
    analyzer = DeviceStatusAnalyzer(current_device["device_id"])  
    last_updated_status_data = await analyzer.analyze_current_status()
    responseData = {
        "device_id": current_device["device_id"],
        "last_updated_status_data": last_updated_status_data
    }
    return JSONResponse(responseData)

# Get Device Current Status History
@app.get("/device/status/history")
async def read_device_day_statistics(current_device: str = Depends(get_current_device)):                
    analyzer = DeviceStatusAnalyzer(current_device["device_id"])  
    last_updated_status_data = await analyzer.analyze_status()
    responseData = {
        "device_id": current_device["device_id"],
        "device_status_history": last_updated_status_data
    }
    return JSONResponse(responseData)

# Get Device Current Day Statistics
@app.get("/device/current_day/statistics")
async def read_device_day_statistics(current_device: str = Depends(get_current_device)):                
    analyzer = DeviceStatusAnalyzer(current_device["device_id"])  
    last_updated_statistics = await analyzer.get_statistics_of_day_range()
    responseData = {
        "device_id": current_device["device_id"],
        "current_day_statistics": last_updated_statistics
    }
    return JSONResponse(responseData)

# Get Device Current Day Power Usage
@app.get("/device/current_day/power_usage")
async def read_device_day_power_usage(current_device: str = Depends(get_current_device)):                
    analyzer = DeviceStatusAnalyzer(current_device["device_id"])  
    last_updated_power_usage = await analyzer.get_energy_statistics_of_day_range()
    responseData = {
        "device_id": current_device["device_id"],
        "current_day_power_usage": last_updated_power_usage
    }
    return JSONResponse(responseData)

# Get Device Current Week Statistics
@app.get("/device/current_week/statistics")
async def read_device_week_statistics(current_device: str = Depends(get_current_device)):                
    analyzer = DeviceStatusAnalyzer(current_device["device_id"]) 
    start_of_week = await analyzer.get_day_difference_from_start_of_week() 
    last_updated_statistics = await analyzer.get_statistics_of_day_range(start_of_week)
    responseData = {
        "device_id": current_device["device_id"],
        "current_week_statistics": last_updated_statistics
    }
    return JSONResponse(responseData)

# Get Device Current Week Power Usage
@app.get("/device/current_week/power_usage")
async def read_device_week_power_usage(current_device: str = Depends(get_current_device)):                
    analyzer = DeviceStatusAnalyzer(current_device["device_id"])  
    start_of_week = await analyzer.get_day_difference_from_start_of_week()
    last_updated_power_usage = await analyzer.get_energy_statistics_of_day_range(start_of_week)
    responseData = {
        "device_id": current_device["device_id"],
        "current_week_power_usage": last_updated_power_usage
    }
    return JSONResponse(responseData)

# Get Device Current month Statistics
@app.get("/device/current_month/statistics")
async def read_device_month_statistics(current_device: str = Depends(get_current_device)):                
    analyzer = DeviceStatusAnalyzer(current_device["device_id"]) 
    start_of_month = await analyzer.get_day_difference_from_start_of_month() 
    last_updated_statistics = await analyzer.get_statistics_of_day_range(start_of_month)
    responseData = {
        "device_id": current_device["device_id"],
        "current_month_statistics": last_updated_statistics
    }
    return JSONResponse(responseData)

# Get Device Current month Power Usage
@app.get("/device/current_month/power_usage")
async def read_device_month_power_usage(current_device: str = Depends(get_current_device)):                
    analyzer = DeviceStatusAnalyzer(current_device["device_id"])  
    start_of_month = await analyzer.get_day_difference_from_start_of_month()
    last_updated_power_usage = await analyzer.get_energy_statistics_of_day_range(start_of_month)
    responseData = {
        "device_id": current_device["device_id"],
        "current_month_power_usage": last_updated_power_usage
    }
    return JSONResponse(responseData)

# Get Device Current year Statistics
@app.get("/device/current_year/statistics")
async def read_device_year_statistics(current_device: str = Depends(get_current_device)):                
    analyzer = DeviceStatusAnalyzer(current_device["device_id"]) 
    start_of_year = await analyzer.get_day_difference_from_start_of_year() 
    last_updated_statistics = await analyzer.get_statistics_of_day_range(start_of_year)
    responseData = {
        "device_id": current_device["device_id"],
        "current_year_statistics": last_updated_statistics
    }
    return JSONResponse(responseData)

# Get Device Current year Power Usage
@app.get("/device/current_year/power_usage")
async def read_device_year_power_usage(current_device: str = Depends(get_current_device)):                
    analyzer = DeviceStatusAnalyzer(current_device["device_id"])  
    start_of_year = await analyzer.get_day_difference_from_start_of_year()
    last_updated_power_usage = await analyzer.get_energy_statistics_of_day_range(start_of_year)
    responseData = {
        "device_id": current_device["device_id"],
        "current_year_power_usage": last_updated_power_usage
    }
    return JSONResponse(responseData)

# Get Device Current day_diff Statistics
@app.get("/device/day_diff/{day_diff}/statistics")
async def read_device_day_diff_statistics(day_diff: int, current_device: str = Depends(get_current_device)):                
    analyzer = DeviceStatusAnalyzer(current_device["device_id"]) 
    last_updated_statistics = await analyzer.get_statistics_of_day_range(day_diff)
    responseData = {
        "device_id": current_device["device_id"],
        "last_updated_statistics": last_updated_statistics
    }
    return JSONResponse(responseData)

# Get Device Current day_diff Power Usage
@app.get("/device/day_diff/{day_diff}/power_usage")
async def read_device_day_diff_power_usage(day_diff: int, current_device: str = Depends(get_current_device)):                
    analyzer = DeviceStatusAnalyzer(current_device["device_id"])  
    last_updated_power_usage = await analyzer.get_energy_statistics_of_day_range(day_diff)
    responseData = {
        "device_id": current_device["device_id"],
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
                    bg.add_task(get_statistics, current_device["device_id"])
                    return JSONResponse({"data": {}, "Error": f""})
            except json.decoder.JSONDecodeError as e:
                bg.add_task(get_statistics, current_device["device_id"])
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
                    bg.add_task(get_statistics, current_device["device_id"])
                    return JSONResponse({"data": {}, "Error": f""})
            except json.decoder.JSONDecodeError as e:
                bg.add_task(get_statistics, current_device["device_id"])
                return JSONResponse({"data": {}, "Error": f"Stats File is empty. {e}"})
    except FileNotFoundError:
            return JSONResponse({"data": {}, "Error": f"Stats File error. {e}"})

@app.get("/activate_device/{action}")
async def start_api_call(action: str, background_tasks: BackgroundTasks, device: str = Depends(get_current_device)):    
    if action == '1':        
        filter_query = {'device_id': device["device_id"]} 
        update_query = {
            "active": True,
            }
        modified_data = await update_device_data(filter_query, update_query)
        if modified_data:
            return JSONResponse({"previous_data": device,"updated_data": modified_data})
        raise HTTPException(status_code=404, detail=f"Device with ID {device} not found")
    elif action == '0':        
        filter_query = {'device_id': device["device_id"]} 
        update_query = {
            "active": False,
            }
        modified_data = await update_device_data(filter_query, update_query)
        if modified_data:
            return JSONResponse({"previous_data": device,"updated_data": modified_data})
        raise HTTPException(status_code=404, detail=f"Device with ID {device} not found")
    else:
        return {"message": "Invalid input"}
    
@app.delete("/devices/{device_id}")
async def delete_device(device_id: str):
    device = await get_device(device_id)
    if device:
        if await remove_device(device['device_id']):
            return {"message": f"Device {device_id} deleted successfully"}
        else:
            raise HTTPException({"message": f"Delete Error"})
    else:
        raise HTTPException(status_code=404, detail="Device not found")

def restart_fastapi_server():
    try:
        subprocess.run(["uvicorn", "api:app", "--reload"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error while restarting FastAPI server: {e}")

async def run_device_request(device):
    call_count = 0
    previous_status = None    
    
    while True:
        print(f"Sending request for Device: #{device['device_id']}...")
        api_response, status_code = send_post_request(device)
        logged_data = await log_device_data(api_response)
        print(json.dumps(logged_data, indent=2))
        # check for status change function here
        if logged_data['online'] != previous_status:
            print(f"\nStatus change detected for device {device['device_id']}. New Status: {logged_data['online']}")
            previous_status = logged_data['online']
            status_data = {
                "status": logged_data['online'],
                "device_id": logged_data['device_id'],
                "start_date": logged_data['timestamp']
            }
            print(json.dumps(status_data, indent=2))
            # send post notification
            notification_response = await send_status_notification(status_data)
            # await send_status_notification(status_data)
            print(notification_response)
        # Calculate analysis and put in json file for easy extractions
        print(f"API Response Status Code: {status_code}")
        await get_statistics(device['device_id'])
        # call_count += 1
        # if call_count >= 30:
        #     await get_statistics(device_id)
        #     call_count = 0
        await asyncio.sleep(60)  # Use asyncio.sleep instead of time.sleep

def send_post_request(device):
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
    try:
        response = requests.post(config['API_ENDPOINT'], headers=headers, json=payload)
        response.raise_for_status()  # Raise an HTTPError for bad responses
        return response.json(), response.status_code
    except requests.RequestException as e:
        return {"error": f"Error: {e}"}, 500

async def log_device_data(device_data):
    try:
        # Get the current time in GMT+1 timezone
        gmt_plus_1_timezone = pytz.timezone(config['TIMEZONE'])  # Adjust to your specific timezone
        current_time_gmt_plus_1 = datetime.datetime.now(gmt_plus_1_timezone)
        
        timestamp = current_time_gmt_plus_1.strftime('%Y-%m-%d %H:%M:%S')
        device_info = device_data.get("data", {}).get("thingList", [{}])[0].get("itemData", {})
        device_id = device_info.get("deviceid", "N/A")
        online = device_info.get("online", "N/A")
        power = device_info.get("params", {}).get("power", "N/A")
        voltage = device_info.get("params", {}).get("voltage", "N/A")
        current = device_info.get("params", {}).get("current", "N/A")
        # name = device_info.get("name", "N/A")
        data_dict = {
            "timestamp": timestamp,
            "device_id": device_id,
            "online": online,
            "power": power,
            "voltage": voltage,
            "current": current,
            # "Name": name
        }
        
        result = await database.insert_device_response(data_dict, device_response_data)
        print(f"#{device_id} Device Data Logged. {result}")
        return result
    except Exception as e:
        print(f"Log Device Data: Exception - {e}")

async def get_statistics(device_id):    
    analyzer = DeviceStatusAnalyzer(device_id)
    print(device_id)
    stats = await analyzer.get_statistics()
    print(stats) 
    result = await load_device_info(stats, "device_stats_file.json")
    return result

async def load_device_info(stats, stats_file):
    try:
        with open(stats_file, "w", encoding='utf-8') as stats_file:
            json.dump(stats, stats_file, ensure_ascii=False, indent=2)
    except FileNotFoundError:
        return None
    
async def send_status_notification(data, notify_token=config['NOTIFY_STATUS_CHANGE_AUHTORIZATION_TOKEN'], api_endpoint=config['NOTIFY_STATUS_CHANGE_API_ENDPOINT']):
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
