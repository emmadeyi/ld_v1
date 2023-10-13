ToDo

"device_id": "1001e2b96d",
        "user_auth_code": "12345"

Current Status - 
the current status duration - 
the start of the current status and end based on data in DB

Restructure code 
Create a manage device Class that is accessible to all
-Register device
-CRUD Device
-List Registered Device

Convert the Api call to device script to OOP
-Calls should be made to only registered and selected devices
-A ping of the status of all devices(Async)
-Get status of registered device


Get Power usage (today, last 7days, last 30days, current week, current month, current year, last 365days, date range)
-energy usage (today, total)

Statistics
-Total hours (No Light)
-Total hours (Light Dey)
-Daytime hours (No Light)
-Daytime hours (Light Dey)
-Nighttime hours (No light)
-Nighttime hours (Light Dey)
-Average hours Daytime per day, week and month (Light Dey and Light nor dey based on set range)

now I need the below statistics

Statistics
-Total hours (online == False)
-Total hours (online == True)
-Daytime hours (online == False)
-Daytime hours (online == True)
-Nighttime hours (online == False)
-Nighttime hours (online == True)

Develope Web api for frontend (Fastapi)
Database - MongoDB

current is sent frontend (not needed)
Write a function to track status change{
        when status changes, calculate duration, post statistics using link provided (Status and status start time.)
}
Create a table to store statistics update for this that runs every 10mins
current day, week, month, year. - sending all statistics as json response

Authenticate Device
- calculate status change
- Authenticate with bearer token
- MongoDB
- Linode

****Calculate daily, weekly, monthly and current year, store in csv file, update in background 

