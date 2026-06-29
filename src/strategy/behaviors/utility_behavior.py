from typing import Dict, Any

class UtilityBehavior:
    
    @staticmethod
    def build_move_action(region_id: str, thought: str = "") -> Dict[str, Any]:
        payload = {
            "type": "action",
            "data": {
                "type": "move",
                "regionId": region_id
            }
        }
        if thought:
            payload["thought"] = thought[:700]
        return payload

    @staticmethod
    def build_rest_action(thought: str = "") -> Dict[str, Any]:
        payload = {
            "type": "action",
            "data": {
                "type": "rest"
            }
        }
        if thought:
            payload["thought"] = thought[:700]
        return payload

    @staticmethod
    def build_use_item_action(item_id: str, thought: str = "") -> Dict[str, Any]:
        payload = {
            "type": "action",
            "data": {
                "type": "use_item",
                "itemId": item_id
            }
        }
        if thought:
            payload["thought"] = thought[:700]
        return payload

    @staticmethod
    def build_interact_action(thought: str = "") -> Dict[str, Any]:
        payload = {
            "type": "action",
            "data": {
                "type": "interact"
            }
        }
        if thought:
            payload["thought"] = thought[:700]
        return payload

    @staticmethod
    def build_pickup_action(item_id: str, thought: str = "") -> Dict[str, Any]:
        payload = {
            "type": "action",
            "data": {
                "type": "pickup",
                "itemId": item_id
            }
        }
        if thought:
            payload["thought"] = thought[:700]
        return payload

    @staticmethod
    def build_equip_action(item_id: str, thought: str = "") -> Dict[str, Any]:
        payload = {
            "type": "action",
            "data": {
                "type": "equip",
                "itemId": item_id
            }
        }
        if thought:
            payload["thought"] = thought[:700]
        return payload