from typing import List, Dict, Any, Optional
import uuid
from src.api.client import BaseHttpClient
from src.utils.logger import logger

class LobbyLoadoutManager(BaseHttpClient):
    """Manages out-of-game lobby inventory and loadout configurations with verified key mapping."""
    
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
        """Fetch owned relics from inventory scanning all potential fallback pagination keys."""
        try:
            res = await self.get("/api/inventory/relics")
            if res.get("success"):
                data = res.get("data", {})
                if isinstance(data, dict):
                    items_list = data.get("relics") or data.get("entries") or data.get("items") or data.get("data")
                    return items_list if isinstance(items_list, list) else []
                elif isinstance(data, list):
                    return data
            return []
        except Exception as e:
            logger.error(f"Failed to fetch relics inventory: {str(e)}")
            return []

    async def get_packs_inventory(self) -> List[Dict[str, Any]]:
        """Fetch owned packs from inventory scanning all potential fallback pagination keys."""
        try:
            res = await self.get("/api/inventory/packs")
            if res.get("success"):
                data = res.get("data", {})
                if isinstance(data, dict):
                    items_list = data.get("packs") or data.get("entries") or data.get("items") or data.get("data")
                    return items_list if isinstance(items_list, list) else []
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

    async def equip_subpack(self, pack_instance_id: str) -> bool:
        """Equip selected active sub pack with robust, exception-safe fallback routing."""
        headers = self._get_headers()
        headers["Idempotency-Key"] = str(uuid.uuid4())
        
        # Coba Rute 1: /api/loadout/subpack
        try:
            res = await self.put(
                path="/api/loadout/subpack",
                json_data={"packInstanceId": pack_instance_id},
                headers_override=headers
            )
            if res.get("success"):
                return True
        except Exception:
            pass

        # Coba Rute 2: /api/loadout/sub-pack
        try:
            res_alt = await self.put(
                path="/api/loadout/sub-pack",
                json_data={"packInstanceId": pack_instance_id},
                headers_override=headers
            )
            if res_alt.get("success"):
                return True
        except Exception:
            pass

        # Coba Rute 3: /api/loadout/pack/sub
        try:
            res_three = await self.put(
                path="/api/loadout/pack/sub",
                json_data={"packInstanceId": pack_instance_id},
                headers_override=headers
            )
            if res_three.get("success"):
                return True
        except Exception:
            pass

        # Coba Rute 4: /api/loadout/sub
        try:
            res_four = await self.put(
                path="/api/loadout/sub",
                json_data={"packInstanceId": pack_instance_id},
                headers_override=headers
            )
            if res_four.get("success"):
                return True
        except Exception:
            pass
            
        logger.error(f"All sub-pack equip endpoints failed (404/409). Check skill.md or server connection.")
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
            logger.error(f"Failed to equip relic in slot {slot_index}: {str(e)}")
            return False