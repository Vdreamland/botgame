import asyncio
from config import settings
from src.websocket.lobby.join_handler import JoinHandler
from src.utils.logger import logger

async def test_matchmaking_connection():
    logger.info("=== MEMULAI PENGUJIAN KONEKSI ANTRIAN BOT ===")
    
    # 1. Validasi konfigurasi settings
    try:
        settings.validate_config()
    except ValueError as e:
        logger.error(str(e))
        logger.error("Silakan lengkapi file .env terlebih dahulu.")
        return

    # 2. Inisiasi antrean
    handler = JoinHandler()
    logger.info("Mulai mendaftar ke antrean Free Room...")
    
    # Menjalankan alur matchmaking untuk Free Room
    gameplay_socket = await handler.execute_join_flow(entry_type="free")
    
    if gameplay_socket:
        logger.info("============================================================")
        logger.info("SUKSES: Bot berhasil terhubung dan siap masuk ke arena game!")
        logger.info("============================================================")
        # Sesuai fokus kita saat ini (koneksi saja dulu), kita tutup socket tes setelah berhasil
        await gameplay_socket.close()
        logger.info("Koneksi uji coba ditutup secara aman.")
    else:
        logger.error("============================================================")
        logger.error("GAGAL: Bot tidak berhasil mendapatkan alokasi room.")
        logger.error("============================================================")

if __name__ == "__main__":
    # Menjalankan loop asinkron utama untuk tes koneksi
    asyncio.run(test_matchmaking_connection())