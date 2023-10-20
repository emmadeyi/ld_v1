# Python
import hashlib
import hmac
import base64
import secrets
import string
import requests
import json

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

def get_auth_token(signature, appid, nonce, api_endpoint,data):
    headers = {
        "Authorization": f"Sign {signature}",
        "Content-Type": "application/json",
        "X-CK-Nonce": f"{nonce}",
        "X-CK-Appid": f"{appid}",

    }

    payload = {
            "code":"79f9cb91-a621-4613-88e5-faa9caa8dedc",
            "redirectUrl":"https://lytdey.com/redirect_url",
            "grantType":"authorization_code"
        }

    try:
        response = requests.post(api_endpoint, headers=headers, json=payload)
        response.raise_for_status()  # Raise an HTTPError for bad responses

        return response.json(), response.status_code
    except requests.RequestException as e:
        return {"error": f"Error: {e}"}, 500
    

if __name__ == "__main__":
    appid = "ZoyNpbjbUyPRa2Uy4I2iEa362mKzOf3N"
    nonce = generate_random_string(8)
    api_endpoint = "https://lytdey.proxy.beeceptor.com/v2/user/oauth/token"
    code = "bb11aaec-9ed6-43e3-b757-8705e985212b"
    data = {
            "code":f"{code}",
            "redirectUrl":"https://lytdey.com/redirect_url",
            "grantType":"authorization_code"
        }
    secret = 'k6qjuyjeHHsIpluEmvsPVAvzoKIzQY96'
    signature = get_signature(secret, data)
    print(signature)

    print(get_auth_token(signature, appid, nonce, api_endpoint, data))
