import asyncio
import json
import websockets
from config import settings
from src.utils.logger import logger
from src.strategy.evaluators.threat_evaluator import ThreatEvaluator
from src.strategy.brain.game_context import GameContext
from src.strategy.brain.decision_engine import DecisionEngine
from src.ui.renderer import TerminalRenderer
from src.websocket.battle.state_parser import StateParser

class AgentHandler:
    
    def __init__(self, socket: websockets.WebSocketClientProtocol):
        self.socket = socket
        self._is_active = True
        self.current_turn = 0
        self.last_rendered_turn = 0  # Memori pelacak nomor turn yang sudah digambar ke PowerShell
        self.is_alive = True
        self.initial_status_logged = False
        self.last_view = {}
        self.opponents_data = {"players": [], "monsters": []}
        self.context = GameContext()
        self.brain = DecisionEngine()

    async def send_json(self, payload: dict):
        try:
            await self.socket.send(json.dumps(payload))
        except Exception:
            pass

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
                    is_new_turn = (new_turn != self.current_turn)
                    self.current_turn = new_turn

                    if "view" in data:
                        self.last_view = data["view"]
                    elif "view" not in data and not self.last_view:
                        continue

                    view_self = self.last_view.get("self", {})
                    server_is_alive = view_self.get("isAlive", True)

                    current_region = self.last_view.get("currentRegion", {})
                    pending_zones = self.last_view.get("pendingDeathzones", [])
                    self.context.update_map(current_region, pending_zones)

                    computed_action = None
                    if is_new_turn and server_is_alive:
                        computed_action = self.brain.compute_action(self.last_view, self.context)
                        if computed_action:
                            await self.send_json(computed_action)

                    self.opponents_data = ThreatEvaluator.scan_detailed_opponents(
                        view=self.last_view,
                        self_id=view_self.get("id", "")
                    )

                    # MEMUTUSKAN APAKAH PERLU RENDERING (Hanya digambar tepat 1 kali saja per nomor turn)
                    if self.current_turn != self.last_rendered_turn:
                        self.last_rendered_turn = self.current_turn

                        parsed_state = StateParser.parse(
                            view=self.last_view,
                            context=self.context,
                            computed_action=computed_action,
                            is_new_turn=is_new_turn
                        )

                        TerminalRenderer.render_turn(
                            turn=self.current_turn,
                            server_is_alive=parsed_state["server_is_alive"],
                            hp=parsed_state["hp"],
                            max_hp=parsed_state["max_hp"],
                            ep=parsed_state["ep"],
                            max_ep=parsed_state["max_ep"],
                            atk=parsed_state["atk"],
                            def_val=parsed_state["def_val"],
                            kills=parsed_state["kills"],
                            weapon_name=parsed_state["weapon_name"],
                            armor_name=parsed_state["armor_name"],
                            inventory_str=parsed_state["inventory_str"],
                            ground_str=parsed_state["ground_str"],
                            location_now=parsed_state["location_now"],
                            location_planning=parsed_state["location_planning"],
                            layer0=parsed_state["layer0"],
                            layer1=parsed_state["layer1"],
                            layer2=parsed_state["layer2"]
                        )

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
                                logger.warning(f"[DEATH] Agent has been eliminated! (HP: {parsed_state['hp']}). Terminating monitor for testing rejoin...")
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