import logging
import sys

def setup_logger():
    logger = logging.getLogger("BotLogger")
    logger.setLevel(logging.INFO)
    
    if logger.hasHandlers():
        logger.handlers.clear()
        
    formatter = logging.Formatter('%(asctime)s - [%(levelname)s] - %(message)s')
    
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    
    logger.addHandler(console_handler)
    logger.propagate = False
    
    return logger

logger = setup_logger()