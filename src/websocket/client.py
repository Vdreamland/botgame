import asyncio
import json
import websockets
from typing import Dict, Any, Optional
from config import settings
from src.utils.logger import logger

class BaseWebSocketClient:
    """Kelas dasar untuk mengelola siklus hidup koneksi WebSocket ke server Claw Royale."""
    
    def __init__(self, url: str):
        self.url = url
        self.websocket: Optional[websockets.WebSocketClientProtocol] = None
        self._ping_task: Optional[asyncio.Task] = None
        self._is_active = False

    def _get_headers(self) -> Dict[str, str]:
        """Menyusun header wajib sesuai protokol Claw Royale (X-API-Key & X-Version)."""
        return {
            "X-API-Key": settings.API_KEY,
            "X-Version": settings.X_VERSION
        }

    async def connect(self) -> bool:
        """Membuka koneksi WebSocket ke server."""
        if self.websocket:
            await self.disconnect()
            
        logger.info(f"Mencoba membuka koneksi WebSocket ke: {self.url}")
        try:
            self.websocket = await websockets.connect(
                self.url,
                extra_headers=self._get_headers()
            )
            self._is_active = True
            # Jalankan background task untuk ping/pong menjaga koneksi tetap hidup
            self._ping_task = asyncio.create_task(self._heartbeat_loop())
            logger.info("Koneksi WebSocket berhasil dibuka.")
            return True
        except Exception as e:
            logger.error(f"Gagal membuka koneksi WebSocket: {str(e)}")
            self.websocket = None
            return False

    async def disconnect(self):
        """Menutup koneksi WebSocket secara aman."""
        self._is_active = False
        if self._ping_task:
            self._ping_task.cancel()
            try:
                await self._ping_task
            except asyncio.CancelledError:
                pass
            self._ping_task = None

        if self.websocket:
            logger.info("Menutup koneksi WebSocket...")
            await self.websocket.close()
            self.websocket = None
            logger.info("Koneksi WebSocket berhasil ditutup.")

    async def send_json(self, payload: Dict[str, Any]):
        """Mengirim pesan JSON ke server."""
        if not self.websocket or not self._is_active:
            raise ConnectionError("Koneksi WebSocket sedang tidak aktif. Tidak dapat mengirim pesan.")
        
        message = json.dumps(payload)
        await self.websocket.send(message)

    async def receive_json(self) -> Optional[Dict[str, Any]]:
        """Menerima pesan JSON dari server."""
        if not self.websocket or not self._is_active:
            raise ConnectionError("Koneksi WebSocket sedang tidak aktif. Tidak dapat menerima pesan.")
        
        try:
            message = await self.websocket.recv()
            return json.loads(message)
        except websockets.exceptions.ConnectionClosed as e:
            logger.warning(f"Koneksi ditutup oleh server: Kode {e.code}, Alasan: {e.reason}")
            self._is_active = False
            return None
        except Exception as e:
            logger.error(f"Error saat menerima pesan WebSocket: {str(e)}")
            return None

    async def _heartbeat_loop(self):
        """Loop asinkron untuk mengirimkan ping ke server setiap 15 detik."""
        try:
            while self._is_active:
                await asyncio.sleep(15)
                if self.websocket and self._is_active:
                    # Sesuai protokol, kirim { "type": "ping" } untuk menjaga status koneksi
                    await self.send_json({"type": "ping"})
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.debug(f"Heartbeat loop terhenti: {str(e)}")