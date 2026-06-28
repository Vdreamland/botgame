# -*- coding: utf-8 -*-
"""
ClawRoyale Central Orchestrator.
Parses agent lists, spawns concurrent task loops, and renders UI monitors.
"""

import os
import json
import asyncio
from typing import List

from utils.logger import AgentLogger
from utils.rate_limiter import GlobalRateLimiter
from core.agent_instance import AgentInstance
from ui.terminal_dashboard import TerminalDashboard


class CentralOrchestrator:
    def __init__(self, config_file: str):
        self.config_file = config_file
        self.logger = AgentLogger.get_logger("orchestrator")
        self.limiter = GlobalRateLimiter()
        self.dashboard = TerminalDashboard()
        
        self.instances: List[AgentInstance] = []
        self._ui_task: Optional[asyncio.Task] = None

    def _load_agents_config(self) -> List[dict]:
        """Reads list of active accounts from config_agents.json."""
        if not os.path.exists(self.config_file):
            self.logger.critical(f"Config file '{self.config_file}' is missing!")
            return []
        
        try:
            with open(self.config_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("agents", [])
        except Exception as e:
            self.logger.critical(f"Failed to parse config_agents.json: {str(e)}")
            return []

    async def run_system(self) -> None:
        """
        Bootstraps all agent instances in parallel task loops and spawns TUI monitor.
        """
        agents_data = self._load_agents_config()
        if not agents_data:
            self.logger.error("No active agent profiles found to execute. Exiting.")
            return

        self.logger.info(f"Loaded {len(agents_data)} agent configurations. Spawning instances...")

        # 1. Instansiasi setiap Bot secara asinkron
        for agent in agents_data:
            name = agent.get("agent_name", "unknown")
            api_key = agent.get("api_key", "")
            private_key = agent.get("private_key", "")
            room_pref = agent.get("room_preference", "free")

            # Buat token bucket rate limiter instan khusus untuk WS bot ini [13]
            ws_bucket = self.limiter.create_ws_limiter()

            instance = AgentInstance(
                agent_name=name,
                api_key=api_key,
                private_key=private_key,
                room_preference=room_pref,
                rest_limiter=self.limiter.global_rest_limiter,
                ws_limiter=ws_bucket
            )
            self.instances.append(instance)

        # 2. Mulai eksekusi putaran hidup asinkron untuk masing-masing bot
        for inst in self.instances:
            await inst.start()

        # 3. Jalankan asinkron task untuk memperbarui Terminal Dashboard setiap 1 detik
        self._ui_task = asyncio.create_task(self._update_dashboard_loop())

        # Jaga proses utama tetap hidup selama agen aktif
        try:
            while True:
                await asyncio.sleep(1.0)
        except asyncio.CancelledError:
            pass
        finally:
            await self.shutdown_system()

    async def _update_dashboard_loop(self) -> None:
        """Runs infinite loop rendering the terminal dashboard periodically."""
        try:
            while True:
                await asyncio.sleep(1.0)
                self.dashboard.draw_dashboard(self.instances)
        except asyncio.CancelledError:
            pass
        except Exception as e:
            self.logger.error(f"Dashboard UI Loop crashed: {str(e)}")

    async def shutdown_system(self) -> None:
        """Safely shuts down all bots and tears down GUI tasks."""
        self.logger.warning("Shutting down Orchestrator System...")
        
        if self._ui_task:
            self._ui_task.cancel()
            self._ui_task = None
            
        for inst in self.instances:
            await inst.stop()
            
        self.logger.info("All bot sessions successfully disconnected. Goodbye!")