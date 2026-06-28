# -*- coding: utf-8 -*-
"""
ClawRoyale State Router.
Routes the agent's execution phase based on GET /accounts/me [1].
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
        """
        try:
            self.logger.info("Routing current agent state via /accounts/me API...")
            account_data = await self.api_client.get_account_me()
            
            data = account_data.get("data", {})
            current_games = data.get("currentGames", [])
            readiness = data.get("readiness", {})

            # Cek keaktifan game di server secara instan [1]
            if current_games:
                active_game = current_games[0]
                self.logger.warning(
                    f"Active game session detected (Match ID: {active_game.get('matchId')}). "
                    f"Routing directly to IN_GAME state."
                )
                return "IN_GAME", account_data

            if readiness.get("paidReady", False):
                self.logger.info("Paid room checks passed. Agent is routed to READY_PAID.")
                return "READY_PAID", account_data

            self.logger.info("Agent is configured and routed to READY_FREE state.")
            return "READY_FREE", account_data

        except APIClientError as ace:
            self.logger.error(f"API Routing exception: {str(ace)}")
            if "401" in str(ace) or "404" in str(ace) or "Unauthorized" in str(ace):
                self.logger.warning("Routing to NO_ACCOUNT state. Registration is required.")
                return "NO_ACCOUNT", {}
            return "ERROR", {}
            
        except Exception as e:
            self.logger.critical(f"Unexpected crash in StateRouter: {str(e)}")
            return "ERROR", {}