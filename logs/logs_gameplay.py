import asyncio
from ai.agent_info import format_agent_status_log
from config.agen_config import get_configured_bots

_turn_data = {}
_printed_turns = set()
_log_lock = asyncio.Lock()

async def _print_turn_safely(turn_num: int, is_death: bool = False):
    try:
        num_bots = len(get_configured_bots())
    except Exception:
        num_bots = 1
    delay = 0.0 if (is_death or num_bots <= 1) else 0.1
    await asyncio.sleep(delay)
    async with _log_lock:
        if turn_num in _printed_turns and not is_death:
            return
        if turn_num in _turn_data:
            bots_info = _turn_data[turn_num]
            sorted_bots = sorted(bots_info.keys())
            print(f"#Turn {turn_num}", flush=True)
            border = "-" * 60
            print(border, flush=True)
            bot_blocks = []
            for bot in sorted_bots:
                block = f"[{bot}] \n{bots_info[bot]}"
                bot_blocks.append(block)
            print("\n\n".join(bot_blocks), flush=True)
            print(border, flush=True)
            _printed_turns.add(turn_num)
            if len(_printed_turns) > 100:
                _printed_turns.clear()
            if turn_num in _turn_data:
                del _turn_data[turn_num]

def clear_gameplay_log(bot_name: str):
    pass

def write_gameplay_log(bot_name: str, message: str, view_data: dict = None):
    is_turn_log = message.startswith("# Turn ")
    is_death = False
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
        try:
            self_data = view_data.get("self", {})
            if isinstance(self_data, dict):
                hp = self_data.get("hp", 100)
                is_alive = self_data.get("isAlive", True)
                if hp == 0 or not is_alive:
                    is_death = True
        except Exception:
            pass
    if is_turn_log:
        try:
            lines = message.strip().split("\n")
            if len(lines) >= 4:
                details = "\n".join(lines[1:])
                if turn_num not in _turn_data:
                    _turn_data[turn_num] = {}
                _turn_data[turn_num][bot_name] = details
                try:
                    loop = asyncio.get_running_loop()
                except RuntimeError:
                    loop = asyncio.get_event_loop()
                loop.create_task(_print_turn_safely(turn_num, is_death))
        except Exception:
            pass
    else:
        print(f"[{bot_name}] {message}", flush=True)