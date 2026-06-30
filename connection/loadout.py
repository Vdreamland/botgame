# connection/loadout.py

import aiohttp
import uuid
from connection.api_endpoints import (
    LOADOUT_URL,
    LOADOUT_PACK_URL,
    LOADOUT_SUB_URL,
    LOADOUT_SLOT_URL,
    INVENTORY_RELICS_URL,
    INVENTORY_PACKS_URL,
    BASE_URL
)

class ClawRoyaleLoadoutClient:
    def __init__(self, session: aiohttp.ClientSession):
        self.session = session

    def _get_headers(self, api_key: str, version: str, is_mutation: bool = False) -> dict:
        headers = {
            "X-API-Key": api_key,
            "X-Version": version,
            "Content-Type": "application/json"
        }
        if is_mutation:
            headers["Idempotency-Key"] = str(uuid.uuid4())
        return headers

    async def get_loadout(self, api_key: str, version: str) -> dict:
        headers = self._get_headers(api_key, version)
        try:
            async with self.session.get(LOADOUT_URL, headers=headers) as r:
                res = await r.json()
                if isinstance(res, dict) and res.get("success"):
                    return res["data"]
                raise Exception(f"HTTP {r.status}")
        except Exception as e:
            raise Exception(f"Failed to fetch loadout: {str(e)}")

    async def set_active_pack(self, api_key: str, version: str, pack_instance_id: str) -> dict:
        headers = self._get_headers(api_key, version, is_mutation=True)
        payload = {"packInstanceId": pack_instance_id}
        try:
            async with self.session.put(LOADOUT_PACK_URL, headers=headers, json=payload) as r:
                res = await r.json()
                if isinstance(res, dict) and res.get("success"):
                    return res["data"]
                raise Exception(f"HTTP {r.status}")
        except Exception as e:
            raise Exception(f"Failed to set active pack: {str(e)}")

    async def unset_active_pack(self, api_key: str, version: str) -> dict:
        headers = self._get_headers(api_key, version, is_mutation=True)
        try:
            async with self.session.delete(LOADOUT_PACK_URL, headers=headers) as r:
                res = await r.json()
                if r.status == 200 and res.get("success"):
                    return res.get("data", {})
                raise Exception(f"HTTP {r.status}")
        except Exception as e:
            raise Exception(f"Failed to unset active pack: {str(e)}")

    async def set_sub_pack(self, api_key: str, version: str, pack_instance_id: str) -> bool:
        headers = self._get_headers(api_key, version, is_mutation=True)
        payload = {"packInstanceId": pack_instance_id}
        
        # Route 1: /api/loadout/subpack
        try:
            url = f"{BASE_URL}/loadout/subpack"
            async with self.session.put(url, headers=headers, json=payload) as r:
                res = await r.json()
                if res.get("success"):
                    return True
        except Exception:
            pass

        # Route 2: /api/loadout/sub-pack
        try:
            url = f"{BASE_URL}/loadout/sub-pack"
            async with self.session.put(url, headers=headers, json=payload) as r:
                res = await r.json()
                if res.get("success"):
                    return True
        except Exception:
            pass

        # Route 3: /api/loadout/pack/sub
        try:
            url = f"{BASE_URL}/loadout/pack/sub"
            async with self.session.put(url, headers=headers, json=payload) as r:
                res = await r.json()
                if res.get("success"):
                    return True
        except Exception:
            pass

        # Route 4: /api/loadout/sub
        try:
            url = f"{BASE_URL}/loadout/sub"
            async with self.session.put(url, headers=headers, json=payload) as r:
                res = await r.json()
                if res.get("success"):
                    return True
        except Exception:
            pass

        raise Exception("All sub-pack endpoints failed.")

    async def unset_sub_pack(self, api_key: str, version: str) -> dict:
        headers = self._get_headers(api_key, version, is_mutation=True)
        try:
            async with self.session.delete(LOADOUT_SUB_URL, headers=headers) as r:
                res = await r.json()
                if r.status == 200 and res.get("success"):
                    return res.get("data", {})
                raise Exception(f"HTTP {r.status}")
        except Exception as e:
            raise Exception(f"Failed to unset sub pack: {str(e)}")

    async def equip_relic(self, api_key: str, version: str, slot_index: int, relic_instance_id: str) -> dict:
        headers = self._get_headers(api_key, version, is_mutation=True)
        url = f"{LOADOUT_SLOT_URL}/{slot_index}"
        payload = {"relicInstanceId": relic_instance_id}
        try:
            async with self.session.put(url, headers=headers, json=payload) as r:
                res = await r.json()
                if r.status == 200 and res.get("success"):
                    return res["data"]
                raise Exception(f"HTTP {r.status}")
        except Exception as e:
            raise Exception(f"Failed to equip relic: {str(e)}")

    async def unequip_relic(self, api_key: str, version: str, slot_index: int) -> dict:
        headers = self._get_headers(api_key, version, is_mutation=True)
        url = f"{LOADOUT_SLOT_URL}/{slot_index}"
        try:
            async with self.session.delete(url, headers=headers) as r:
                res = await r.json()
                if r.status == 200 and res.get("success"):
                    return res.get("data", {})
                raise Exception(f"HTTP {r.status}")
        except Exception as e:
            raise Exception(f"Failed to unequip relic: {str(e)}")

    async def get_relics_inventory(self, api_key: str, version: str, limit: int = 15, after_id: str = "") -> list:
        headers = self._get_headers(api_key, version)
        params = {"limit": limit}
        if after_id:
            params["afterId"] = after_id
        try:
            async with self.session.get(INVENTORY_RELICS_URL, headers=headers, params=params) as r:
                res = await r.json()
                if isinstance(res, dict) and res.get("success"):
                    data = res.get("data", {})
                    if isinstance(data, dict):
                        items_list = data.get("relics") or data.get("entries") or data.get("items") or data.get("data")
                        return items_list if isinstance(items_list, list) else []
                    elif isinstance(data, list):
                        return data
                elif isinstance(res, list):
                    return res
                return []
        except Exception as e:
            raise Exception(f"Failed to fetch relics inventory: {str(e)}")

    async def get_packs_inventory(self, api_key: str, version: str, limit: int = 5, after_id: str = "") -> list:
        headers = self._get_headers(api_key, version)
        params = {"limit": limit}
        if after_id:
            params["afterId"] = after_id
        try:
            async with self.session.get(INVENTORY_PACKS_URL, headers=headers, params=params) as r:
                res = await r.json()
                if isinstance(res, dict) and res.get("success"):
                    data = res.get("data", {})
                    if isinstance(data, dict):
                        items_list = data.get("packs") or data.get("entries") or data.get("items") or data.get("data")
                        return items_list if isinstance(items_list, list) else []
                    elif isinstance(data, list):
                        return data
                elif isinstance(res, list):
                    return res
                return []
        except Exception as e:
            raise Exception(f"Failed to fetch packs inventory: {str(e)}")