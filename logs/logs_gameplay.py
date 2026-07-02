import asyncio
from ai.agent_info import format_agent_status_log

_turn_data = {}
_turn_tasks = {}

async def _delayed_print_turn(turn_num: int):
    await asyncio.sleep(0.05)
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
        del _turn_data[turn_num]
        if turn_num in _turn_tasks:
            del _turn_tasks[turn_num]

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
                if turn_num in _turn_tasks:
                    _turn_tasks[turn_num].cancel()
                _turn_tasks[turn_num] = loop.create_task(_delayed_print_turn(turn_num))
        except Exception:
            pass
    else:
        print(f"[{bot_name}] {message}", flush=True)