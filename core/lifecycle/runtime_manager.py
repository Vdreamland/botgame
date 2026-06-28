# -*- coding: utf-8 -*-
"""
ClawRoyale Autonomous Runtime Lifecycle Manager.
Coordinates setup, welcome claims, room selector signing, queue entry, and game loops.
"""

import asyncio
from utils.logger import AgentLogger
from core.network.api_client import APIClient
from core.network.ws_client import WebSocketClient
from core.lifecycle.state_router import StateRouter
from core.lifecycle.setup_handler import SetupHandler
from core.lifecycle.onboarding_redeemer.py import OnboardingRedeemer if False else None # Import safety

# Pastikan import aman dari kegagalan path
from core.lifecycle.onboarding_redeemer import OnboardingRedeemer
from core.lifecycle.room_selector import RoomSelector


class RuntimeManager:
    def __init__(self, agent_name: str, private_key: str, room_preference: str,
                 api_client: APIClient, ws_client: WebSocketClient):
        self.agent_name = agent_name
        self.private_key = private_key
        self.room_preference = room_preference
        self.api_client = api_client
        self.ws_client = ws_client
        
        self.logger = AgentLogger.get_logger(agent_name)
        
        # Inisialisasi modul pembantu alur hidup
        self.router = StateRouter(agent_name, api_client)
        self.setup = SetupHandler(agent_name, private_key, api_client)
        self.redeemer = OnboardingRedeemer(agent_name, api_client)
        self.selector = RoomSelector(agent_name, private_key)
        
        self.is_running = False
        self._main_task: Optional[asyncio.Task] = None

    async def start(self) -> None:
        """Starts the autonomous agent runtime asynchronously."""
        self.is_running = True
        self.logger.info("Autonomous Agent Runtime initialized successfully.")
        self._main_task = asyncio.create_task(self._execution_loop())

    async def stop(self) -> None:
        """Stops the runtime execution and closes network sockets."""
        self.is_running = False
        if self._main_task:
            self._main_task.cancel()
            self._main_task = None
        await self.ws_client.disconnect()
        self.logger.warning("Autonomous Agent Runtime shut down gracefully.")

    async def _execution_loop(self) -> None:
        """
        Infinite autonomous execution loop.
        Never crashes; handles errors gracefully with exponential backoff.
        """
        consecutive_errors = 0
        
        while self.is_running:
            try:
                # 1. Pindai Status Akun di Database Server ClawRoyale [1]
                state, account_data = await self.router.route_current_state()
                consecutive_errors = 0  # Reset counter error jika route berhasil

                # --- STATE 1: NO_ACCOUNT (Belum Terdaftar) ---
                if state == "NO_ACCOUNT":
                    # Lakukan verifikasi whitelist
                    is_ok = await self.setup.verify_whitelist_status()
                    if is_ok:
                        # Daftarkan akun baru
                        success, _ = await self.setup.register_new_agent_account()
                        if not success:
                            self.logger.error("Failed to register account. Retrying in 30s...")
                            await asyncio.sleep(30)
                    else:
                        self.logger.error("Address is not whitelisted. Retrying check in 60s...")
                        await asyncio.sleep(60)
                    continue

                # --- STATE 2: ERROR JARINGAN ---
                elif state == "ERROR":
                    raise RuntimeError("REST API returned ERROR state during routing.")

                # --- STATE 3: IN_GAME (Bypass Rekoneksi WebSocket) [1] ---
                elif state == "IN_GAME":
                    data = account_data.get("data", {})
                    current_games = data.get("currentGames", [])
                    if current_games:
                        active_game = current_games[0]
                        token = active_game.get("token")
                        
                        # Langsung hubungkan kembali ke socket gameplay [5]
                        await self.ws_client.connect_to_gameplay(token)
                        
                        # Tunggu hingga pertempuran selesai
                        while self.ws_client.is_connected:
                            await asyncio.sleep(2.0)
                    continue

                # --- STATE 4: READY_FREE / READY_PAID (Siap Memulai Antrean Match) [5] ---
                elif state in ["READY_FREE", "READY_PAID"]:
                    # Lakukan klaim welcome bundle otomatis jika memenuhi syarat [3]
                    await self.redeemer.redeem_welcome_bundle_if_needed(account_data)

                    # Tentukan tipe kamar optimal (Free vs Paid) & tanda tangani pesan jika Paid [5, 6]
                    actual_entry, sign_payload = await self.selector.determine_optimal_room(
                        account_data, self.room_preference
                    )

                    if actual_entry == "blocked":
                        self.logger.critical("Agent is blocked due to SC wallet policy violation. Retrying in 60s...")
                        await asyncio.sleep(60)
                        continue

                    # Bergabung ke antrean websocket ws/join [5]
                    await self.ws_client.connect_to_queue(actual_entry)
                    
                    # Kirim payload data registrasi tanda tangan jika tipe kamar berbayar (Paid) [6]
                    if actual_entry == "paid" and sign_payload:
                        # Payload dikirimkan asinkron sebagai pendaftaran validasi kamar berbayar [6]
                        await self.ws_client.send_message({
                            "type": "register_paid",
                            "signature": sign_payload.get("signature"),
                            "message": sign_payload.get("message")
                        })

                    # Biarkan loop antrean WS berjalan hingga dialihkan ke game atau terputus
                    while self.ws_client.is_connected:
                        await asyncio.sleep(2.0)

            except asyncio.CancelledError:
                break
            except Exception as e:
                consecutive_errors += 1
                backoff_time = min(300, 5 * (2 ** (consecutive_errors - 1)))
                self.logger.critical(
                    f"Fatal crash inside Autonomous Loop (Consecutive: {consecutive_errors}): {str(e)}. "
                    f"Backing off execution for {backoff_time}s..."
                )
                await self.ws_client.disconnect()
                await asyncio.sleep(backoff_time)