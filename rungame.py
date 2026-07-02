import asyncio
import os
import sys
from dotenv import load_dotenv
from config.agen_config import load_agent_configs, auto_claim_rewards
from utils.api_client import ClawRoyaleAPI
from utils.ws_client import GameWebSocketClient
from utils.logger import setup_logger
from logs.logs_agent import log_agent_status_table
from logs.quest_reward_log import log_quest_reward_status
from web.server import start_web_server

# Global list of bots status for dashboard and terminal
global_bots_status = []

async def log_agent_status_loop(version, total_bots):
    log_agent_status_table(version, "Successful", global_bots_status)

async def run_bot(config, api_client, bot_status):
    api = ClawRoyaleAPI(config["api_key"])
    bot_status["status"] = "Connecting"
    
    # Auto claim reward
    bot_status["status"] = "Claiming Rewards"
    await auto_claim_rewards(api, bot_status)
    
    # Start websocket client
    ws_client = GameWebSocketClient(config["api_key"], bot_status)
    await ws_client.connect()

async def main():
    load_dotenv()
    
    VERSION = "1.12.0"
    
    # Setup network/quest logger
    setup_logger()
    
    agent_configs = load_agent_configs()
    total_bots = len(agent_configs)
    
    # Initialize global status list
    for config in agent_configs:
        global_bots_status.append({
            "name": config["name"],
            "redeem": "Checking",
            "weekly": "Checking",
            "smoltz": 0,
            "target": config["room_type"].capitalize(),
            "room": "Room",
            "status": "Starting"
        })
    
    # Start dashboard server
    asyncio.create_task(start_web_server(global_bots_status))
    
    # Start terminal log loop
    asyncio.create_task(log_agent_status_loop(VERSION, total_bots))
    
    # Start all bots concurrently
    tasks = []
    for i, config in enumerate(agent_configs):
        tasks.append(run_bot(config, ClawRoyaleAPI(config["api_key"]), global_bots_status[i]))
    
    await asyncio.gather(*tasks)

if __name__ == "__main__":
    try:
        if sys.platform == "win32":
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nServer stopped manually.")