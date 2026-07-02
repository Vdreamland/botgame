import logging
import sys

class CustomFormatter(logging.Formatter):
    def format(self, record):
        if record.levelno == logging.ERROR:
            return f"[ERROR] {record.getMessage()}"
        elif record.levelno == logging.WARNING:
            return f"[WARN]  {record.getMessage()}"
        else:
            return record.getMessage()

def setup_logger():
    logger = logging.getLogger("BotLogger")
    logger.setLevel(logging.INFO)
    
    if logger.hasHandlers():
        logger.handlers.clear()
    
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(CustomFormatter())
    
    logger.addHandler(console_handler)
    logger.propagate = False
    
    return logger

logger = setup_logger()