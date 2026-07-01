# connection/http_client.py

import aiohttp
import json
from connection.api_endpoints import VERSION_URL, ACCOUNTS_ME_URL

class ClawRoyaleHTTPClient:
    def __init__(self, session: aiohttp.ClientSession):
        self.session = session

    async def get_current_version(self) -> str:
        try:
            async with self.session.get(VERSION_URL) as response:
                text_response = await response.text()
                
                if response.status == 200:
                    cleaned_text = text_response.strip()
                    
                    try:
                        res_json = json.loads(cleaned_text)
                        if isinstance(res_json, dict):
                            if res_json.get("success"):
                                data = res_json.get("data")
                                if isinstance(data, dict):
                                    return str(data.get("version", ""))
                                elif isinstance(data, str):
                                    return data
                            
                            if "version" in res_json:
                                return str(res_json["version"])
                    except json.JSONDecodeError:
                        if cleaned_text:
                            return cleaned_text
                    
                    raise Exception(f"Unknown format: {text_response[:100]}")
                raise Exception(f"HTTP {response.status}")
        except Exception as e:
            raise Exception(f"Failed to fetch game version: {str(e)}")

    async def get_account_me(self, api_key: str, version: str) -> dict:
        headers = {
            "X-API-Key": api_key,
            "X-Version": version,
            "Content-Type": "application/json"
        }
        try:
            async with self.session.get(ACCOUNTS_ME_URL, headers=headers) as response:
                res_json = await response.json()
                if response.status == 200 and res_json.get("success"):
                    return res_json["data"]
                elif response.status == 426:
                    raise Exception("VERSION_MISMATCH - Please update your app.")
                else:
                    error_msg = res_json.get("error", {}).get("message", "Unknown error")
                    raise Exception(f"{error_msg} (HTTP {response.status})")
        except Exception as e:
            raise Exception(f"Account check failed: {str(e)}")

    async def get_room_name(self, game_id: str, api_key: str, version: str) -> str:
        """Pusat logika HTTP request untuk mengambil nama game/room secara dinamis"""
        url = f"https://cdn.clawroyale.ai/api/games/{game_id}"
        headers = {
            "X-API-Key": api_key,
            "X-Version": version
        }
        try:
            async with self.session.get(url, headers=headers) as response:
                if response.status == 200:
                    res = await response.json()
                    if isinstance(res, dict) and res.get("success"):
                        data = res.get("data", {})
                        name = data.get("name") or data.get("title")
                        if name:
                            return name
        except Exception:
            pass
        return game_id[:8]