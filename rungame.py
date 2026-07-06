import asyncio
import time
from src.api import get_account_state, redeem_welcome_code
from src.websocket_handler import run_ws_loop

def initialize_agent():
    print("Initializing Agent...")
    account_data = get_account_state()
    if not account_data:
        print("Failed to retrieve account data.")
        return None

    print(f"Account loaded: {account_data.get('name')} | Balance: {account_data.get('balance')} sMoltz")
    
    print("Checking onboarding bundle claim (WELCOME)...")
    redeem_welcome_code()
    
    return account_data

def main():
    while True:
        account_data = initialize_agent()
        if not account_data:
            print("Failed to initialize agent. Retrying in 10 seconds...")
            time.sleep(10)
            continue

        current_games = account_data.get("currentGames", [])
        active_game = next((g for g in current_games if g.get("isAlive") and g.get("gameStatus") != "finished"), None)
        
        try:
            asyncio.run(run_ws_loop(active_game=active_game))
        except Exception as e:
            print(f"Error in connection loop: {e}")
            
        print("\nSession finished. Checking for next match in 5 seconds...")
        time.sleep(5)

if __name__ == "__main__":
    main()