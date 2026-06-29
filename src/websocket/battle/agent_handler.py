import asyncio
import json
import websockets
from config import settings
from src.utils.logger import logger
from src.strategy.evaluators.threat_evaluator import ThreatEvaluator

class AgentHandler:
    
    def __init__(self, socket: websockets.WebSocketClientProtocol):
        self.socket = socket
        self._is_active = True
        self.current_turn = 0
        self.is_alive = True
        self.initial_status_logged = False
        self.last_view = {}
        self.opponents_data = {"players": [], "monsters": []}  # Penampung memori internal data musuh

    async def start_monitoring(self):
        logger.info("Battle monitor active. Monitoring turns and rendering stats...")
        
        try:
            while self._is_active:
                message = await self.socket.recv()
                data = json.loads(message)
                msg_type = data.get("type")
                
                if msg_type == "waiting":
                    continue

                if msg_type in ["agent_view", "turn_advanced"]:
                    new_turn = data.get("turn", 0)
                    self.current_turn = new_turn

                    if "view" in data:
                        self.last_view = data["view"]
                    elif "view" not in data and not self.last_view:
                        continue

                    view_self = self.last_view.get("self", {})
                    hp = view_self.get("hp", 100)
                    max_hp = view_self.get("maxHp", 100)
                    ep = view_self.get("ep", 10)
                    max_ep = view_self.get("maxEp", 10)
                    atk = view_self.get("atk", 25)
                    def_val = view_self.get("def", 5)
                    kills = view_self.get("kills", 0)
                    server_is_alive = view_self.get("isAlive", True)

                    equipped_weapon = view_self.get("equippedWeapon")
                    weapon_name = "None"
                    if equipped_weapon:
                        if isinstance(equipped_weapon, dict):
                            weapon_name = equipped_weapon.get("name") or equipped_weapon.get("displayName") or "Unknown"
                        else:
                            weapon_name = str(equipped_weapon)

                    equipped_armor = view_self.get("equippedArmor")
                    armor_name = "None"
                    if equipped_armor:
                        if isinstance(equipped_armor, dict):
                            armor_name = equipped_armor.get("name") or equipped_armor.get("displayName") or "Unknown"
                        else:
                            armor_name = str(equipped_armor)

                    inventory_raw = view_self.get("inventory", [])
                    inventory_counts = {}
                    for item in inventory_raw:
                        if isinstance(item, dict):
                            name = item.get("name") or item.get("displayName") or "Unknown Item"
                        else:
                            name = str(item)
                        inventory_counts[name] = inventory_counts.get(name, 0) + 1

                    if not inventory_counts:
                        inventory_str = "None"
                    else:
                        inventory_str = " / ".join(f"{item_name} x{qty}" for item_name, qty in inventory_counts.items())

                    current_region = self.last_view.get("currentRegion", {})
                    location_now = current_region.get("name", "Unknown Location")
                    location_planning = "None"

                    # 1. Pemindaian Ringkas Jumlah Musuh per Layer
                    layer0, layer1, layer2 = ThreatEvaluator.scan_enemies(
                        view=self.last_view, 
                        self_id=view_self.get("id", "")
                    )

                    # 2. Pemindaian Mendalam Atribut & Stat Musuh (Disimpan ke Memori Internal)
                    self.opponents_data = ThreatEvaluator.scan_detailed_opponents(
                        view=self.last_view,
                        self_id=view_self.get("id", "")
                    )

                    print(f"# TURN {self.current_turn}")
                    print(f"- Agent Name : {settings.AGENT_NAME} / Status : {'ALIVE' if server_is_alive else 'DEAD'}")
                    print(f"- HP : {hp}/{max_hp} / EP/Energy : {ep}/{max_ep}")
                    print(f"- ATK : {atk} / DEF : {def_val} / Kills : {kills}")
                    print(f"- Equipped > Weapon : {weapon_name} / Armor : {armor_name}")
                    print(f"- Inventory > {inventory_str}")
                    print(f"- Location > Now : {location_now} / Next : {location_planning}")
                    print(f"- Enemy Scan > Layer 0 (Here) : P:{layer0[0]} M:{layer0[1]} / "
                          f"Layer 1 (Adjacent) : P:{layer1[0]} M:{layer1[1]} / "
                          f"Layer 2 (Farther) : P:{layer2[0]} M:{layer2[1]}")
                    print("")

                    # Cetak status kesuksesan pemindaian mendalam secara bersih tanpa mengotori PowerShell
                    logger.info("Enemy stats scan: SUCCESSFUL")

                    if not self.initial_status_logged:
                        self.initial_status_logged = True
                        self.is_alive = server_is_alive
                        if not server_is_alive:
                            logger.warning(f"[DEATH] Agent is connected in a DEAD state. Terminating monitor for testing rejoin...")
                            self._is_active = False
                            break
                    else:
                        if not server_is_alive and self.is_alive:
                            self.is_alive = False
                            logger.warning(f"[DEATH] Agent has been eliminated! (HP: {hp}). Terminating monitor for testing rejoin...")
                            self._is_active = False
                            break

                elif msg_type == "game_ended":
                    logger.info("[FINISHED] The match has fully ended.")
                    self._is_active = False
                    break
                
                elif msg_type == "error":
                    logger.error(f"Server Error: {data.get('message')}")
                    break

        except websockets.exceptions.ConnectionClosed:
            logger.warning("Connection to battle arena closed by server.")
        except Exception as e:
            logger.error(f"Error during battle monitoring: {str(e)}")
        finally:
            self._is_active = False

    def stop(self):
        self._is_active = False