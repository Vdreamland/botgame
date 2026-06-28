# -*- coding: utf-8 -*-
"""
ClawRoyale Multi-Agent Terminal Dashboard (TUI).
Builds an Elite PowerShell dashboard containing tables and map grids.
Logs are completely excluded from the console to prevent Windows crash.
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
        
        # AKTIFKAN DUKUNGAN ANSI/VT100 SECARA NATIVE PADA POWERSHELL WINDOWS [8]
        # Ini menghentikan cetakan '←[H' liar dan menghentikan kedipan layar secara mutlak!
        if os.name == 'nt':
            try:
                import ctypes
                kernel32 = ctypes.windll.kernel32
                # -11 = STD_OUTPUT_HANDLE
                # 7 = ENABLE_VIRTUAL_TERMINAL_PROCESSING | ENABLE_PROCESSED_OUTPUT
                kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
            except Exception:
                pass

    def draw_dashboard(self, active_instances: List[AgentInstance]) -> None:
        """
        Renders the elite visual dashboard with hex map.
        Uses cursor-home sequence to prevent PowerShell flickering completely.
        """
        # Pindahkan kursor kembali ke pojok kiri atas secara instan (Flicker-Free Overwrite)
        # Berkat inisialisasi VT100 di __init__, ini tidak akan mencetak '←[H' lagi di Windows!
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

        # 3. Cetak Komponen Bersih ke Terminal (LOG FEED DIHAPUS TOTAL)
        self.console.print(Panel("[bold white]CLAWROYALE MULTI-BOT SYSTEM MONITOR v1.11.2[/bold white]", style="blue"), justify="center")
        self.console.print(Panel(summary_table, title="Active Bots Registry", border_style="cyan"))
        self.console.print(map_panel)
        self.console.print("[dim white]Press CTRL+C to safely exit and disconnect all bots.[/dim white]", justify="center")