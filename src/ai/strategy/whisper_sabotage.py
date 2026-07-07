import os

def get_ally_names(my_name):
    allies = set()
    for key, value in os.environ.items():
        if key.startswith("BOT") and key.endswith("_NAME"):
            if value and value != my_name:
                allies.add(value)
    return allies

def generate_sabotage_whispers(manager, raw_data):
    view = raw_data.get("view", {})
    self_data = view.get("self", {})
    my_id = self_data.get("id")
    my_name = self_data.get("name", "Unknown")
    
    visible_agents = view.get("visibleAgents", [])
    ally_names = get_ally_names(my_name)
    
    whisper_actions = []
    
    for agent in visible_agents:
        agent_id = agent.get("id")
        if agent_id and agent_id != my_id:
            agent_name = agent.get("name")
            if agent_name and agent_name not in ally_names:
                if agent.get("isAlive", True):
                    whisper_actions.append({
                        "type": "action",
                        "data": {
                            "type": "whisper",
                            "target": agent_name,
                            "message": "hello"
                        }
                    })
                    
    return whisper_actions