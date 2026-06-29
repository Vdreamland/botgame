import logging
import sys

def setup_logger(name: str = "Bot") -> logging.Logger:
    """Mengonfigurasi logger minimalis, bersih, dan rapi untuk PowerShell."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        
        # Format sangat bersih: [LEVEL] Pesan
        formatter = logging.Formatter(
            fmt="[%(levelname)s] %(message)s"
        )
        
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
    return logger

# Ekspor logger global
logger = setup_logger()