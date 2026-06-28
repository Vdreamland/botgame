# -*- coding: utf-8 -*-
"""
ClawRoyale ASCII Map Renderer.
Converts Region connections and adjacent entities into a readable terminal graph [8].
"""

from typing import Dict, Any, List, Tuple
from core.state.game_state import GameState


class ASCIIMapRenderer:
    @staticmethod
    def render_local_map(game_state: GameState, view_radius: int = 3) -> str:
        """
        Draws a visual connectivity graph representing the agent's adjacent surroundings.
        Symbols:
          [ P ] = Agent (Self)
          (E)   = Enemy Present
          (*)   = Items on ground
        """
        lines = []
        
        current_name = game_state.current_region_name
        current_id = game_state.current_region_id
        
        # Cari musuh di ruangan sendiri
        enemies_here = [e.get("name") for e in game_state.enemies if (e.get("regionId") or game_state.current_region_id) == current_id]
        items_count = len(game_state.items_on_ground)
        
        self_status = ""
        if enemies_here:
            self_status += f" [bold red](E: {len(enemies_here)} enemies here!)[/bold red]"
        if items_count > 0:
            self_status += f" [bold green](*: {items_count} items on ground)[/bold green]"

        # Gambar Node Pusat (Tempat Bot berdiri)
        lines.append(" [bold yellow]============================================================[/bold yellow]")
        lines.append(f"  CURRENT REGION: [bold white]{current_name}[/bold white] ({current_id[:18]}...) {self_status}")
        lines.append(" [bold yellow]============================================================[/bold yellow]")
        lines.append("        |")
        lines.append("        +--- ADJACENT CONNECTED REGIONS:")

        # Gambar Node Tetangga (Koneksi aktif)
        connections = game_state.connections
        if not connections:
            lines.append("             [ No connections detected ]")
        else:
            for conn_id in connections:
                # Terjemahkan UUID koneksi ke nama manusiawi secara real-time
                resolved_conn_name = game_state.get_region_name(conn_id)

                # Cari musuh di region tetangga ini
                enemies_there = [e.get("name") for e in game_state.enemies if e.get("regionId") == conn_id]
                status_suffix = ""
                if enemies_there:
                    status_suffix += f" [bold red](E: {len(enemies_there)} enemies present)[/bold red]"
                
                # Cek jika ada ruins di tetangga ini
                is_ruins = False
                for r in game_state.visible_ruins:
                    if r.get("ruinId") == conn_id:
                        is_ruins = True
                        break
                if is_ruins:
                    status_suffix += " [bold gold][ Ruins ][/bold gold]"

                lines.append(f"             |--- [cyan]{resolved_conn_name}[/cyan] ({conn_id[:8]}...) {status_suffix}")

        lines.append(" [bold yellow]============================================================[/bold yellow]")
        return "\n".join(lines)