# -*- coding: utf-8 -*-
"""
ClawRoyale Onboarding Redeemer.
Handles the automatic claim of the 'WELCOME' starter pack for new accounts.
"""

from utils.logger import AgentLogger
from core.network.api_client import APIClient, APIClientError


class OnboardingRedeemer:
    def __init__(self, agent_name: str, api_client: APIClient):
        self.agent_name = agent_name
        self.api_client = api_client
        self.logger = AgentLogger.get_logger(agent_name)

    async def redeem_welcome_bundle_if_needed(self, account_data: dict) -> bool:
        """
        Verifies if the agent account has already claimed its welcome starter bundle.
        If not, automatically executes the claim via the REST API.
        :param account_data: The account profile payload from GET /accounts/me.
        :return: True if successfully claimed or already claimed; False on execution failure.
        """
        data = account_data.get("data", {})
        onboarding = data.get("onboarding", {})
        
        # Cek status kelayakan welcome pack dari profile
        has_redeemed = onboarding.get("welcomeRedeemed", False)

        if has_redeemed:
            self.logger.info("Welcome starter bundle has already been successfully redeemed for this account.")
            return True

        self.logger.warning("Account is eligible for the welcome starter bundle. Initiating POST claim...")
        
        try:
            response = await self.api_client.claim_welcome_pack()
            status = response.get("status", "")
            
            if status == "success" or response.get("code") == "SUCCESS":
                self.logger.info("Onboarding welcome bundle claimed successfully! (2 packs, 3 relics, 13 stones received).")
                return True
                
            self.logger.error(f"Redeem API responded with an unexpected status: {response}")
            return False

        except APIClientError as ace:
            # Cegah bot terhenti jika error adalah kode ganda atau klaim paralel
            if "ALREADY_CLAIMED" in str(ace) or "already claimed" in str(ace).lower():
                self.logger.warning("Redeem API reported that this welcome bundle was already claimed. Syncing...")
                return True
            self.logger.error(f"Failed to execute onboarding Welcome redeem: {str(ace)}")
            return False
        except Exception as e:
            self.logger.critical(f"Unexpected exception during welcome bundle redemption: {str(e)}")
            return False