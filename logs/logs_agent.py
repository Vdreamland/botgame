import os

_has_logged_startup = False

def draw_status_table(bots_state: dict, num_bots: int):
    global _has_logged_startup
    if not _has_logged_startup:
        os.system("cls" if os.name == "nt" else "clear")
        print("> Reference Skill.md Ver1.12.0")
        print("> Connection Game Successful")
        print(f"> {num_bots} bots detected in configuration\n")
        print("All Setup ready to play ...")
        _has_logged_startup = True