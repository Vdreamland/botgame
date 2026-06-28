# -*- coding: utf-8 -*-
"""
ClawRoyale EIP-712 Cryptographic Helper.
Generates secure message signatures for paid room matchmaking.
Uses standard eth_account for structured data signing.
"""

from typing import Dict, Any
from eth_account import Account
from eth_account.messages import encode_structured_data


class CryptoHelper:
    @staticmethod
    def get_address_from_private_key(private_key_hex: str) -> str:
        """
        Derives the public Ethereum address from a hex private key.
        """
        try:
            # Pastikan format hex diawali dengan 0x
            if not private_key_hex.startswith("0x"):
                private_key_hex = f"0x{private_key_hex}"
            
            account = Account.from_key(private_key_hex)
            return account.address
        except Exception as e:
            raise ValueError(f"Invalid private key format: {str(e)}")

    @staticmethod
    def sign_eip712_message(private_key_hex: str, domain_data: Dict[str, Any], 
                            message_types: Dict[str, Any], message_data: Dict[str, Any]) -> str:
        """
        Signs structured typed data according to the EIP-712 standard.
        :param private_key_hex: Private key used to sign the message.
        :param domain_data: EIP-712 Domain metadata dictionary.
        :param message_types: EIP-712 Types specification.
        :param message_data: The actual payload message contents.
        :return: Hex string signature.
        """
        try:
            if not private_key_hex.startswith("0x"):
                private_key_hex = f"0x{private_key_hex}"

            # Susun struktur data EIP-712 standar
            structured_json = {
                "types": message_types,
                "primaryType": list(message_types.keys())[1] if len(message_types) > 1 else "Message",
                "domain": domain_data,
                "message": message_data
            }

            # Enkode data terstruktur dan tanda tangani
            signable_msg = encode_structured_data(structured_json)
            signed_obj = Account.sign_message(signable_msg, private_key=private_key_hex)
            
            return signed_obj.signature.hex()
        except Exception as e:
            raise RuntimeError(f"EIP-712 structured signing failed: {str(e)}")