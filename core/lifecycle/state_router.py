# -*- coding: utf-8 -*-
"""
ClawRoyale State Router.
Routes the agent's execution phase based on GET /accounts/me.
"""

from typing import Dict, Any, Tuple
from utils.logger import AgentLogger
from core.network.api_client import APIClient, APIClientError


class StateRouter:
    def __init__(self, agent_name: str, api_client: APIClient):
        self.agent_name = agent_name
        self.api_client = api_client
        self.logger = AgentLogger.get_logger(agent_name)

    async def route_current_state(self) -> Tuple[str, Dict[str, Any]]:
        """
        Queries /accounts/me and maps the response to an authoritative state string.
        Returns: Tuple[state_name, parsed_account_data]
        States mapped:
        - NO_ACCOUNT: No valid API Key or Whitelist required.
        - IN_GAME: Active game found in progress (needs WS reconnection bypass).
        - READY_PAID: Configured loadout with available Moltz ready for paid game.
        - READY_FREE: Base state or fallback state for free room matchmaking.
        - ERROR: Connection timeout or system exceptions.
        """
        try:
            self.logger.info("Routing current agent state via /accounts/me API...")
            account_data = await self.api_client.get_account_me()
            
            data = account_data.get("data", {})
            current_games = data.get("currentGames", [])
            readiness = data.get("readiness", {})

            # 1. Cek Apakah Sedang Berada di Tengah Game (Bypass Reconnection)
            if current_games:
                active_game = current_games[0]
                self.logger.warning(
                    f"Active game session detected (Match ID: {active_game.get('matchId')}). "
                    f"Routing to IN_GAME state for direct WebSocket connection."
                )
                return "IN_GAME", account_data

            # 2. Cek Ketersediaan Kamar Berbayar (READY_PAID)
            if readiness.get("paidReady", False):
                self.logger.info("Paid room checks passed. Agent is routed to READY_PAID.")
                return "READY_PAID", account_data

            # 3. Default: READY_FREE
            self.logger.info("Agent is configured and routed to READY_FREE state.")
            return "READY_FREE", account_data

        except APIClientError as ace:
            # 4. Deteksi Jika Akun Tidak Ditemukan atau Kredensial Salah
            self.logger.error(f"API Routing exception: {str(ace)}")
            # Umumnya error 401 atau 404 menandakan akun belum terdaftar
            if "401" in str(ace) or "404" in str(ace) or "Unauthorized" in str(ace):
                self.logger.warning("Routing to NO_ACCOUNT state. Registration is required.")
                return "NO_ACCOUNT", {}
            return "ERROR", {}
            
        except Exception as e:
            self.logger.critical(f"Unexpected crash in StateRouter: {str(e)}")
            return "ERROR", {}