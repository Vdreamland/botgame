# -*- coding: utf-8 -*-
"""
ClawRoyale Multi-Agent Terminal Dashboard (TUI).
Builds an Elite PowerShell dashboard containing tables, map grids, action logs, and rolling logs.
"""

import os
from typing import List
from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table

from core.agent_instance import AgentInstance
from ui.ascii_map_renderer import ASCIIMapRenderer


class TerminalDashboard:
    def __init__(self):
        self.console = Console()
        self.layout = Layout()

    def _get_last_logs(self, filepath: str = "logs/system.log", count: int = 8) -> str:
        """
        Safely reads the last few lines of the system log to display on the terminal.
        """
        if not os.path.exists(filepath):
            return "No logs generated yet."
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                lines = f.readlines()
            return "".join(lines[-count:]).strip()
        except Exception:
            return "Failed to read logs dynamically."

    def draw_dashboard(self, active_instances: List[AgentInstance]) -> None:
        """
        Renders the elite visual dashboard with hex map and active log stream.
        """
        # Gunakan Escape Sequence ANSI untuk memindahkan kursor kembali ke pojok kiri atas
        # Ini mencegah layar PowerShell berkedip, bergetar, atau menumpuk teks ke bawah
        self.console.print("\033[H", end="")

        # 1. Tabel Registrasi Status Bot Aktif
        summary_table = Table(expand=True, border_style="cyan")
        summary_table.add_column("Agent Name", style="bold green")
        summary_table.add_column("Room Pref", justify="center")
        summary_table.add_column("HP State", justify="center")
        summary_table.add_column("EP State", justify="center")
        summary_table.add_column("Current Region", justify="center")
        summary_table.add_column("Alert", justify="center")
        summary_table.add_column("Active Action Status", style="bold yellow", justify="left")
        summary_table.add_column("Synergy", justify="center")

        for inst in active_instances:
            gs = inst.game_state
            
            hp_color = "green" if gs.hp > 60 else "yellow" if gs.hp > 35 else "red"
            ep_color = "green" if gs.ep > 7 else "yellow" if gs.ep > 3 else "red"
            
            hp_str = f"[{hp_color}]{gs.hp:.1f}%[/{hp_color}]"
            ep_str = f"[{ep_color}]{gs.ep:.1f} EP[/{ep_color}]"
            
            # Tampilkan Nama Wilayah Aktif di dalam tabel (bukan koordinat q, r yang membingungkan)
            region_str = f"{gs.current_region_name} ({gs.current_region_id[:8]}...)"
            alert_str = f"{gs.alert_gauge}/10"
            
            action_status_str = gs.current_action.upper()
            synergy_str = "RGB fullSet" if gs.has_full_set else "None"

            summary_table.add_row(
                inst.agent_name,
                inst.room_preference.upper(),
                hp_str,
                ep_str,
                region_str,
                alert_str,
                action_status_str,
                synergy_str
            )

        # 2. Mini Map Visual Graf Konektivitas Wilayah
        map_string = ""
        if active_instances:
            map_string = ASCIIMapRenderer.render_local_map(active_instances[0].game_state)
        
        map_panel = Panel(
            map_string,
            title=f"Region Connectivity Mini-Map (Active: {active_instances[0].agent_name if active_instances else 'None'})",
            border_style="yellow",
            expand=True
        )

        # 3. Live Log Feed Panel (Membaca logs/system.log sebanyak 8 baris terakhir secara real-time)
        last_logs_content = self._get_last_logs()
        log_panel = Panel(
            last_logs_content,
            title="Live Activity Log Feed",
            border_style="green",
            expand=True
        )

        # 4. Cetak Seluruh Komponen ke Terminal PowerShell
        self.console.print(Panel("[bold white]CLAWROYALE MULTI-BOT SYSTEM MONITOR v1.11.2[/bold white]", style="blue"), justify="center")
        self.console.print(Panel(summary_table, title="Active Bots Registry", border_style="cyan"))
        self.console.print(map_panel)
        self.console.print(log_panel)
        self.console.print("[dim white]Press CTRL+C to safely exit and disconnect all bots.[/dim white]", justify="center")