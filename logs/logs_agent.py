import sys

_has_logged_startup = False

def draw_status_table(bots_state: dict, num_bots: int):
    global _has_logged_startup
    if not _has_logged_startup:
        sys.stdout.write("\033[H\033[2J")
        sys.stdout.flush()
        print("> Reference Skill.md Ver1.12.0")
        print("> Connection Game Successful")
        print(f"> {num_bots} bots detected in configuration\n")
        _has_logged_startup = True