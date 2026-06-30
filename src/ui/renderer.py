from config import settings

class TerminalRenderer:
    
    @staticmethod
    def render_turn(
        turn: int,
        server_is_alive: bool,
        hp: int,
        max_hp: int,
        ep: int,
        max_ep: int,
        atk: int,
        def_val: int,
        kills: int,
        weapon_name: str,
        armor_name: str,
        inventory_str: str,
        ground_str: str,
        location_now: str,
        location_planning: str,
        action_thought: str,
        deadzone_status: str,
        deadzone_warning: str,
        layer0: tuple,
        layer1: tuple,
        layer2: tuple,
        active_pack: str,
        weather: str,
        can_act: bool,
        cooldown_ms: int,
        alert_gauge: int,
        alert_active: bool,
        recent_messages: list,
        target_hp_info: str = "",
        agent_name: str = ""
    ):
        name = agent_name if agent_name else settings.AGENT_NAME
        alert_status = "ACTIVE TARGETING" if alert_active else "SAFE"
        
        print(f"# TURN {turn}")
        print(f"- Agent Name : {name} / Status : {'ALIVE' if server_is_alive else 'DEAD'} / Active Pack : {active_pack}")
        print(f"- HP : {hp}/{max_hp} / EP/Energy : {ep}/{max_ep} / Weather : {weather.upper()}")
        print(f"- ATK : {atk} / DEF : {def_val} / Kills : {kills} / Alert Level : {alert_gauge}/10 ({alert_status})")
        print(f"- Can Act : {can_act} (Cooldown: {cooldown_ms}ms)")
        print(f"- Equipped > Weapon : {weapon_name} / Armor : {armor_name}")
        print(f"- Inventory > {inventory_str}")
        print(f"- Ground > {ground_str}")
        print(f"- Location > Now : {location_now} / Next : {location_planning}{target_hp_info} / Deadzone : {deadzone_status}")
        print(f"- Deadzone > Warning : {deadzone_warning}")
        print(f"- Action Reason : {action_thought}")
        print(f"- Enemy Scan > Layer 0 (Here) : P:{layer0[0]} M:{layer0[1]} / "
              f"Layer 1 (Adjacent) : P:{layer1[0]} M:{layer1[1]} / "
              f"Layer 2 (Farther) : P:{layer2[0]} M:{layer2[1]}")
        print("- Recent Arena Events:")
        if not recent_messages:
            print("  * No recent events.")
        else:
            for msg in recent_messages:
                print(f"  * {msg}")
        print("")