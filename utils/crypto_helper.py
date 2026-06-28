# -*- coding: utf-8 -*-
"""
ClawRoyale EIP-712 Cryptographic Helper.
Generates secure message signatures for paid room matchmaking.
Uses standard eth_account for structured data signing.
"""

from typing import Dict, Any


class CryptoHelper:
    @staticmethod
    def get_address_from_private_key(private_key_hex: str) -> str:
        """
        Derives the public Ethereum address from a hex private key.
        Returns empty string if key is empty.
        """
        if not private_key_hex:
            return ""
        try:
            # Impor tertunda untuk menghindari kegagalan startup pada kamar gratis
            from eth_account import Account
            
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
        """
        if not private_key_hex:
            raise ValueError("Private key is empty. Cannot sign EIP-712 messages.")

        try:
            from eth_account import Account
            from eth_account.messages import encode_structured_data
            
            if not private_key_hex.startswith("0x"):
                private_key_hex = f"0x{private_key_hex}"

            structured_json = {
                "types": message_types,
                "primaryType": list(message_types.keys())[1] if len(message_types) > 1 else "Message",
                "domain": domain_data,
                "message": message_data
            }

            signable_msg = encode_structured_data(structured_json)
            signed_obj = Account.sign_message(signable_msg, private_key=private_key_hex)
            
            return signed_obj.signature.hex()
        except ImportError:
            raise RuntimeError(
                "EIP-712 signing is not available because your eth-account library is outdated. "
                "Please upgrade it via 'pip install --upgrade eth-account' to play in Paid Rooms."
            )
        except Exception as e:
            raise RuntimeError(f"EIP-712 structured signing failed: {str(e)}")