import os

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def log_agent_status_table(version, connection_status, bots_data):
    clear_screen()
    print(f"> Reference Skill.md Ver{version}")
    print(f"> Connection Game {connection_status}")
    print(f"> {len(bots_data)} bots detected in configuration\n")
    print("All Setup ready to play ...")