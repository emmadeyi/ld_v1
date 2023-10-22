import time
import datetime
import json
import asyncio
from dotenv import dotenv_values
from DatabaseClass import MongoDBClass

config = dotenv_values(".env") 
db_client = config['DATABASE_URL']
db_name = config['DATABASE_NAME']
device_response_data = config['DEVICE_RESPONSE_COLLECTION']
device_info = config['DEVICE_INFO_COLLECTION']

database = MongoDBClass(db_client, db_name)

class DeviceStatusAnalyzer:
    def __init__(self, device_id=None,  device_tariff=None):
        self.device_id = device_id

    async def get_status_transitions(self, device_id, start_time=None, end_time=None):
        filter_query = {'device_id': device_id}
        projection = {"_id": 0}

        if start_time is not None and end_time is not None:
            # Add the timestamp condition for a specific time range
            filter_query['timestamp'] = {'$gte': start_time, '$lte': end_time}

        # Execute the query and return the result
        result = await database.get_device_data(filter_query, projection, device_response_data, 'timestamp')

        return result
    
    async def get_device_tariff(self, device_id):
        try:
            # Assuming registration_data is a collection in your MongoDB database
            query = {"device_id": device_id}
            query_condition = {"tariff": 1, "_id": 0}
            result = await database.get_device_info(query, device_info, query_condition)

            return result["tariff"] if result else None
        except Exception as e:
            print(f"MongoDB Error: {e}")

    async def get_device(self, device_id):
        try:
            # Assuming registration_data is a collection in your MongoDB database
            query = {"device_id": device_id}
            result = await database.get_device(query, device_info)
            return result if result else None
        except Exception as e:
            print(f"MongoDB Error: {e}")

    async def get_most_recent_status_transition(self):        
        try:
            query = {"device_id": self.device_id}
            projection = {"_id": 0}

            result = await database.get_last_device_data(query, device_response_data, projection)

            for transition in result:
                return transition

        except Exception as e:
            print(f"MongoDB Error: {e}")

    async def calculate_status_durations(self, transitions):
        durations = []
        start_time = None
        current_status = None
        most_recent_time = None
        for transition in transitions:
            status = transition['online']
            timestamp = transition['timestamp']
            if current_status is None:
                current_status = status
                start_time = timestamp
                most_recent_time = timestamp
            elif current_status != status:
                duration_seconds = int(time.mktime(time.strptime(most_recent_time, '%Y-%m-%d %H:%M:%S'))) - int(time.mktime(time.strptime(start_time, '%Y-%m-%d %H:%M:%S')))
                duration_hours, remainder = divmod(duration_seconds, 3600)
                duration_minutes, duration_seconds = divmod(remainder, 60)
                durations.append((current_status, start_time, most_recent_time, duration_hours, duration_minutes, duration_seconds))
                current_status = status
                start_time = most_recent_time  
            most_recent_time = timestamp

        if current_status is not None:
        
            most_recent_timestamp = most_recent_time
            
            duration_seconds = int(time.mktime(time.strptime(most_recent_timestamp, '%Y-%m-%d %H:%M:%S'))) - int(time.mktime(time.strptime(start_time, '%Y-%m-%d %H:%M:%S')))
            duration_hours, remainder = divmod(duration_seconds, 3600)
            duration_minutes, duration_seconds = divmod(remainder, 60)
            
            durations.append((current_status, start_time, most_recent_timestamp, duration_hours, duration_minutes, duration_seconds))

        return durations

    async def separate_date_and_time(self, datetime_str):
        date_str, time_str = datetime_str.split(' ')
        return date_str, time_str

    async def format_duration_to_hours_minutes_sec(self, duration_hours, duration_minutes, duration_seconds):
        return f"{duration_hours} hours, {duration_minutes} minutes, {duration_seconds} seconds"

    async def get_current_status(self, status_durations):
        try:
            most_recent_status, most_recent_start_time, most_recent_most_recent_time, most_recent_duration_hours, most_recent_duration_minutes, most_recent_duration_seconds =  status_durations[-1]
            last_start_date, last_start_time = await self.separate_date_and_time(most_recent_start_time)
            last_most_recent_date, last_most_recent_time = await self.separate_date_and_time(most_recent_most_recent_time)

        except Exception as e:
            # Handle any other unexpected exceptions
            print("An unexpected error occurred:", e)

        else:
            # This block is executed if no exception occurs in the try block
            return {
                "status": True if most_recent_status == True else False if most_recent_status == False else 'Connection lost',
                "duration": await self.format_duration_to_hours_minutes_sec(most_recent_duration_hours, most_recent_duration_minutes, most_recent_duration_seconds),
                "start_date": last_start_date,
                "start_time": last_start_time,
                "last_updated_date": last_most_recent_date,
                "last_updated_time": last_most_recent_time
            }

    async def analyze_status(self):
        status_transitions = await self.get_status_transitions(self.device_id)
        if status_transitions:
            status_durations = await self.calculate_status_durations(status_transitions)
            all_status_analysis = []

            for status, start_time, most_recent_time, duration_hours, duration_minutes, duration_seconds in status_durations:
                start_date, start_time = await self.separate_date_and_time(start_time)
                most_recent_date, most_recent_time = await self.separate_date_and_time(most_recent_time)

                all_status_analysis.append({
                    "status": True if status == True else False if status == False else 'Connection lost',
                    "duration": await self.format_duration_to_hours_minutes_sec(duration_hours, duration_minutes, duration_seconds),
                    "start_date": start_date,
                    "start_time": start_time,
                    "last_updated_date": most_recent_date,
                    "last_updated_time": most_recent_time
                })
        
            return {"all_status_transitions":status_transitions, "all_status_analysis":all_status_analysis}
        else:
            return []
        
    async def analyze_current_status(self):
        status_transitions = await self.get_status_transitions(self.device_id)
        if status_transitions:
            status_durations = await self.calculate_status_durations(status_transitions) 
            print(status_durations)
            last_updated_status_statistics = await self.get_current_status(status_durations)
        
            return last_updated_status_statistics
        else:
            return []

    async def extract_hour_from_timestamp(self, timestamp):
        return int(timestamp.split(' ')[1].split(':')[0])

    async def calculate_total_hours(self, status_durations, status='1'):
        return sum(duration[3] * 3600 + duration[4] * 60 + duration[5] for duration in status_durations)
    
    async def total_duration_between(self, start_time, end_time, range_start, range_end):
        # Convert start_time and end_time to datetime objects
        start_datetime = datetime.datetime.strptime(start_time, '%Y-%m-%d %H:%M:%S')
        end_datetime = datetime.datetime.strptime(end_time, '%Y-%m-%d %H:%M:%S')

        total_duration = datetime.timedelta()

        while start_datetime < end_datetime:
            current_time = start_datetime.time()
            
            # Check if the current time is within the nighttime range
            if range_start <= current_time or current_time < range_end:
                # Calculate the time difference until the end of nighttime
                time_difference = datetime.datetime.combine(start_datetime.date(), range_end) - start_datetime

                # Add the time difference to the total duration
                total_duration += time_difference

                # Move the start time to the beginning of the next day
                start_datetime = datetime.datetime.combine(start_datetime.date() + datetime.timedelta(days=1), range_start)
            else:
                # The current time is outside the nighttime range, so move to the next hour
                start_datetime += datetime.timedelta(hours=1)

        # Extract hours, minutes, and seconds from the total duration
        total_hours, remainder = divmod(total_duration.seconds, 3600)
        total_minutes, total_seconds = divmod(remainder, 60)

        return total_hours, total_minutes, total_seconds

    async def calculate_daytime_hours(self, duration_transitions, status):
        daytime_records = []
        for transition in duration_transitions:
            if transition['online'] == status:
                daytime_records = [ record for record in duration_transitions if 0 <= int(record['timestamp'].split(' ')[1].split(':')[0]) < 18 ]
    
        return daytime_records

    async def calculate_nighttime_hours(self, duration_transitions, status):
        nighttime_records = []
        for transition in duration_transitions:
            if transition['online'] == status:
                nighttime_records = [ record for record in duration_transitions if 18 <= int(record['timestamp'].split(' ')[1].split(':')[0]) < 24 ]
                # nighttime_records = [ record for record in duration_transitions if 18 <= int(record['timestamp'].split(' ')[1].split(':')[0]) and int(record['timestamp'].split(' ')[1].split(':')[0]) < 24]

        return nighttime_records
    
    async def get_day_and_night_durations(self, status_durations, transitions):
        night_durations = []
        day_durations = []
        for duration in status_durations:
            duration_start = duration[1]
            duration_end = duration[2]  
            duration_transitions = []
            for transition in transitions:
                if transition['timestamp'] >= duration_start and transition['timestamp'] <= duration_end:                    
                    duration_transitions.append(transition)            
            
            # split duration transitions into daytime and nighttime durations
            daytime_transitions = await self.calculate_daytime_hours(duration_transitions, duration[0])
            nighttime_transitions = await self.calculate_nighttime_hours(duration_transitions, duration[0])

            daytime_durations = await self.calculate_status_durations(daytime_transitions)
            nighttime_durations = await self.calculate_status_durations(nighttime_transitions)
            
            for duration in daytime_durations:
                day_durations.append(duration) 
            for duration in nighttime_durations:
                night_durations.append(duration)
        
        return day_durations, night_durations
    
    async def get_day_and_night_statistics_in_seconds(self, daytime_statistics, nighttime_statistics):
        total_online_duration = daytime_statistics[0] + nighttime_statistics[0]
        total_offline_duration = nighttime_statistics[1] + nighttime_statistics[1]
        total_disconnected_duration = nighttime_statistics[2] + nighttime_statistics[2]
        
        return total_online_duration, total_offline_duration, total_disconnected_duration

    async def get_statistics_in_seconds(self, durations):
        online_duration = 0
        offline_duration = 0
        disconnected_duration = 0
        for duration in durations:
            if duration[0] == True:
                online_duration += duration[3] * 3600 + duration[4] * 60 + duration[5]
            elif duration[0] == False:
                offline_duration += duration[3] * 3600 + duration[4] * 60 + duration[5]
            else:
                disconnected_duration += duration[3] * 3600 + duration[4] * 60 + duration[5]

        return online_duration, offline_duration, disconnected_duration

    async def calculate_statistics(self, start_time=None, end_time=None):
        # Fetch transitions within the specified time range
        transitions = await self.get_status_transitions(self.device_id, start_time, end_time)
        # # Calculate status durations for the specified time range
        status_durations = await self.calculate_status_durations(transitions)
        # # Get day and night durations
        durations = await self.get_day_and_night_durations(status_durations, transitions)
        day_durations = durations[0]
        night_durations = durations[1]

        
        # # get total daytime statistics in seconds
        daytime_statistics = await self.get_statistics_in_seconds(day_durations)
                
        # # get total nighttime statistics in seconds  
        nighttime_statistics = await self.get_statistics_in_seconds(night_durations)
        
        
        # # get total daytime and nighttime statistics in seconds 
        total_statistics = await self.get_day_and_night_statistics_in_seconds(daytime_statistics, nighttime_statistics)
        result = {
            'start_time': transitions[0]['timestamp'] if start_time == None else start_time,
            'end_time': transitions[-1]['timestamp'] if end_time == None else end_time,
            "daytime_online": daytime_statistics[0], 
            "daytime_offline": daytime_statistics[1], 
            "daytime_connection_lost": daytime_statistics[2],
            "nighttime_online": nighttime_statistics[0], 
            "nighttime_offline": nighttime_statistics[1], 
            "nighttime_connection_lost": nighttime_statistics[2],
            "total_online": total_statistics[0], 
            "total_offline": total_statistics[1],
            "total_connection_lost": total_statistics[2]
        }

        return result
    
    async def calculate_energy_statistics(self, start_time=None, end_time=None):
        # Fetch transitions within the specified time range
        transitions = await self.get_status_transitions(self.device_id, start_time, end_time)        
        tariff = await self.get_device_tariff(self.device_id)
        total_online_energy = 0
        total_offline_energy = 0
        total_disconnected_energy = 0
        for transition in transitions:
            if transition['online'] == True:
                # calculate total online energy overrall
                total_online_energy += float(transition['power'])
            elif transition['online'] == False:
                # calculate total offline energy 
                total_offline_energy += float(transition['power'])
            elif transition['online'] == 'N/A':
                # calculate total disconnected energy 
                total_disconnected_energy += float(transition['power'])
            else:
                pass
        kwh = round(await self.convert_energy_to_KWh(total_online_energy), 7)

        result = {
                    'start_time': transitions[0][1] if start_time == None else start_time,
                    'end_time': transitions[-1][1] if end_time == None else end_time,
                    'power_usage':{
                        "kwh": kwh,
                        "cost": round(kwh * float(tariff), 2),
                    }
                }
        return result
    
    async def convert_energy_to_KWh(self, energy_value):
        return (energy_value / 1000) * (1/60)
    
    async def format_duration(self, duration_seconds):
        duration_hours, remainder = divmod(duration_seconds, 3600)
        duration_minutes, duration_seconds = divmod(remainder, 60)
        return f"{duration_hours} hours, {duration_minutes} minutes, {duration_seconds} seconds"
    
    async def get_day_range(self, day_count):
        return datetime.date.today() - datetime.timedelta(days=day_count)
    
    async def get_statistics_of_day_range(self, start_day_difference=0, end_day_difference=0):
        # # Calculate based on difference in day
        # e.g 0 for current day 2 for last 2 days
        start_day = await self.get_day_range(start_day_difference)
        end_day = await self.get_day_range(end_day_difference)
        start_time_current_day = f"{start_day} 00:00:00"
        end_time_current_day = f"{end_day} 23:59:59"
        
        return await self.calculate_statistics(start_time_current_day, end_time_current_day)
    
    async def get_total_status_statistics(self):       
        return await self.calculate_statistics()
    
    async def get_energy_statistics_of_day_range(self, start_day_difference=0, end_day_difference=0):
        # # Calculate based on difference in day
        # e.g 0 for current day 2 for last 2 days
        start_day = datetime.date.today() - datetime.timedelta(days=start_day_difference)
        end_day = datetime.date.today() - datetime.timedelta(days=end_day_difference)
        start_time_current_day = f"{start_day} 00:00:00"
        end_time_current_day = f"{end_day} 23:59:59"
        return await self.calculate_energy_statistics(start_time_current_day, end_time_current_day)
    
    async def get_total_energy_statistics(self):    
        return await self.calculate_energy_statistics()
    
    async def get_day_difference_from_start_of_week(self):
        # Get the current date and time
        now = datetime.datetime.now()

        # Find the current day of the week (Monday is 0 and Sunday is 6)
        current_day_of_week = now.weekday()

        # Calculate the difference between the current day and the start of the week (Monday)
        days_until_start_of_week = current_day_of_week

        return days_until_start_of_week
    
    async def get_day_difference_from_start_of_month(self):
        # Get the current date and time
        now = datetime.datetime.now()# Get the current date and time
        # Calculate the difference between the current day and the start of the month
        days_until_start_of_month = now.day - 1  # Subtract 1 as days are 1-indexed

        return days_until_start_of_month
    
    async def get_day_difference_from_start_of_year(self):
        # Get the current date and time
        now = datetime.datetime.now()
        # Calculate the difference between the current day and the start of the year
        days_until_start_of_year = (now - datetime.datetime(now.year, 1, 1)).days
        return days_until_start_of_year
    
    async def get_statistics(self):
        start_of_week = await self.get_day_difference_from_start_of_week()
        start_of_month = await self.get_day_difference_from_start_of_month()
        start_of_year = await self.get_day_difference_from_start_of_year()

        stats = {
                    "device_id": self.device_id,
                    "current_tariff": await self.get_device_tariff(self.device_id),
                    "energy_statistics": 
                    {
                        "day": await self.get_energy_statistics_of_day_range(),
                        "week": await self.get_energy_statistics_of_day_range(start_of_week),
                        "month": await self.get_energy_statistics_of_day_range(start_of_month),
                        "year": await self.get_energy_statistics_of_day_range(start_of_year)
                    },
                    "status_statistics": 
                    {
                        "day": await self.get_statistics_of_day_range(),
                        "week": await self.get_statistics_of_day_range(start_of_week),
                        "month": await self.get_statistics_of_day_range(start_of_month),
                        "year": await self.get_statistics_of_day_range(start_of_year)
                    }                
                }
        result = await database.store_statistics(stats, config['DEVICE_STATS_COLLECTION'])
        return result

# Define a custom encoder to handle sets
class SetEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, set):
            return list(obj)
        return super().default(obj)
    

# if __name__ == "__main__":
#     analyzer = DeviceStatusAnalyzer('1001e2b96d')
#     results = asyncio.run(analyzer.calculate_statistics())
#     print(results)
    
    