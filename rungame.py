import asyncio
import time
from src.api import get_account_state, redeem_welcome_code
from src.websocket_handler import run_ws_loop
from src.config import get_headers, get_all_bot_keys

async def run_bot(bot_name, api_key):
    headers = get_headers(api_key)
    first_run = True
    while True:
        account_data = get_account_state(headers=headers)
        if not account_data:
            print(f"[{bot_name}] Failed to retrieve account data. Retrying in 10 seconds...")
            await asyncio.sleep(10)
            continue
            
        if first_run:
            print(f"[{bot_name}] Account loaded: {account_data.get('name')} | Balance: {account_data.get('balance')} sMoltz")
            print(f"[{bot_name}] Checking onboarding bundle claim (WELCOME)...")
            redeem_welcome_code(headers=headers)
            first_run = False
            
        current_games = account_data.get("currentGames", [])
        active_game = next((g for g in current_games if g.get("isAlive") and g.get("gameStatus") != "finished"), None)
        
        try:
            await run_ws_loop(active_game=active_game, headers=headers)
        except Exception as e:
            print(f"[{bot_name}] Error in connection loop: {e}")
            
        print(f"\n[{bot_name}] Session finished. Checking for next match in 5 seconds...")
        await asyncio.sleep(5)

def main():
    bots = get_all_bot_keys()
    if not bots:
        print("No active bot API keys found in .env.")
        return
        
    print(f"Loaded {len(bots)} bots. Starting concurrent gameplay loop...")
    
    tasks = []
    for bot_name, api_key in bots:
        tasks.append(run_bot(bot_name, api_key))
        
    asyncio.run(asyncio.gather(*tasks))

if __name__ == "__main__":
    main()