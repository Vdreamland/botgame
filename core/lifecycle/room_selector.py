# -*- coding: utf-8 -*-
"""
ClawRoyale Dynamic Room Selector.
Decides between paid and free room entry based on settings, balance, and policy.
Provides automatic fallback to free play to prevent execution stalls.
"""

from typing import Dict, Any, Tuple
from utils.logger import AgentLogger
from utils.crypto_helper import CryptoHelper
from core.lifecycle.wallet_policy import WalletPolicyManager


class RoomSelector:
    def __init__(self, agent_name: str, private_key: str):
        self.agent_name = agent_name
        self.private_key = private_key
        self.logger = AgentLogger.get_logger(agent_name)
        self.policy = WalletPolicyManager(agent_name)

    async def determine_optimal_room(self, account_data: Dict[str, Any], 
                                     preferred_type: str) -> Tuple[str, Dict[str, Any]]:
        """
        Determines the entry type (free vs paid) and generates EIP-712 payload if paid.
        :param account_data: Fresh response payload from GET /accounts/me.
        :param preferred_type: Requested type ('free' or 'paid') from config_agents.json.
        :return: Tuple of (actual_entry_type, sign_data_dict)
        """
        data = account_data.get("data", {})
        readiness = data.get("readiness", {})
        
        # Validasi kebijakan utama terlebih dahulu
        if not self.policy.validate_primary_agent_status(account_data):
            self.logger.critical("Primary agent check failed. Blocking game entry to avoid 403 error.")
            return "blocked", {}

        # Skenario 1: Pengguna secara manual mengatur ke Free Room
        if preferred_type.lower() == "free":
            self.logger.info("User preference: Free Room selected.")
            return "free", {}

        # Skenario 2: Pengguna menyetel ke Paid Room -> Periksa kelayakan paidReady
        is_paid_ready = readiness.get("paidReady", False)
        
        if is_paid_ready:
            # Periksa concurrency limit game berbayar yang aktif pada wallet
            if not self.policy.check_active_concurrency_limit(account_data, "paid"):
                self.logger.warning("Paid lobby active concurrency block. Falling back to Free Room.")
                return "free", {}

            self.logger.info("Paid Room criteria satisfied. Compiling EIP-712 sign payload...")
            
            try:
                # Mengumpulkan domain EIP-712 dinamis yang dikirimkan oleh server
                paid_room_info = readiness.get("paidRoom", {})
                signature_request = paid_room_info.get("signatureRequest", {})
                
                domain = signature_request.get("domain", {})
                types = signature_request.get("types", {})
                message = signature_request.get("message", {})

                # Buat tanda tangan digital kriptografi asinkron
                signature = CryptoHelper.sign_eip712_message(
                    private_key_hex=self.private_key,
                    domain_data=domain,
                    message_types=types,
                    message_data=message
                )

                payload = {
                    "signature": signature,
                    "message": message
                }
                
                self.logger.info("Successfully signed EIP-712 transaction for paid room entry.")
                return "paid", payload

            except Exception as e:
                self.logger.error(f"EIP-712 signing failed: {str(e)}. Falling back to Free Room.")
                return "free", {}

        # Skenario 3: Fallback Otomatis jika Paid Room Belum Siap (Never Stall)
        self.logger.warning("Paid Room requirements not met. Safely falling back to Free Room.")
        return "free", {}