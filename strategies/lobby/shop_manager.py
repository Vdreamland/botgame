# -*- coding: utf-8 -*-
"""
ClawRoyale Lobby Shop Manager.
This module has been stripped of all active purchasing and auto-spending logic
to guarantee 100% security for the operator's Moltz tokens.
"""

from utils.logger import AgentLogger
from core.network.api_client import APIClient


class LobbyShopManager:
    def __init__(self, agent_name: str, api_client: APIClient):
        self.agent_name = agent_name
        self.api_client = api_client
        self.logger = AgentLogger.get_logger(agent_name)

    def log_safety_status(self) -> None:
        """
        Logs the safety status of the lobby shop manager.
        Ensures the operator knows that spending is physically blocked.
        """
        self.logger.info("Lobby Shop Security Check: Automated Moltz spending functions are completely removed.")