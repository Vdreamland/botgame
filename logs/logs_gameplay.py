import os
from ai.agent_info import format_agent_status_log

def clear_gameplay_log(bot_name: str):
    directory = os.path.join("logs", "gameplay")
    if not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)
    
    log_file_path = os.path.join(directory, f"{bot_name}.log")
    try:
        with open(log_file_path, "w", encoding="utf-8") as f:
            f.write("")
    except Exception:
        pass

def write_gameplay_log(bot_name: str, message: str, view_data: dict = None):
    directory = os.path.join("logs", "gameplay")
    if not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)
    
    log_file_path = os.path.join(directory, f"{bot_name}.log")
    is_turn_log = message.startswith("# Turn ")
    
    if is_turn_log:
        if view_data is None:
            return
        try:
            parts = message.split()
            if len(parts) >= 3:
                turn_num = int(parts[2])
                message = format_agent_status_log(bot_name, turn_num, view_data)
        except Exception:
            pass
    
    with open(log_file_path, "a", encoding="utf-8") as f:
        f.write(message + "\n")
        
    if is_turn_log:
        border = "-" * 60
        lines = message.strip().split("\n")
        print(f"\n{border}")
        for line in lines:
            print(f"[{bot_name}] {line}")
        print(f"{border}\n")
    else:
        print(f"[{bot_name}] {message}")