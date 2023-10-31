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


####### create venv to use venv
sudo apt install python3.10-venv
python3 -m venv venv
source venv/bin/activate

Run app
$ pip3 install -r requirements.txt
$ pip install --force-reinstall pyopenssl
$ sudo apt-get install libpq-dev
$ python3 DatabaseClass.py - initialize DBase

$ nohup python3 -m uvicorn api:app > api.log 2>&1 &
$ nohup python3 run_request.py > device_request.log 2>&1 &

##########Securing Server


# Kill background process
    ps aux | grep uvicorn or python
    kill -9 process_id



