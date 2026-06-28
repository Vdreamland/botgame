# -*- coding: utf-8 -*-
"""
ClawRoyale Agent Forge Token Registrar.
Authenticates the agent session for Pre-Season 1 operations using signed messages.
"""

import time
from utils.logger import AgentLogger
from utils.crypto_helper import CryptoHelper
from core.network.api_client import APIClient, APIClientError


class AgentTokenRegistrar:
    def __init__(self, agent_name: str, private_key: str, api_client: APIClient):
        self.agent_name = agent_name
        self.private_key = private_key
        self.api_client = api_client
        self.logger = AgentLogger.get_logger(agent_name)

    async def register_forge_token_if_expired(self, current_token: str) -> str:
        """
        Registers or refreshes the agent token used for Forge/Reforge operations.
        If token is empty or expired, signs a timestamped message and exchanges it for a new token.
        """
        # Skenario: Token masih valid, tidak perlu refresh
        if current_token:
            return current_token

        self.logger.info("Initializing Agent Forge Token registration session...")
        timestamp = int(time.time())
        derived_address = CryptoHelper.get_address_from_private_key(self.private_key)
        
        # Susun pesan penandatanganan sesuai standar keamanan blockchain
        domain = {
            "name": "ClawRoyale-Forge",
            "version": "1",
            "chainId": 1  # Standard Ethereum Mainnet ID
        }
        types = {
            "EIP712Domain": [
                {"name": "name", "type": "string"},
                {"name": "version", "type": "string"},
                {"name": "chainId", "type": "uint256"}
            ],
            "ForgeAuth": [
                {"name": "address", "type": "address"},
                {"name": "timestamp", "type": "uint256"}
            ]
        }
        message = {
            "address": derived_address,
            "timestamp": timestamp
        }

        try:
            signature = CryptoHelper.sign_eip712_message(
                private_key_hex=self.private_key,
                domain_data=domain,
                message_types=types,
                message_data=message
            )

            payload = {
                "address": derived_address,
                "timestamp": timestamp,
                "signature": signature
            }

            # Kirim request ke endpoint otentikasi token forge [1]
            response = await self.api_client.safe_request("POST", "agents/tokens", data=payload)
            data = response.get("data", {})
            new_token = data.get("token", "")

            if new_token:
                self.logger.info("Successfully acquired new Agent Forge session token.")
                return new_token
                
            self.logger.error("API responded successfully but token was empty.")
            return ""

        except APIClientError as ace:
            self.logger.error(f"Failed to exchange signature for Forge token: {str(ace)}")
            return ""
        except Exception as e:
            self.logger.critical(f"Unexpected failure inside TokenRegistrar: {str(e)}")
            return ""