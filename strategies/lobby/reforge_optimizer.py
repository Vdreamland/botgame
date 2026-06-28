# -*- coding: utf-8 -*-
"""
ClawRoyale Lobby Reforge Optimizer.
Coordinates asynchronous relic reforge sessions to roll optimal stats.
"""

from typing import Dict, Any, List, Optional
from utils.logger import AgentLogger
from core.network.api_client import APIClient, APIClientError


class RelicReforgeOptimizer:
    def __init__(self, agent_name: str, api_client: APIClient):
        self.agent_name = agent_name
        self.api_client = api_client
        self.logger = AgentLogger.get_logger(agent_name)

    async def optimize_relic_affixes(self, relic_id: str, 
                                     target_affixes: List[str], 
                                     reforge_token: str, 
                                     max_attempts: int = 5) -> bool:
        """
        Sends requests to POST /reforge to roll optimal stats on a targeted relic.
        Stops immediately once any target affix (e.g., 'atk_boost_percentage') is rolled.
        :param relic_id: Unique database ID of the relic in inventory.
        :param target_affixes: List of desired affix strings (e.g. ['atk_boost_5', 'def_boost_5']).
        :param reforge_token: Authorization session token acquired from AgentTokenRegistrar.
        :param max_attempts: Limit of reforge stones we are willing to consume.
        """
        if not reforge_token:
            self.logger.error("Reforge session blocked: Missing active session reforge token.")
            return False

        self.logger.info(f"Initiating auto-reforge optimization for relic ID: {relic_id}...")
        
        # Header khusus menyertakan Token Forge [4]
        headers_override = {
            "Authorization-Forge": f"Bearer {reforge_token}"
        }

        attempts = 0
        while attempts < max_attempts:
            attempts += 1
            self.logger.info(f"Reforge attempt {attempts}/{max_attempts} for relic {relic_id}...")

            payload = {
                "relicId": relic_id,
                "consumeStones": 1
            }

            try:
                # Kirim request reforge ke API [1]
                response = await self.api_client.safe_request(
                    method="POST",
                    endpoint="reforge",
                    data=payload,
                    headers_override=headers_override
                )

                data = response.get("data", {})
                current_affixes = data.get("currentAffixes", [])
                
                self.logger.info(f"Rolled affixes on attempt {attempts}: {current_affixes}")

                # Cek apakah hasil roll saat ini sudah mengandung salah satu target affix kita
                matched = False
                for rolled in current_affixes:
                    if rolled in target_affixes:
                        matched = True
                        break

                if matched:
                    self.logger.info("Reforge target achieved! Optimal stats successfully locked.")
                    return True

            except APIClientError as ace:
                self.logger.error(f"Reforge operation aborted on attempt {attempts}: {str(ace)}")
                return False
            except Exception as e:
                self.logger.critical(f"Unexpected crash in reforge optimizer loop: {str(e)}")
                return False

        self.logger.warning(f"Reforge completed. Reached max limit of {max_attempts} attempts without rolling exact targets.")
        return False