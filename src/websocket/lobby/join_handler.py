import asyncio
from typing import Dict, Any, Optional
import websockets
from config import settings
from src.utils.logger import logger
from src.websocket.client import BaseWebSocketClient

class JoinHandler(BaseWebSocketClient):
    """Mengelola proses antrean masuk room (matchmaking) melalui endpoint /ws/join."""
    
    def __init__(self):
        super().__init__(settings.WS_JOIN_URL)

    async def execute_join_flow(self, entry_type: str = "free") -> Optional[websockets.WebSocketClientProtocol]:
        """
        Menjalankan alur pendaftaran antrean (Free Room / Paid Room).
        Mengembalikan koneksi socket aktif jika berhasil dimasukkan ke dalam game.
        """
        # 1. Hubungkan ke WebSocket /ws/join
        connected = await self.connect()
        if not connected:
            logger.error("Gagal memulai alur pendaftaran antrean karena koneksi bermasalah.")
            return None

        try:
            # 2. Baca frame pertama dari server (Wajib berupa frame 'welcome')
            logger.info("Menunggu pesan 'welcome' dari server...")
            welcome_frame = await self.receive_json()
            if not welcome_frame or welcome_frame.get("type") != "welcome":
                logger.error(f"Protokol salah. Mengharapkan 'welcome' frame, menerima: {welcome_frame}")
                await self.disconnect()
                return None

            decision = welcome_frame.get("decision")
            logger.info(f"Menerima keputusan awal dari server: [ {decision} ]")

            # 3. Penanganan keputusan server
            if decision == "BLOCKED":
                logger.error("Akses diblokir oleh server. Periksa kelayakan akun (readiness flags) di /accounts/me.")
                await self.disconnect()
                return None
                
            elif decision == "ALREADY_IN_GAME":
                logger.info("Akun terdeteksi masih memiliki game aktif yang sedang berjalan.")
                logger.info("Server otomatis melakukan proksi koneksi langsung ke arena pertarungan.")
                # Socket ini sekarang valid digunakan sebagai gameplay socket
                active_socket = self.websocket
                # Cabut kepemilikan socket agar tidak ditutup saat objek JoinHandler dihancurkan
                self.websocket = None
                await self.disconnect()
                return active_socket

            # 4. Kirim respon 'hello' untuk masuk antrean
            if entry_type == "free":
                logger.info("Mengirim hello frame untuk mendaftar antrean [ FREE ROOM ]")
                hello_payload = {
                    "type": "hello",
                    "entryType": "free"
                }
                await self.send_json(hello_payload)
            elif entry_type == "paid":
                logger.info("Mengirim hello frame untuk mendaftar antrean [ PAID ROOM ]")
                # Menggunakan mode default offchain sMoltz sesuai instruksi skill.md
                hello_payload = {
                    "type": "hello",
                    "entryType": "paid",
                    "mode": "offchain"
                }
                await self.send_json(hello_payload)
            else:
                logger.error(f"Entry type '{entry_type}' tidak dikenal.")
                await self.disconnect()
                return None

            # 5. Loop memantau status antrean hingga dialihkan ke arena pertarungan
            logger.info("Menunggu alokasi room dari server (Proses Matchmaking)...")
            while self._is_active:
                response = await self.receive_json()
                if not response:
                    logger.error("Koneksi terputus saat berada di dalam antrean room.")
                    break

                response_type = response.get("type")
                logger.info(f"Pesan Antrean: {response}")

                # Penanganan jika diperlukan tanda tangan EIP-712 untuk Paid Room
                if response_type == "sign_required":
                    logger.warning("Server meminta tanda tangan EIP-712 untuk masuk Paid Room.")
                    # Jika Anda ingin mengaktifkan fitur ini nanti, kirim file references/contracts.md 
                    # agar kita bisa membuat implementasi crypto.py yang akurat tanpa asumsi.
                    logger.error("Fitur tanda tangan Paid Room belum diaktifkan karena memerlukan references/contracts.md.")
                    break

                # Berhasil dialokasikan ke room pertarungan
                if response_type == "assigned" or response_type == "joined":
                    game_id = response.get("gameId")
                    agent_id = response.get("agentId")
                    logger.info(f"MATCHMAKING BERHASIL! Dialokasikan ke Game ID: {game_id}, Agent ID: {agent_id}")
                    logger.info("Socket ini otomatis bertransisi menjadi gameplay socket.")
                    
                    active_socket = self.websocket
                    # Cabut kepemilikan socket agar tidak ditutup oleh disconnect()
                    self.websocket = None
                    await self.disconnect()
                    return active_socket

                # Mengabaikan pesan pong / keep-alive
                if response_type == "pong":
                    continue

        except Exception as e:
            logger.error(f"Terjadi error saat menjalankan alur antrean: {str(e)}")

        await self.disconnect()
        return None