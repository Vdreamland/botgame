# -*- coding: utf-8 -*-
"""
ClawRoyale Teammate Cooperative Coordinator.
Handles target sharing, loot coordination, and backup requests using free message actions [11, 13].
"""

import json
from typing import Dict, Any, Tuple, Optional
from utils.logger import AgentLogger
from core.state.game_state import GameState
from core.state.team_registry import TeamRegistry
from actions.action_dispatcher import ActionDispatcher


class TeamCoordinator:
    def __init__(self, agent_name: str, game_state: GameState, dispatcher: ActionDispatcher):
        self.agent_name = agent_name
        self.game_state = game_state
        self.dispatcher = dispatcher
        
        self.logger = AgentLogger.get_logger(agent_name)
        self.team_registry = TeamRegistry()

    async def broadcast_target_position(self, target_id: str, q: int, r: int) -> None:
        """
        Broadcasts the coordinate of a confirmed hostile target to all allied bots [13].
        Helps teammates coordinate focus-fire attacks [11].
        """
        # Format payload pesan koordinasi dalam bentuk JSON string
        info = {
            "msg_type": "FOCUS_FIRE",
            "target_id": target_id,
            "q": q,
            "r": r,
            "sender": self.agent_name
        }
        raw_message = json.dumps(info)
        self.logger.info(f"Broadcasting focus-fire coordinate target on hostile ID: {target_id} [13].")
        await self.dispatcher.execute_broadcast(raw_message)

    async def whisper_backup_request(self, nearest_ally_id: str, enemy_id: str, q: int, r: int) -> None:
        """
        Sends a private whisper to the nearest allied bot to request urgent assistance [13].
        """
        info = {
            "msg_type": "REQUEST_BACKUP",
            "enemy_id": enemy_id,
            "q": q,
            "r": r,
            "sender": self.agent_name
        }
        raw_message = json.dumps(info)
        self.logger.warning(f"Whispering backup request to ally ID: {nearest_ally_id} [13].")
        await self.dispatcher.execute_whisper(nearest_ally_id, raw_message)

    async def coordinate_looting_target(self, ground_item_id: str, q: int, r: int) -> None:
        """
        Broadcasts item coordinate we are currently heading towards, preventing
        other allied bots from wasting EP heading to the same item [13].
        """
        info = {
            "msg_type": "CLAIM_LOOT",
            "item_id": ground_item_id,
            "q": q,
            "r": r,
            "sender": self.agent_name
        }
        raw_message = json.dumps(info)
        self.logger.info(f"Broadcasting loot claim on item ID: {ground_item_id} at ({q}, {r}) [13].")
        await self.dispatcher.execute_broadcast(raw_message)

    async def parse_and_process_incoming_team_msg(self, sender_name: str, raw_content: str) -> Optional[Dict[str, Any]]:
        """
        Parses whispered or broadcasted coordination messages from other allied bots.
        Ensures our bot reacts accordingly (e.g. shifts pathfinder to backup location).
        """
        # Verifikasi bahwa pengirim pesan memang kawan kita, bukan musuh yang menyamar
        if not self.team_registry.is_ally(player_id="", name=sender_name):
            return None

        try:
            data = json.loads(raw_content)
            msg_type = data.get("msg_type")

            if msg_type == "FOCUS_FIRE":
                self.logger.warning(
                    f"Team Signal: Focus-fire request received from {sender_name} "
                    f"on target {data.get('target_id')} at ({data.get('q')}, {data.get('r')}) [11]."
                )
                return {"action": "SET_HUNT_TARGET", "target_id": data.get("target_id"), "coords": (data.get("q"), data.get("r"))}

            elif msg_type == "REQUEST_BACKUP":
                self.logger.warning(
                    f"Team Signal: Ally {sender_name} is under attack at ({data.get('q')}, {data.get('r')}). "
                    f"Rerouting to provide backup assistance."
                )
                return {"action": "PROVIDE_BACKUP", "coords": (data.get("q"), data.get("r"))}

            elif msg_type == "CLAIM_LOOT":
                self.logger.info(f"Team Signal: Ally {sender_name} claimed ground item ID: {data.get('item_id')}. Skipping.")
                # Kembalikan koordinat item agar diblacklist sementara dari radar pencarian ground_item_scanner
                return {"action": "BLACKLIST_ITEM_COORDS", "coords": (data.get("q"), data.get("r"))}

        except Exception as e:
            self.logger.error(f"Failed to parse incoming team cooperative message: {str(e)}")
            
        return None