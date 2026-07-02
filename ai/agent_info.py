def format_agent_status_log(bot_name: str, turn: int, view_data: dict) -> str:
    if not view_data:
        return f"# Turn {turn} [{bot_name}]\nHP: Unknown | EP: Unknown"

    self_data = view_data.get("self", {})
    hp = self_data.get("hp", "Unknown")
    ep = self_data.get("ep", "Unknown")

    return f"# Turn {turn} [{bot_name}]\nHP: {hp} | EP: {ep}"