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
    
    def __init__(self, socket: websockets.WebSocketClientProtocol, agent_name: str = None):
        self.socket = socket
        self.agent_name = agent_name or settings.AGENT_NAME
        self._is_active = True
        self.current_turn = 0
        self.last_rendered_turn = 0
        self.is_alive = True
        self.initial_status_logged = False
        self.action_sent_this_turn = False
        self.last_view = {}
        self.opponents_data = {"players": [], "monsters": []}
        self.context = GameContext()
        self.brain = DecisionEngine()
        
        # Perekam cooldown dan status izin aksi kelompok
        self.can_act = True
        self.cooldown_remaining_ms = 0

    async def send_json(self, payload: dict):
        try:
            await self.socket.send(json.dumps(payload))
        except Exception:
            pass

    async def start_monitoring(self):
        logger.info(f"Battle monitor active for [ {self.agent_name} ]. Monitoring turns and rendering stats...")
        
        try:
            while self._is_active:
                message = await self.socket.recv()
                data = json.loads(message)
                msg_type = data.get("type")

                if msg_type == "waiting":
                    continue
                    
                elif msg_type == "action_result":
                    # Update status cooldown setelah menerima aksi dari server
                    self.can_act = data.get("canAct", True)
                    self.cooldown_remaining_ms = data.get("cooldownRemainingMs", 0)
                    
                elif msg_type == "can_act_changed":
                    # Cooldown telah berakhir di tingkat server
                    self.can_act = data.get("canAct", True)
                    self.cooldown_remaining_ms = data.get("cooldownRemainingMs", 0)
                    
                    # REAL-TIME TRIGGER: Jika cooldown habis dan bot belum beraksi di turn ini, langsung tembak instan!
                    view_self = self.last_view.get("self", {}) if self.last_view else {}
                    server_is_alive = view_self.get("isAlive", True) if view_self else True
                    
                    if self.can_act and server_is_alive and not self.action_sent_this_turn and self.last_view:
                        computed_action = self.brain.compute_action(self.last_view, self.context)
                        if computed_action:
                            action_data = computed_action.get("data", {})
                            action_type = action_data.get("type")
                            
                            is_cooldown_group = action_type in ["move", "explore", "attack", "use_item", "interact", "rest"]
                            if is_cooldown_group:
                                self.action_sent_this_turn = True
                                
                            await self.send_json(computed_action)

                elif msg_type in ["agent_view", "turn_advanced"]:
                    new_turn = data.get("turn", 0)
                    is_new_turn = (new_turn != self.current_turn)
                    self.current_turn = new_turn
                    self.last_view = data.get("view", {})

                    if is_new_turn:
                        self.action_sent_this_turn = False

                    view_self = self.last_view.get("self", {})
                    server_is_alive = view_self.get("isAlive", True)

                    current_region = self.last_view.get("currentRegion", {})
                    
                    bot_name = view_self.get("name", "")
                    region_id = current_region.get("id")
                    if bot_name and region_id:
                        settings.BOT_POSITIONS[bot_name] = region_id

                    # Ekstraksi tangguh multi-sumber dari root data dan view (Mengamankan sinkronisasi deadzone)
                    pending_zones = (
                        self.last_view.get("pendingDeathzones") or 
                        self.last_view.get("pendingDeathZones") or 
                        data.get("pendingDeathzones") or 
                        data.get("pendingDeathZones") or 
                        []
                    )
                    self.context.update_map(current_region, pending_zones)

                    # PEMINDAIAN DETAIL MUSUH: Data dimasukkan langsung ke context sebelum aksi dihitung
                    self.context.opponents_data = ThreatEvaluator.scan_detailed_opponents(
                        view=self.last_view,
                        self_id=view_self.get("id", "")
                    )
                    self.opponents_data = self.context.opponents_data

                    computed_action = None
                    
                    # COOLDOWN-SAFE CHECK: Hanya hitung aksi jika status izin aksi kelompok (can_act) aktif
                    if server_is_alive and self.can_act and not self.action_sent_this_turn:
                        computed_action = self.brain.compute_action(self.last_view, self.context)
                        if computed_action:
                            action_thought = computed_action.get("thought", "Executing strategic action.")
                            action_data = computed_action.get("data", {})
                            action_type = action_data.get("type")
                            
                            is_cooldown_group = action_type in ["move", "explore", "attack", "use_item", "interact", "rest"]
                            if is_cooldown_group:
                                self.action_sent_this_turn = True

                    if computed_action:
                        await self.send_json(computed_action)

                    if self.current_turn != self.last_rendered_turn:
                        self.last_rendered_turn = self.current_turn

                        parsed_state = StateParser.parse(
                            view=self.last_view,
                            context=self.context,
                            computed_action=computed_action,
                            is_new_turn=is_new_turn
                        )

                        # Membaca pikiran tindakan langsung dari computed_action tanpa variabel menumpuk
                        action_thought = computed_action.get("thought", "Executing strategic action.") if computed_action else "None"

                        # Mengirimkan seluruh data telemetri taktis baru ke TerminalRenderer
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
                            location_planning=parsed_state["location_planning"],  # Membaca langsung dari parsed_state
                            action_thought=action_thought,
                            deadzone_status=parsed_state["deadzone_status"],
                            deadzone_warning=parsed_state["deadzone_warning"],
                            layer0=parsed_state["layer0"],
                            layer1=parsed_state["layer1"],
                            layer2=parsed_state["layer2"],
                            active_pack=parsed_state["active_pack"],
                            weather=parsed_state["weather"],
                            can_act=self.can_act,
                            cooldown_ms=self.cooldown_remaining_ms,
                            alert_gauge=parsed_state["alert_gauge"],
                            alert_active=parsed_state["alert_active"],
                            recent_messages=parsed_state["recent_messages"],
                            target_hp_info=parsed_state["target_hp_info"],
                            agent_name=self.agent_name
                        )

                        logger.info(f"[{self.agent_name}] Enemy stats scan: SUCCESSFUL")

                        if not self.initial_status_logged:
                            self.initial_status_logged = True
                            self.is_alive = server_is_alive
                            if not server_is_alive:
                                logger.warning(f"[{self.agent_name}] Agent is connected in a DEAD state. Terminating monitor for testing rejoin...")
                                self._is_active = False
                                break
                        else:
                            if not server_is_alive and self.is_alive:
                                self.is_alive = False
                                logger.warning(f"[{self.agent_name}] Agent has been eliminated! (HP: {parsed_state['hp']}). Terminating monitor for testing rejoin...")
                                self._is_active = False
                                break

                elif msg_type == "game_ended":
                    logger.info(f"[{self.agent_name}] The match has fully ended.")
                    self._is_active = False
                    break
                
                elif msg_type == "error":
                    logger.error(f"[{self.agent_name}] Server Error: {data.get('message')}")
                    break

        except websockets.exceptions.ConnectionClosed:
            logger.warning(f"[{self.agent_name}] Connection to battle arena closed by server.")
        except Exception as e:
            logger.error(f"[{self.agent_name}] Error during battle monitoring: {str(e)}")
        finally:
            self._is_active = False

    def stop(self):
        self._is_active = False