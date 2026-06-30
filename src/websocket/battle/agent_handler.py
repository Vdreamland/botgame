import asyncio
import json
import websockets
import re
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
        self.last_rendered_turn = -1
        self.last_location_id = ""
        self.is_alive = True
        self.initial_status_logged = False
        self.action_sent_this_turn = False
        self.last_view = {}
        self.opponents_data = {"players": [], "monsters": []}
        self.context = GameContext()
        self.brain = DecisionEngine()
        
        self.can_act = True
        self.cooldown_remaining_ms = 0
        self.last_computed_action = None

    async def send_json(self, payload: dict):
        try:
            await self.socket.send(json.dumps(payload))
        except Exception:
            pass

    def _deep_scan_deadzones(self, data: dict) -> list:
        found_ids = []
        messages = data.get("view", {}).get("recentMessages", [])
        for msg in messages:
            text = msg.get("text", "").lower() if isinstance(msg, dict) else str(msg).lower()
            if "death" in text or "zone" in text or "incoming" in text:
                matches = re.findall(r'[0-9a-f]{8}', text)
                found_ids.extend(matches)
        return list(set(found_ids))

    async def _process_and_render(self, data: dict, msg_type: str):
        view = data.get("view", {})
        if not view: return

        self.last_view = view
        view_self = view.get("self", {})
        self.is_alive = view_self.get("isAlive", True)
        self.current_turn = data.get("turn", self.current_turn)
        
        current_region = view.get("currentRegion", {})
        region_id = current_region.get("id", "")
        
        if self.agent_name and region_id:
            settings.BOT_POSITIONS[self.agent_name] = region_id

        detected_deadzones = self._deep_scan_deadzones(data)
        standard_pending = data.get("pendingDeathzones") or data.get("pendingDeathZones") or view.get("pendingDeathzones") or []
        combined_deadzones = list(set(detected_deadzones + [z.get("id") if isinstance(z, dict) else z for z in standard_pending]))
        
        self.context.update_map(current_region, combined_deadzones)
        self.context.opponents_data = ThreatEvaluator.scan_detailed_opponents(view, view_self.get("id", ""))

        if self.is_alive and self.can_act and not self.action_sent_this_turn:
            computed_action = self.brain.compute_action(view, self.context)
            if computed_action:
                self.last_computed_action = computed_action
                action_data = computed_action.get("data", {})
                action_type = action_data.get("type")
                if action_type in ["move", "explore", "attack", "use_item", "interact", "rest"]:
                    self.action_sent_this_turn = True
                await self.send_json(computed_action)
                
                thought = computed_action.get("thought", "Executing tactical move.")
                logger.info(f"[{self.agent_name}] Action Triggered: {action_type.upper()} | Reason: {thought}")

        # LOGIKA RENDER BERSIH: Dasbor hanya dicetak jika turn berganti atau bot baru saja melangkah (Ganti Lokasi)
        should_render = (self.current_turn != self.last_rendered_turn) or (region_id != self.last_location_id)
        
        if should_render and self.is_alive:
            self.last_rendered_turn = self.current_turn
            self.last_location_id = region_id
            
            parsed_state = StateParser.parse(view, self.context, self.last_computed_action, False)
            action_thought = self.last_computed_action.get("thought", "None") if self.last_computed_action else "None"
            
            if not self.can_act and not self.action_sent_this_turn:
                action_thought = f"Waiting for cooldown ({self.cooldown_remaining_ms}ms)..."

            TerminalRenderer.render_turn(
                turn=self.current_turn,
                server_is_alive=self.is_alive,
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

    async def start_monitoring(self):
        logger.info(f"Battle monitor active for [ {self.agent_name} ]. Synchronizing with arena...")
        
        try:
            while self._is_active:
                message = await self.socket.recv()
                data = json.loads(message)
                msg_type = data.get("type")

                if msg_type == "waiting":
                    continue
                    
                elif msg_type == "action_result":
                    self.can_act = data.get("canAct", True)
                    self.cooldown_remaining_ms = data.get("cooldownRemainingMs", 0)
                    
                elif msg_type == "can_act_changed":
                    self.can_act = data.get("canAct", True)
                    self.cooldown_remaining_ms = 0
                    if not self.action_sent_this_turn and self.last_view:
                        # Langsung proses tanpa mencetak log 'Cooldown finished' yang menumpuk
                        await self._process_and_render({"view": self.last_view, "turn": self.current_turn}, "cooldown_refresh")

                elif msg_type in ["agent_view", "turn_advanced"]:
                    if msg_type == "turn_advanced":
                        self.action_sent_this_turn = False
                        self.last_computed_action = None
                    
                    await self._process_and_render(data, msg_type)

                    if not self.is_alive:
                        logger.warning(f"[{self.agent_name}] Agent has been eliminated! Terminating monitor...")
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
            logger.warning(f"[{self.agent_name}] Connection closed.")
        except Exception as e:
            logger.error(f"[{self.agent_name}] Monitor Error: {str(e)}")
        finally:
            self._is_active = False

    def stop(self):
        self._is_active = False