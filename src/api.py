import requests
from src.config import BASE_URL, HEADERS

def get_account_state():
    url = f"{BASE_URL}/api/accounts/me"
    resp = requests.get(url, headers=HEADERS)
    if resp.status_code == 200:
        return resp.json().get("data")
    else:
        print(f"Error fetching account state: {resp.status_code}")
        return None

def redeem_welcome_code():
    url = f"{BASE_URL}/api/redeem"
    headers = HEADERS.copy()
    headers["Idempotency-Key"] = f"redeem-welcome-{HEADERS['Authorization'][-8:]}"
    body = {"code": "WELCOME"}
    resp = requests.post(url, headers=headers, json=body)
    if resp.status_code == 200:
        print("Successfully redeemed WELCOME bundle!")
        return resp.json().get("data")
    elif resp.status_code == 409:
        print("WELCOME bundle already redeemed or inventory full.")
        return None
    else:
        print(f"Redeem returned status: {resp.status_code}, detail: {resp.text}")
        return None