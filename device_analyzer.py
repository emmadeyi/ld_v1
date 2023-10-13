import requests
import json
import time
import sqlite3
import csv
import getpass
import threading
from queue import Queue
import asyncio
import secrets
from passlib.context import CryptContext
# import classes
from DeviceManager import DeviceManager
from DeviceStatusAnalyzerClass import DeviceStatusAnalyzer

sqlite_db_file="device_data.db"
device_info_file="device_info.json"
passcode_file="passcode.txt"
api_endpoint="https://eu-apia.coolkit.cc/v2/device/thing"
authorization_token="616c8e6d436ec80abf5dc8874fb6c2bc8682b0e9"

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
def verify_password(plain_pass, hashed_pass):
    return pwd_context.verify(plain_pass, hashed_pass)

def get_password_hash(password):
    return pwd_context.hash(password)

# Initialize device manager
device_manager = DeviceManager(
    api_endpoint=api_endpoint,
    authorization_token=authorization_token,
    sqlite_db_file=sqlite_db_file,
    device_info_file=device_info_file,
    passcode_file=passcode_file
)

async def get_user_input():

    while True:
        print("Select an option:")
        print("1. Register Device")
        print("2. Update Device tariff") 
        print("3. Update Device api and token") 
        print("4. Get Device Current Status")
        print("5. Get Device Current Day Power Usage")
        print("6. Get Device Current Day Statistics")
        print("7. Get Device Current Week Statistics")
        print("8. Get Device Current Month Statistics")
        print("9. Get Device Current Year Statistics")
        print("10. Get Device Current Week Power Usage")
        print("11. Get Device Current Month Power Usage")
        print("12. Get Device Current Year Power Usage")
        print("13. Get Device Historical Statistics")
        print("14. Get Device Total Power Usage")
        print("15. Get Device Total Status Statistics")
        print("16. Get registered devices") 
        print("17. Exit")
        print("=================================")
        print("18. Update Device Passcode") 
        print("19. Refresh Device Bearer Token") 
        print("20. Get Device") 

        choice = input("Enter your choice from options: ")

        if choice == "1":
            device_id = input("Enter Device ID for API: ")
            device_tariff = input("Enter Device Tariff: ")
            device_api = input("Enter Device API URL: ")
            device_token = input("Enter Device API Token: ")
            device_pass = getpass.getpass("Enter passcode for API: ")
            # device_id = "1001e2b96d"
            # device_pass = "12345"
            register_new_device(device_id, device_pass, device_tariff, device_api, device_token)
        elif choice == "2":
            device_id = input("Enter Device ID for API: ")
            device_pass = getpass.getpass("Enter passcode for API: ")
            device = device_manager.get_device_data(device_id)
            if device:
                if verify_password(device_pass, device[2]):       
                    device_tariff = input(f"Enter Tariff value for #{device_id}: ")
                    # Update Device Details            
                    result = await device_manager.update_device_tariff(device_id, device_tariff)
                    print(json.dumps(result, indent=2))
                else:
                    print("Invalid Credentials")
            else:
                print("Device not found in System")
        elif choice == "3":
            device_id = input("Enter Device ID for API: ")
            device_pass = getpass.getpass("Enter passcode for API: ")
            device = device_manager.get_device_data(device_id)
            if device:
                if verify_password(device_pass, device[2]):        
                    device_api = input("Enter Device API URL: ")
                    device_token = input("Enter Device API Token: ")
                    # Update Device Details            
                    result = device_manager.update_device_api(device_id, device_api, device_token)
                    print(json.dumps(result, indent=2))
                else:
                    print("Invalid Credentials")
            else:
                print("Device not found in System")
        elif choice == "18":
            device_id = input("Enter Device ID for API: ")
            device_pass = getpass.getpass("Enter passcode for API: ")
            device = device_manager.get_device_data(device_id)
            if device:
                # print(device_pass, device[2], verify_password(device_pass, device[2]))
                if verify_password(device_pass, device[2]):
                    passcode = getpass.getpass("Enter New Passcode: ")
                    # Update Device Details                
                    hashed_passcode = pwd_context.hash(passcode)         
                    # result = await device_manager.update_device_passcode(device_id, device_pass)
                    result = await device_manager.update_device_passcode(device_id, hashed_passcode)
                    print(json.dumps(result, indent=2))
                else:
                    print("Invalid Credentials")
            else:
                print("Device not found in System")
        elif choice == "19":
            device_id = input("Enter Device ID for API: ")
            device_pass = getpass.getpass("Enter passcode for API: ")
            device = device_manager.get_device_data(device_id)
            if device:
                # print(device_pass, device[2], verify_password(device_pass, device[2]))
                if verify_password(device_pass, device[2]):
                    print("updating bearer token")
                    token = secrets.token_hex(32)         
                    result = await device_manager.update_device_bearer_token(device_id, token)
                    print(json.dumps(result, indent=2))
                else:
                    print("Invalid Credentials")
            else:
                print("Device not found in System")
        elif choice == "20":
            device_id = input("Enter Device ID for API: ")
            device_pass = getpass.getpass("Enter passcode for API: ")
            device = device_manager.get_device_data(device_id)
            if device:
                # print(device_pass, device[2], verify_password(device_pass, device[2]))
                if verify_password(device_pass, device[2]):
                    print("updating bearer token")
                    print(json.dumps(device, indent=2))
                else:
                    print("Invalid Credentials")
            else:
                print("Device not found in System")
        elif choice == "4":
            # device_id = input("Enter Device ID for API: ")
            # device_pass = getpass.getpass("Enter passcode for API: ")
            device_id = "1001e2b96d"
            device_pass = "12345"
            result = await get_current_device_status(device_id)
            print(json.dumps(result, indent=2))
        elif choice == "5":
            # device_id = input("Enter Device ID for API: ")
            # device_pass = getpass.getpass("Enter passcode for API: ")
            device_id = "1001e2b96d"
            device_pass = "12345"
            result = await get_current_power_usage(device_id)
            print(json.dumps(result, indent=2))
        elif choice == "6":
            # device_id = input("Enter Device ID for API: ")
            # device_pass = getpass.getpass("Enter passcode for API: ")
            device_id = "1001e2b96d"
            device_pass = "12345"
            result = await get_current_day_statistics(device_id)
            print(json.dumps(result, indent=2))
        elif choice == "7":
            # device_id = input("Enter Device ID for API: ")
            # device_pass = getpass.getpass("Enter passcode for API: ")
            device_id = "1001e2b96d"
            device_pass = "12345"
            result = await get_current_week_statistics(device_id)
            print(json.dumps(result, indent=2))
        elif choice == "8":
            # device_id = input("Enter Device ID for API: ")
            # device_pass = getpass.getpass("Enter passcode for API: ")
            device_id = "1001e2b96d"
            device_pass = "12345"
            result = await get_current_month_statistics(device_id)
            print(json.dumps(result, indent=2))
        elif choice == "9":
            # device_id = input("Enter Device ID for API: ")
            # device_pass = getpass.getpass("Enter passcode for API: ")
            device_id = "1001e2b96d"
            device_pass = "12345"
            result = await get_current_year_statistics(device_id)
            print(json.dumps(result, indent=2))
        elif choice == "10":
            # device_id = input("Enter Device ID for API: ")
            # device_pass = getpass.getpass("Enter passcode for API: ")
            device_id = "1001e2b96d"
            device_pass = "12345"
            result = await get_current_week_power_usage(device_id)
            print(json.dumps(result, indent=2))
        elif choice == "11":
            # device_id = input("Enter Device ID for API: ")
            # device_pass = getpass.getpass("Enter passcode for API: ")
            device_id = "1001e2b96d"
            device_pass = "12345"
            result = await get_current_month_power_usage(device_id)
            print(json.dumps(result, indent=2))
        elif choice == "12":
            # device_id = input("Enter Device ID for API: ")
            # device_pass = getpass.getpass("Enter passcode for API: ")
            device_id = "1001e2b96d"
            device_pass = "12345"
            result = await get_current_year_power_usage(device_id)
            print(json.dumps(result, indent=2))
        elif choice == "13":
            # device_id = input("Enter Device ID for API: ")
            # device_pass = getpass.getpass("Enter passcode for API: ")
            device_id = "1001e2b96d"
            device_pass = "12345"
            result = await get_device_status_history(device_id)
            print(json.dumps(result, indent=2))
        elif choice == "14":
            # device_id = input("Enter Device ID for API: ")
            # device_pass = getpass.getpass("Enter passcode for API: ")
            device_id = "1001e2b96d"
            device_pass = "12345"
            result = await get_total_power_usage(device_id)
            print(json.dumps(result, indent=2))
        elif choice == "15":
            # device_id = input("Enter Device ID for API: ")
            # device_pass = getpass.getpass("Enter passcode for API: ")
            device_id = "1001e2b96d"
            device_pass = "12345"
            result = await get_total_status_statistics(device_id)
            print(json.dumps(result, indent=2))
        elif choice == "16":
            result = await device_manager.get_devices()
            print(json.dumps(result, indent=2))
        elif choice == "17":
            exit_program()
            break
        else:
            print(f"Invalid choice. {choice}. Select enter from options 1-18.")

