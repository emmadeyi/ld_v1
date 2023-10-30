from fastapi import Depends, FastAPI, HTTPException, status, BackgroundTasks
from fastapi.security import OAuth2AuthorizationCodeBearer
from DeviceStatusAnalyzerClass import DeviceStatusAnalyzer
import secrets
from fastapi.responses import JSONResponse
from dotenv import dotenv_values
from DatabaseClass import MongoDBClass
import get_device_auth_token 
from run_request import send_post_request
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional
from pydantic import BaseModel
from fastapi.security import OAuth2PasswordBearer

config = dotenv_values(".env")   

app = FastAPI()
db_client = config['DATABASE_URL']
db_name = config['DATABASE_NAME']
device_info = config['DEVICE_INFO_COLLECTION']
device_response_data = config['DEVICE_RESPONSE_COLLECTION']
device_stats_data = config['DEVICE_STATS_COLLECTION']
api_endpoint=config["API_ENDPOINT"]

database = MongoDBClass(db_client, db_name)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
# Configure security
ALGORITHM = config['ALGORITHM']
SECRET_KEY = config['SECRET_KEY']
ACCESS_TOKEN_EXPIRE_MINUTES = config['ACCESS_TOKEN_EXPIRE_MINUTES']

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

# Device model for authentication
class DeviceInDB(BaseModel):
    device_id: str
    active: bool

# User model for token
class Device(BaseModel):
    device_id: str
    active: bool

# Token model
class Token(BaseModel):
    access_token: str
    token_type: str

async def get_device(device_id: str):
    device =  await database.get_single_device(device_id, device_info)
    if not device:
        raise credentials_exception
    return DeviceInDB(**device)  

