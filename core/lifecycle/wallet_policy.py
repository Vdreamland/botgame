# -*- coding: utf-8 -*-
"""
ClawRoyale Smart Contract Wallet Policy Manager.
Enforces the 1:1 wallet policy and prevents 'NOT_PRIMARY_AGENT' errors.
"""

from typing import Dict, Any
from utils.logger import AgentLogger


class WalletPolicyManager:
    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        self.logger = AgentLogger.get_logger(agent_name)

    def validate_primary_agent_status(self, account_data: Dict[str, Any]) -> bool:
        """
        Validates whether this agent instance is allowed to enter matchmaking queues.
        Inspects readiness missing codes for 'NOT_PRIMARY_AGENT'.
        """
        data = account_data.get("data", {})
        readiness = data.get("readiness", {})
        
        # Cek status kelayakan kamar gratis maupun berbayar
        free_room_status = readiness.get("freeRoom", {})
        paid_room_status = readiness.get("paidRoom", {})

        # Pindai kode error missing pada masing-masing tipe kamar
        missing_free = free_room_status.get("missing", [])
        missing_paid = paid_room_status.get("missing", [])

        # Cari indikasi kesalahan NOT_PRIMARY_AGENT
        for item in missing_free + missing_paid:
            if isinstance(item, dict) and item.get("code") == "NOT_PRIMARY_AGENT":
                self.logger.error(
                    f"Validation failed: This agent is NOT the primary agent for the linked wallet. "
                    f"Guide URL reference: {item.get('guide')}"
                )
                return False
            elif str(item) == "NOT_PRIMARY_AGENT":
                self.logger.error("Validation failed: NOT_PRIMARY_AGENT detected in readiness missing items.")
                return False

        self.logger.info("Wallet policy check passed. Agent is recognized as the primary agent.")
        return True

    def check_active_concurrency_limit(self, account_data: Dict[str, Any], target_room: str) -> bool:
        """
        Verifies that the wallet does not violate active concurrent play rules.
        (Max 1 active free game + 1 active paid game globally per wallet).
        """
        data = account_data.get("data", {})
        current_games = data.get("currentGames", [])

        if not current_games:
            return True

        for game in current_games:
            game_type = game.get("entryType")
            if game_type == target_room:
                self.logger.warning(
                    f"Concurrency block: Wallet already has an active '{target_room}' game running. "
                    f"To prevent duplicate session errors, wait until the active game ends."
                )
                return False

        return True