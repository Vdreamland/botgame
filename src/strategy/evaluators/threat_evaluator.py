from typing import Dict, Any, Tuple, List
from config.game_data import MONSTERS, WEAPONS

class ThreatEvaluator:
    
    @staticmethod
    def scan_enemies(view: Dict[str, Any], self_id: str) -> Tuple[Tuple[int, int], Tuple[int, int], Tuple[int, int]]:
        current_region = view.get("currentRegion", {})
        current_region_id = current_region.get("id")
        connections = current_region.get("connections", [])
        
        visible_agents = view.get("visibleAgents", [])
        visible_monsters = view.get("visibleMonsters", [])
        
        layer0 = [0, 0]
        layer1 = [0, 0]
        layer2 = [0, 0]

        for agent in visible_agents:
            if not isinstance(agent, dict): continue
            if agent.get("id") == self_id or not agent.get("isAlive", True): continue
                
            r_id = agent.get("regionId")
            if r_id == current_region_id: layer0[0] += 1
            elif r_id in connections: layer1[0] += 1
            else: layer2[0] += 1

        for monster in visible_monsters:
            if not isinstance(monster, dict): continue
            r_id = monster.get("regionId")
            if r_id == current_region_id: layer0[1] += 1
            elif r_id in connections: layer1[1] += 1
            else: layer2[1] += 1

        return tuple(layer0), tuple(layer1), tuple(layer2)

    @staticmethod
    def scan_detailed_opponents(view: Dict[str, Any], self_id: str) -> Dict[str, List[Dict[str, Any]]]:
        visible_agents = view.get("visibleAgents", [])
        visible_monsters = view.get("visibleMonsters", [])
        scanned_players = []
        scanned_monsters = []

        for agent in visible_agents:
            if not isinstance(agent, dict): continue
            a_id = agent.get("id", "")
            if a_id == self_id or not agent.get("isAlive", True): continue
            
            weapon = agent.get("equippedWeapon", {})
            w_name = "None"
            w_bonus = 0
            w_range = 0
            if weapon:
                w_name = weapon.get("name", "Unknown") if isinstance(weapon, dict) else str(weapon)
                static_weapon = WEAPONS.get(w_name, {})
                w_bonus = static_weapon.get("atk_bonus", 0)
                w_range = static_weapon.get("range", 0)

            scanned_players.append({
                "id": a_id,
                "name": agent.get("name", "Unknown"),
                "hp": agent.get("hp", 100),
                "atk": agent.get("atk", 25 + w_bonus),
                "weapon_range": w_range,
                "region_id": agent.get("regionId")
            })

        for monster in visible_monsters:
            if not isinstance(monster, dict): continue
            m_name = monster.get("name", "Unknown")
            clean_name = m_name.split(" #")[0]
            static_stats = MONSTERS.get(clean_name, {})
            scanned_monsters.append({
                "id": monster.get("id", ""),
                "name": m_name,
                "hp": monster.get("hp", 0),
                "atk": static_stats.get("atk", 0)
            })

        return {"players": scanned_players, "monsters": scanned_monsters}