# Function to create a JWT token
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# Dependency to get the current device
async def get_current_device(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        device_id: str = payload.get("sub")
        if device_id is None:
            raise HTTPException(status_code=400, detail="Could not validate device")
        device_data = await get_device(device_id)
        if device_data is None:
            raise HTTPException(status_code=400, detail="User not found")
        device = Device(device_id=device_data['device_id'], active=device_data['active'])
    except JWTError:
        raise HTTPException(status_code=401, detail="Could not validate device")
    return device

async def get_device_tariff_value(device_id):
        device =  await database.get_single_device(device_id, device_info)
        if not device:
            return None
        return device['tariff']  

def generate_bearer_token():
    # Generate a secure random string (you can customize the length)
    return secrets.token_urlsafe(64)

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
    device = await get_device(device_id)
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
    request_token = access_token
    nonce = get_device_auth_token.generate_random_string(8)
    api_endpoint = "https://lytdey.proxy.beeceptor.com/v2/user/oauth/token"
    data = {
            "code":f"{app_code}",
            "redirectUrl":"https://lytdey.com/redirect_url",
            "grantType":"authorization_code"
        }
    secret = app_secret
    if request_token is not None:
        device_auth_token = request_token
    elif request_token is None and app_id is not None and app_code is not None and app_secret is not None:
        signature = get_device_auth_token.get_signature(secret, data)
        device_request_token = get_device_auth_token.get_auth_token(signature, app_id, nonce, api_endpoint, app_code)
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
# @app.get("/device_token/{device_id}")
# async def get_device_token(device_id: str = Depends(get_device_token)):
#     token = device_id
#     return {"message": "Device Token Fetched", "token": token}

# Get device tarrif
@app.get("/device_tariff/{device_id}")
async def get_device_tariff(device_id: str = Depends(get_device_tariff)):
    tariff = device_id
    return {"message": "Device Tariff Fetched", "Tariff": tariff}

@app.get("/device_token/{device_id}", response_model=Token)
async def get_token(device_id: str):
    device = await database.get_single_device(device_id, device_info)
    if not await database.get_single_device(device_id, device_info):
        raise HTTPException(
            status_code=404, detail="Device not registered"
        )
    
    if not device['active']:
        raise HTTPException(
            status_code=400, detail="Inactive device"
        )

    access_token = create_access_token(data={"sub": device['device_id']})
    return {"access_token": access_token, "token_type": "bearer"}



################ Protected Routes
# Get device tarrif
@app.put("/update_device_tariff/")
async def update_device_tariff(tariff: float, device: str = Depends(get_current_device)):
    filter_query = {'device_id': device["device_id"]} 
    update_query = {"tariff": tariff}
    modified_data = await update_device_data(filter_query, update_query)
    if modified_data:
        return JSONResponse({"device_id": device['device_id'], "previous_tariff": device['tariff'],"updated_tariff": modified_data['tariff']})
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
    return {"message": "Device Token Refreshed", "token": device_id['bearer_token']}

# Get Current Device
@app.get("/device/")
async def read_current_device(current_device: str = Depends(get_current_device)):
    return JSONResponse(current_device)

@app.get("/device_status")
async def read_current_device(current_device: str = Depends(get_current_device)):
    response_data, response_status = send_post_request(current_device)
    return JSONResponse(response_data, response_status)

# Get Device Current Status
@app.get("/device/current_status")
async def read_device_data(current_device: str = Depends(get_current_device)):                
    analyzer = DeviceStatusAnalyzer(current_device.device_id)  
    last_updated_status_data = await analyzer.analyze_current_status()
    responseData = {
        "device_id": current_device.device_id,
        "last_updated_status_data": last_updated_status_data
    }
    return JSONResponse(responseData)

# Get Device Current Status History
@app.get("/device/status/history")
async def read_device_day_statistics(current_device: str = Depends(get_current_device)):                
    analyzer = DeviceStatusAnalyzer(current_device.device_id)  
    last_updated_status_data = await analyzer.analyze_status()
    responseData = {
        "device_id": current_device.device_id,
        "device_status_history": last_updated_status_data
    }
    return JSONResponse(responseData)

# Get Device Current Day Statistics
@app.get("/device/current_day/statistics")
async def read_device_day_statistics(current_device: str = Depends(get_current_device)):                
    analyzer = DeviceStatusAnalyzer(current_device.device_id)  
    last_updated_statistics = await analyzer.get_statistics_of_day_range()
    responseData = {
        "device_id": current_device.device_id,
        "current_day_statistics": last_updated_statistics
    }
    return JSONResponse(responseData)

# Get Device Current Day Power Usage
@app.get("/device/current_day/power_usage")
async def read_device_day_power_usage(current_device: str = Depends(get_current_device)):                
    analyzer = DeviceStatusAnalyzer(current_device.device_id)  
    last_updated_power_usage = await analyzer.get_energy_statistics_of_day_range()
    responseData = {
        "device_id": current_device.device_id,
        "current_day_power_usage": last_updated_power_usage
    }
    return JSONResponse(responseData)

# Get Device Current Week Statistics
@app.get("/device/current_week/statistics")
async def read_device_week_statistics(current_device: str = Depends(get_current_device)):                
    analyzer = DeviceStatusAnalyzer(current_device.device_id) 
    start_of_week = await analyzer.get_day_difference_from_start_of_week() 
    last_updated_statistics = await analyzer.get_statistics_of_day_range(start_of_week)
    responseData = {
        "device_id": current_device.device_id,
        "current_week_statistics": last_updated_statistics
    }
    return JSONResponse(responseData)

# Get Device Current Week Power Usage
@app.get("/device/current_week/power_usage")
async def read_device_week_power_usage(current_device: str = Depends(get_current_device)):                
    analyzer = DeviceStatusAnalyzer(current_device.device_id)  
    start_of_week = await analyzer.get_day_difference_from_start_of_week()
    last_updated_power_usage = await analyzer.get_energy_statistics_of_day_range(start_of_week)
    responseData = {
        "device_id": current_device.device_id,
        "current_week_power_usage": last_updated_power_usage
    }
    return JSONResponse(responseData)

# Get Device Current month Statistics
@app.get("/device/current_month/statistics")
async def read_device_month_statistics(current_device: str = Depends(get_current_device)):                
    analyzer = DeviceStatusAnalyzer(current_device.device_id) 
    start_of_month = await analyzer.get_day_difference_from_start_of_month() 
    last_updated_statistics = await analyzer.get_statistics_of_day_range(start_of_month)
    responseData = {
        "device_id": current_device.device_id,
        "current_month_statistics": last_updated_statistics
    }
    return JSONResponse(responseData)

# Get Device Current month Power Usage
@app.get("/device/current_month/power_usage")
async def read_device_month_power_usage(current_device: str = Depends(get_current_device)):                
    analyzer = DeviceStatusAnalyzer(current_device.device_id)  
    start_of_month = await analyzer.get_day_difference_from_start_of_month()
    last_updated_power_usage = await analyzer.get_energy_statistics_of_day_range(start_of_month)
    responseData = {
        "device_id": current_device.device_id,
        "current_month_power_usage": last_updated_power_usage
    }
    return JSONResponse(responseData)

# Get Device Current year Statistics
@app.get("/device/current_year/statistics")
async def read_device_year_statistics(current_device: str = Depends(get_current_device)):                
    analyzer = DeviceStatusAnalyzer(current_device.device_id) 
    start_of_year = await analyzer.get_day_difference_from_start_of_year() 
    last_updated_statistics = await analyzer.get_statistics_of_day_range(start_of_year)
    responseData = {
        "device_id": current_device.device_id,
        "current_year_statistics": last_updated_statistics
    }
    return JSONResponse(responseData)

# Get Device Current year Power Usage
@app.get("/device/current_year/power_usage")
async def read_device_year_power_usage(current_device: str = Depends(get_current_device)):                
    analyzer = DeviceStatusAnalyzer(current_device.device_id)  
    start_of_year = await analyzer.get_day_difference_from_start_of_year()
    last_updated_power_usage = await analyzer.get_energy_statistics_of_day_range(start_of_year)
    responseData = {
        "device_id": current_device.device_id,
        "current_year_power_usage": last_updated_power_usage
    }
    return JSONResponse(responseData)

# Get Device Current day_diff Statistics
@app.get("/device/day_diff/{day_diff}/statistics")
async def read_device_day_diff_statistics(day_diff: int, current_device: str = Depends(get_current_device)):                
    analyzer = DeviceStatusAnalyzer(current_device.device_id) 
    last_updated_statistics = await analyzer.get_statistics_of_day_range(day_diff)
    responseData = {
        "device_id": current_device.device_id,
        "last_updated_statistics": last_updated_statistics
    }
    return JSONResponse(responseData)

# Get Device Current day_diff Power Usage
@app.get("/device/day_diff/{day_diff}/power_usage")
async def read_device_day_diff_power_usage(day_diff: int, current_device: str = Depends(get_current_device)):                
    analyzer = DeviceStatusAnalyzer(current_device.device_id)  
    last_updated_power_usage = await analyzer.get_energy_statistics_of_day_range(day_diff)
    responseData = {
        "device_id": current_device.device_id,
        "last_updated_power_usage": last_updated_power_usage
    }
    return JSONResponse(responseData)

# Get Device Aggregated Stats
@app.get("/device/aggregated/statistics")
async def read_device_aggregated_stats(bg: BackgroundTasks, current_device: str = Depends(get_current_device)): 
    stats = await database.get_statistics_record(config['DEVICE_STATS_COLLECTION'], current_device.device_id)
    bg.add_task(get_statistics, current_device.device_id)
    if stats:
        return JSONResponse({"device_id": stats['device_id'],
                             "tariff": stats['current_tariff'], 
                             "status_statistics": stats['status_statistics']
                             })
    return JSONResponse({"data": {}, "Error": f""})
    
@app.get("/device/aggregated/power_usage")
async def read_device_aggregated_stats(bg: BackgroundTasks, current_device: str = Depends(get_current_device)): 
    stats = await database.get_statistics_record(config['DEVICE_STATS_COLLECTION'], current_device.device_id)
    bg.add_task(get_statistics, current_device.device_id)
    if stats:
        return JSONResponse({"device_id": stats['device_id'],
                             "tariff": stats['current_tariff'], 
                             "energy_statistics": stats['energy_statistics']
                             })
    return JSONResponse({"data": {}, "Error": f""})

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
    
# @app.delete("/devices/{device_id}")
# async def delete_device(device_id: str):
#     device = await get_device(device_id)
#     if device:
#         if await remove_device(device['device_id']):
#             return {"message": f"Device {device_id} deleted successfully"}
#         else:
#             raise HTTPException({"message": f"Delete Error"})
#     else:
#         raise HTTPException(status_code=404, detail="Device not found")

async def get_statistics(device_id):    
    analyzer = DeviceStatusAnalyzer(device_id)
    result = await analyzer.get_statistics()
    return result
