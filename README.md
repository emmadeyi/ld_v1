$ sudo apt-get update
$ sudo apt install python3-pip
$ sudo apt install nginx

$ cd /etc/nginx/sites-enabled/
$ sudo nano fastapi_nginx

server {    
   listen 80;    
   server_name server_public_ip;    
   location / {        
     proxy_pass http://127.0.0.1:8000;    
   }
}
$ sudo service nginx restart


Installing MongoDB

sudo apt-get install gnupg curl

curl -fsSL https://pgp.mongodb.com/server-7.0.asc | \
   sudo gpg -o /usr/share/keyrings/mongodb-server-7.0.gpg \
   --dearmor

echo "deb [ arch=amd64,arm64 signed-by=/usr/share/keyrings/mongodb-server-7.0.gpg ] https://repo.mongodb.org/apt/ubuntu jammy/mongodb-org/7.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-7.0.list

sudo apt-get update

sudo apt-get install -y mongodb-org

sudo systemctl start mongod

sudo systemctl status mongod

sudo systemctl enable mongod


####### create venv
sudo apt install python3.10-venv
python3 -m venv venv
source venv/bin/activate

########## Run app
$ pip3 install -r requirements.txt
$ python3 DatabaseClass.py - initialize DBase
$ nohup python3 -m uvicorn api:app
$ nohup python3 run_request.py

##########Securing Server


test data

"updated_data": {
        "_id": "652fab4081966ac61b773bc2",
        "device_id": "1001e2b96d",
        "tariff": 68.2,
        "bearer_token": "yDq7R9WGX_VbD2uoptptUwtAlOU97IyglwdYH81T6mLnN9CxRbq-nOzOnwt_HGYOCQmOn9iLR9RM8aSvKpZqKQ",
        "request_token": "1c30586f63074fb831f95d8350bd24e4a1749dab",
        "notify_token": "d7dcde50cf4771acfbf36e28a4c58e96",
        "refresh_token": "e20e2e70aac58647ac53511e24b77b3b2637a63a",
        "active": false
    }

################ Kill background process
    ps aux | grep uvicorn or python
    kill -9 process_id



