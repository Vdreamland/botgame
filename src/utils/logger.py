import logging
import sys

def setup_logger(name: str = "ClawRoyaleBot") -> logging.Logger:
    """Mengonfigurasi logger terstruktur untuk konsol PowerShell."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        
        # Format log yang bersih untuk CLI / PowerShell
        formatter = logging.Formatter(
            fmt="[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s",
            datefmt="%H:%M:%S"
        )
        
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
    return logger

# Ekspor instance logger global untuk kemudahan penggunaan
logger = setup_logger()