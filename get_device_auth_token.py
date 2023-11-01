import hashlib
import hmac
import base64
import secrets
import string
import requests
import json
from dotenv import load_dotenv
import os
# Load environment variables from .env file
load_dotenv()
 
def makeSign(key, message):
    j = hmac.new(key.encode(), message.encode(), digestmod=hashlib.sha256)
    return (base64.b64encode(j.digest())).decode()

def get_signature(secret, data):
    message = json.dumps(data)
    sign = makeSign(key=secret, message=message)
    return sign

def generate_random_string(length=8):
    alphabet = string.ascii_letters  # You can customize this string for different character sets
    result = ''.join(secrets.choice(alphabet) for _ in range(length))
    return result

def get_auth_token(signature, appid, nonce, api_endpoint, app_code):
    headers = {
        "Authorization": f"Sign {signature}",
        "Content-Type": "application/json",
        "X-CK-Nonce": f"{nonce}",
        "X-CK-Appid": f"{appid}",

    }

    payload = {
            "code": app_code,
            "redirectUrl": os.environ['REDIRECT_URL'],
            "grantType": os.environ['GRANT_TYPE']
        }

    try:
        response = requests.post(api_endpoint, headers=headers, json=payload)
        response.raise_for_status()  # Raise an HTTPError for bad responses

        return response.json(), response.status_code
    except requests.RequestException as e:
        return {"error": f"Error: {e}"}, 500