async def get_current_device_status(device_id):
    # Initialize device analyzer class
    analyzer = DeviceStatusAnalyzer(device_id)
    last_updated_status_data = await analyzer.analyze_current_status()
    responseData = {
        "device_id": device_id,
        "current_day_device_status": last_updated_status_data
    }
    return responseData

async def get_device_status_history(device_id):
    # Initialize device analyzer class
    analyzer = DeviceStatusAnalyzer(device_id)
    last_updated_status_data = await analyzer.analyze_status()
    responseData = {
        "device_id": device_id,
        "device_status_history": last_updated_status_data
    }
    return responseData

async def get_current_day_statistics(device_id):
    # Initialize device analyzer class
    analyzer = DeviceStatusAnalyzer(device_id)
    last_updated_status_data = await analyzer.get_statistics_of_day_range()
    responseData = {
        "current_day_statistics": last_updated_status_data
    }
    return responseData

async def get_current_power_usage(device_id):
    # Initialize device analyzer class
    analyzer = DeviceStatusAnalyzer(device_id)
    last_updated_power_usage = await analyzer.get_energy_statistics_of_day_range()
    responseData = {
        "current_day_power_usage": last_updated_power_usage
    }
    return responseData

async def get_current_week_statistics(device_id):    
    # Initialize device analyzer class
    analyzer = DeviceStatusAnalyzer(device_id)
    start_of_week = await analyzer.get_day_difference_from_start_of_week()    
    last_updated_status_data = await analyzer.get_statistics_of_day_range(start_of_week)
    responseData = {
        "current_week_statistics": last_updated_status_data
    }
    return responseData

