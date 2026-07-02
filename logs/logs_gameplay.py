from ai.agent_info import format_agent_status_log

def clear_gameplay_log(bot_name: str):
    pass

def write_gameplay_log(bot_name: str, message: str, view_data: dict = None):
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
        
    if is_turn_log:
        border = "-" * 60
        lines = message.strip().split("\n")
        
        if lines[0].endswith(f" [{bot_name}]"):
            lines[0] = lines[0].replace(f" [{bot_name}]", "")
            
        print(border)
        for line in lines:
            print(f"[{bot_name}] {line}")
        print(border)
    else:
        print(f"[{bot_name}] {message}")