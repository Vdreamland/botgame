from utils.logger import logger

def log_ws_connecting(url: str):
    logger.info(f"Connecting to WebSocket: {url}")

def log_ws_connected():
    logger.info("WebSocket connection established successfully.")

def log_ws_error(error_msg: str):
    logger.error(f"WebSocket error: {error_msg}")

def log_ws_send(data: dict):
    logger.info(f"WebSocket sent payload: {data}")

def log_ws_receive(data: str):
    logger.info(f"WebSocket received raw data: {data}")

def log_ws_closed():
    logger.info("WebSocket connection closed.")