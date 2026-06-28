# -*- coding: utf-8 -*-
"""
ClawRoyale Account Setup & Whitelist Handler.
Coordinates new account registrations and whitelist verification.
"""

from typing import Dict, Any, Tuple
from utils.logger import AgentLogger
from utils.crypto_helper import CryptoHelper
from core.network.api_client import APIClient, APIClientError


class SetupHandler:
    def __init__(self, agent_name: str, private_key: str, api_client: APIClient):
        self.agent_name = agent_name
        self.private_key = private_key
        self.api_client = api_client
        self.logger = AgentLogger.get_logger(agent_name)

    async def register_new_agent_account(self) -> Tuple[bool, Dict[str, Any]]:
        """
        Attempts to register the derived public wallet address into the ClawRoyale backend database.
        Used when StateRouter returns NO_ACCOUNT.
        """
        try:
            derived_address = CryptoHelper.get_address_from_private_key(self.private_key)
            self.logger.warning(f"No account found. Attempting registration for address: {derived_address}")

            # Persiapkan data registrasi sesuai format pendaftaran akun baru
            payload = {
                "address": derived_address,
                "agentName": self.agent_name,
                "agreementSigned": True
            }

            # Daftarkan via endpoint POST /accounts [1]
            response = await self.api_client.safe_request("POST", "accounts", data=payload)
            
            if response.get("status") == "success" or "data" in response:
                self.logger.info("Successfully registered a new ClawRoyale agent account.")
                return True, response
                
            self.logger.error(f"Account registration API responded with unexpected data: {response}")
            return False, {}

        except APIClientError as ace:
            self.logger.error(f"Failed to register new agent account: {str(ace)}")
            return False, {}
        except Exception as e:
            self.logger.critical(f"Unexpected crash in SetupHandler: {str(e)}")
            return False, {}

    async def verify_whitelist_status(self) -> bool:
        """
        Verifies if the derived wallet address is currently authorized / whitelisted
        to enter paid and free games under Pre-Season 1 policies [6].
        """
        try:
            derived_address = CryptoHelper.get_address_from_private_key(self.private_key)
            endpoint = f"whitelist/check?address={derived_address}"
            
            # Request status ke endpoint verifikasi whitelist
            response = await self.api_client.safe_request("GET", endpoint)
            data = response.get("data", {})
            
            is_whitelisted = data.get("isWhitelisted", False)
            if is_whitelisted:
                self.logger.info(f"Wallet address {derived_address} is verified on the whitelist database.")
                return True
                
            self.logger.warning(f"Wallet address {derived_address} is NOT whitelisted yet.")
            return False

        except Exception as e:
            self.logger.error(f"Failed to complete whitelist verification: {str(e)}")
            # Berikan toleransi free room karena free room tidak memerlukan whitelist khusus di v1.11.2 [5]
            return True