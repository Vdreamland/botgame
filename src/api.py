import requests
from src.config import BASE_URL, HEADERS

def get_account_state(headers=None):
    use_headers = headers if headers else HEADERS
    url = f"{BASE_URL}/api/accounts/me"
    resp = requests.get(url, headers=use_headers)
    if resp.status_code == 200:
        return resp.json().get("data")
    else:
        print(f"Error fetching account state: {resp.status_code}")
        return None

def redeem_welcome_code(headers=None):
    use_headers = headers if headers else HEADERS
    url = f"{BASE_URL}/api/redeem"
    req_headers = use_headers.copy()
    req_headers["Idempotency-Key"] = f"redeem-welcome-{use_headers['Authorization'][-8:]}"
    body = {"code": "WELCOME"}
    resp = requests.post(url, headers=req_headers, json=body)
    if resp.status_code == 200:
        print("Successfully redeemed WELCOME bundle!")
        return resp.json().get("data")
    elif resp.status_code == 409:
        print("WELCOME bundle already redeemed or inventory full.")
        return None
    else:
        print(f"Redeem returned status: {resp.status_code}, detail: {resp.text}")
        return None