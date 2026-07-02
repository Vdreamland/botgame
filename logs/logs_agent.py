import os

def draw_status_table(bots_state: dict, num_bots: int):
    os.system("cls" if os.name == "nt" else "clear")
    print("> Reference Skill.md Ver1.12.0")
    print("> Connection Game Successful")
    print(f"> {num_bots} bots detected in configuration\n")
    print("| Agent      | Redeem  | Weekly  | sMoltz | Target | Room       | Status      |")
    print("---------------------------------------------------------------------------------")
    for name, state in bots_state.items():
        agent = f"{name:<10}"
        redeem = f"{state.get('redeem', '-'):<7}"
        weekly = f"{state.get('weekly', '-'):<7}"
        smoltz = f"{state.get('smoltz', '-'):<6}"
        target = f"{state.get('target', '-'):<6}"
        room = f"{state.get('room', '-'):<10}"
        status = f"{state.get('status', '-'):<11}"
        print(f"| {agent} | {redeem} | {weekly} | {smoltz} | {target} | {room} | {status} |")
    print("\nAll Setup ready to play ...")