import asyncio
import aiohttp
import logging
from utils.logger import logger as custom_logger
from logs.quest_reward_log import (
    log_redeem_attempt,
    log_redeem_success,
    log_redeem_failed,
    log_weekly_check,
    log_weekly_claim_attempt,
    log_weekly_claim_success,
    log_weekly_claim_failed
)

logger = logging.getLogger("APIClient")

class ClawRoyaleAPI:
    BASE_URL = "https://cdn.clawroyale.ai/api"

    def __init__(self, api_key: str, api_version: str = "1.12.0"):
        self.api_key = api_key
        self.api_version = api_version
        self.headers = {
            "X-API-Key": self.api_key,
            "X-Version": self.api_version,
            "Content-Type": "application/json"
        }

    def _build_url(self, path: str) -> str:
        if path.startswith("/api/"):
            path = path[4:]
        if not path.startswith("/"):
            path = "/" + path
        return f"{self.BASE_URL}{path}"

    async def _request(self, method: str, path: str, json_data: dict = None, retries: int = 3) -> dict:
        url = self._build_url(path)
        async with aiohttp.ClientSession(headers=self.headers) as session:
            for attempt in range(retries):
                try:
                    async with session.request(method, url, json=json_data) as response:
                        if response.status == 429:
                            retry_after = int(response.headers.get("Retry-After", 5))
                            await asyncio.sleep(retry_after)
                            continue
                        
                        if response.status not in [200, 201]:
                            error_text = await response.text()
                            return {"success": False, "status": response.status, "error": error_text}
                        
                        return await response.json()
                except Exception as e:
                    if attempt < retries - 1:
                        await asyncio.sleep(2)
                    else:
                        return {"success": False, "error": str(e)}
            return {"success": False, "error": "Max retries exceeded"}

    async def get_my_profile(self) -> dict:
        return await self._request("GET", "/accounts/me")

    async def get_weekly_tracks(self) -> dict:
        return await self._request("GET", "/accounts/me/weekly")

    async def claim_weekly_reward(self, track_index: int) -> dict:
        payload = {"trackIndex": track_index}
        return await self._request("POST", "/api/weekly/claim", payload)

    async def get_preseason_leaderboard(self) -> dict:
        return await self._request("GET", "/api/preseason1/leaderboard")

    async def redeem_code(self, code: str = "WELCOME") -> dict:
        payload = {"code": code}
        return await self._request("POST", "/api/redeem", payload)

    async def get_loadout(self) -> dict:
        return await self._request("GET", "/api/loadout")

    async def equip_pack(self, pack_id: str, slot: str) -> dict:
        payload = {"id": pack_id, "slot": slot}
        return await self._request("PUT", "/api/loadout/pack", payload)

    async def remove_pack(self, slot: str) -> dict:
        payload = {"slot": slot}
        return await self._request("DELETE", "/api/loadout/pack", payload)

    async def equip_relic(self, relic_id: str, slot_index: int) -> dict:
        payload = {"id": relic_id}
        return await self._request("PUT", f"/api/loadout/slot/{slot_index}", payload)

    async def remove_relic(self, slot_index: int) -> dict:
        return await self._request("DELETE", f"/api/loadout/slot/{slot_index}")

    async def get_inventory_relics(self) -> dict:
        return await self._request("GET", "/api/inventory/relics")

    async def delete_inventory_relic(self, relic_id: str) -> dict:
        return await self._request("DELETE", f"/api/inventory/relics/{relic_id}")

    async def get_inventory_packs(self) -> dict:
        return await self._request("GET", "/api/inventory/packs")

    async def delete_inventory_pack(self, pack_id: str) -> dict:
        return await self._request("DELETE", f"/api/inventory/packs/{pack_id}")

    async def reforge_relic(self, relic_id: str, material_id: str) -> dict:
        payload = {
            "relicId": relic_id,
            "materialId": material_id
        }
        return await self._request("POST", "/api/reforge", payload)

    async def get_shop_listings(self) -> dict:
        return await self._request("GET", "/api/shop/listings")

    async def purchase_item(self, listing_id: str, quantity: int = 1) -> dict:
        payload = {
            "listingId": listing_id,
            "quantity": quantity
        }
        return await self._request("POST", "/api/shop/purchase", payload)

    async def create_account(self, owner_wallet: str, sc_wallet: str, agent_wallet: str) -> dict:
        payload = {
            "ownerWallet": owner_wallet,
            "scWallet": sc_wallet,
            "agentWallet": agent_wallet
        }
        return await self._request("POST", "/accounts", payload)

    async def update_agent_wallet(self, agent_wallet: str) -> dict:
        payload = {"agentWallet": agent_wallet}
        return await self._request("PUT", "/accounts/wallet", payload)

    async def auto_claim_rewards(self):
        log_redeem_attempt("WELCOME")
        redeem_res = await self.redeem_code("WELCOME")
        if redeem_res.get("success"):
            log_redeem_success("WELCOME")
        else:
            error_text = redeem_res.get("error") or f"status {redeem_res.get('status')}"
            log_redeem_failed("WELCOME", error_text)

        log_weekly_check()
        weekly_res = await self.get_weekly_tracks()
        if weekly_res.get("success"):
            data = weekly_res.get("data", {})
            tracks = data.get("tracks", [])
            claimed_any = False
            for track in tracks:
                if isinstance(track, dict) and track.get("opened") is True and track.get("claimed") is False:
                    track_index = track.get("trackIndex")
                    if track_index is not None:
                        log_weekly_claim_attempt(track_index)
                        claim_res = await self.claim_weekly_reward(track_index)
                        if claim_res.get("success"):
                            log_weekly_claim_success(track_index)
                            claimed_any = True
                            break
                        else:
                            claim_err = claim_res.get("error") or f"status {claim_res.get('status')}"
                            log_weekly_claim_failed(track_index, claim_err)
            if not claimed_any:
                custom_logger.info("[*] No claimable weekly reward tracks found.")
        else:
            custom_logger.warning(f"[WARN] Failed to retrieve weekly tracks: {weekly_res.get('error')}")