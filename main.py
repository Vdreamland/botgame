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

    # 2. Inisiasi antrean sesuai preferensi room di settings
    handler = JoinHandler()
    logger.info(f"Mulai mendaftar ke antrean [ {settings.ROOM_PREFERENCE.upper()} ROOM ]...")
    
    # Menjalankan alur matchmaking dinamis berdasarkan preferensi di .env
    gameplay_socket = await handler.execute_join_flow(entry_type=settings.ROOM_PREFERENCE)
    
    if gameplay_socket:
        logger.info("============================================================")
        logger.info(f"SUKSES: Bot berhasil masuk antrean {settings.ROOM_PREFERENCE.upper()} dan teralokasi!")
        logger.info("============================================================")
        # Menutup socket tes setelah berhasil uji koneksi
        await gameplay_socket.close()
        logger.info("Koneksi uji coba ditutup secara aman.")
    else:
        logger.error("============================================================")
        logger.error(f"GAGAL: Bot tidak berhasil mendapatkan alokasi room {settings.ROOM_PREFERENCE.upper()}.")
        logger.error("============================================================")

if __name__ == "__main__":
    # Menjalankan loop asinkron utama untuk tes koneksi
    asyncio.run(test_matchmaking_connection())