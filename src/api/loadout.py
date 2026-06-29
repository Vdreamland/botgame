from typing import List, Dict, Any, Optional
import uuid
from src.api.client import BaseHttpClient
from src.utils.logger import logger

class LobbyLoadoutManager(BaseHttpClient):
    """Manages out-of-game lobby inventory and loadout configurations with robust type checks."""
    
    def __init__(self, api_key: str):
        super().__init__(api_key)

    async def get_loadout(self) -> Dict[str, Any]:
        """Fetch current equipped loadout."""
        try:
            res = await self.get("/api/loadout")
            if res.get("success"):
                data = res.get("data", {})
                return data if isinstance(data, dict) else {}
            return {}
        except Exception as e:
            logger.error(f"Failed to fetch lobby loadout: {str(e)}")
            return {}

    async def get_relics_inventory(self) -> List[Dict[str, Any]]:
        """Fetch owned relics from inventory with robust dictionary/list checks."""
        try:
            res = await self.get("/api/inventory/relics")
            if res.get("success"):
                data = res.get("data", {})
                if isinstance(data, dict):
                    return data.get("relics", [])
                elif isinstance(data, list):
                    return data
            return []
        except Exception as e:
            logger.error(f"Failed to fetch relics inventory: {str(e)}")
            return []

    async def get_packs_inventory(self) -> List[Dict[str, Any]]:
        """Fetch owned packs from inventory with robust dictionary/list checks."""
        try:
            res = await self.get("/api/inventory/packs")
            if res.get("success"):
                data = res.get("data", {})
                if isinstance(data, dict):
                    return data.get("packs", [])
                elif isinstance(data, list):
                    return data
            return []
        except Exception as e:
            logger.error(f"Failed to fetch packs inventory: {str(e)}")
            return []

    async def equip_pack(self, pack_instance_id: str) -> bool:
        """Equip selected active pack."""
        try:
            headers = self._get_headers()
            headers["Idempotency-Key"] = str(uuid.uuid4())
            
            res = await self.put(
                path="/api/loadout/pack",
                json_data={"packInstanceId": pack_instance_id},
                headers_override=headers
            )
            return res.get("success", False)
        except Exception as e:
            logger.error(f"Failed to equip active pack: {str(e)}")
            return False

    async def equip_relic(self, slot_index: int, relic_instance_id: str) -> bool:
        """Equip selected relic into slot index."""
        try:
            headers = self._get_headers()
            headers["Idempotency-Key"] = str(uuid.uuid4())
            
            res = await self.put(
                path=f"/api/loadout/slot/{slot_index}",
                json_data={"relicInstanceId": relic_instance_id},
                headers_override=headers
            )
            return res.get("success", False)
        except Exception as e:
            logger.error(f"Failed to equip relic in slot {slot_index}: {str(e)}") [2]
            return False