async def get_current_week_power_usage(device_id):
    # Initialize device analyzer class
    analyzer = DeviceStatusAnalyzer(device_id)
    start_of_week = await analyzer.get_day_difference_from_start_of_week()    
    last_updated_power_usage = await analyzer.get_energy_statistics_of_day_range(start_of_week)
    responseData = {
        "current_week_power_usage": last_updated_power_usage
    }
    return responseData

async def get_current_month_statistics(device_id):    
    # Initialize device analyzer class
    analyzer = DeviceStatusAnalyzer(device_id)
    start_of_month = await analyzer.get_day_difference_from_start_of_month()    
    last_updated_status_data = await analyzer.get_statistics_of_day_range(start_of_month)
    responseData = {
        "current_month_statistics": last_updated_status_data
    }
    return responseData

async def get_current_month_power_usage(device_id):
    # Initialize device analyzer class
    analyzer = DeviceStatusAnalyzer(device_id)
    start_of_month = await analyzer.get_day_difference_from_start_of_month()    
    last_updated_power_usage = await analyzer.get_energy_statistics_of_day_range(start_of_month)
    responseData = {
        "current_month_power_usage": last_updated_power_usage
    }
    return responseData

async def get_current_year_statistics(device_id):    
    # Initialize device analyzer class
    analyzer = DeviceStatusAnalyzer(device_id)
    start_of_year = await analyzer.get_day_difference_from_start_of_year()    
    last_updated_status_data = await analyzer.get_statistics_of_day_range(start_of_year)
    responseData = {
        "current_year_statistics": last_updated_status_data
    }
    return responseData

async def get_current_year_power_usage(device_id):
    # Initialize device analyzer class
    analyzer = DeviceStatusAnalyzer(device_id)
    start_of_year = await analyzer.get_day_difference_from_start_of_year()    
    last_updated_power_usage = await analyzer.get_energy_statistics_of_day_range(start_of_year)
    responseData = {
        "current_year_power_usage": last_updated_power_usage
    }
    return responseData

async def get_total_power_usage(device_id):
    # Initialize device analyzer class
    analyzer = DeviceStatusAnalyzer(device_id)  
    last_updated_power_usage = await analyzer.get_total_energy_statistics()
    responseData = {
        "total_power_usage": last_updated_power_usage
    }
    return responseData

async def get_total_status_statistics(device_id):
    # Initialize device analyzer class
    analyzer = DeviceStatusAnalyzer(device_id)  
    last_updated_status_data = await analyzer.get_total_status_statistics()
    responseData = {
        "total_power_usage": last_updated_status_data
    }
    return responseData

def register_new_device(device_id, device_pass, device_tariff=None, device_api=None, device_token=None):    
    # register new device
    # Create SQLite tables if not exists
    device_manager.create_tables()    
    if device_manager.get_device_data(device_id, device_pass):
        print(f"#{device_id} already in system")
        return
    else: 
        device_info = device_manager.insert_registration_data(device_id, device_pass, device_tariff, device_api, device_token)
        return device_info

def exit_program():
    print("Exiting the program.")

async def main():
    loop = asyncio.get_event_loop()
    await get_user_input()

if __name__ == "__main__":
    # print(secrets.token_hex(32))
    asyncio.run(main())
