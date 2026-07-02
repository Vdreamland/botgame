import logging
import sys
import os

if sys.platform == "win32":
    os.system("")

class CustomFormatter(logging.Formatter):
    def format(self, record):
        time_str = self.formatTime(record, "%H:%M:%S")
        if record.levelno == logging.ERROR:
            return f"\033[91m[{time_str}] [ERROR] {record.getMessage()}\033[0m"
        elif record.levelno == logging.WARNING:
            return f"\033[93m[{time_str}] [WARN]  {record.getMessage()}\033[0m"
        else:
            return f"[{time_str}] [INFO]  {record.getMessage()}"

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