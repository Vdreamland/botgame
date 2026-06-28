# -*- coding: utf-8 -*-
"""
ClawRoyale ASCII Map Renderer.
Converts Hexagonal coordinates (q, r) into a readable terminal string [8].
"""

from typing import Dict, Any, List, Tuple
from core.state.game_state import GameState


class ASCIIMapRenderer:
    @staticmethod
    def render_local_map(game_state: GameState, view_radius: int = 3) -> str:
        """
        Draws a visual hexagonal grid representing the agent's nearby surroundings.
        Symbols:
        [ P ] = Agent (Self)
        [ E ] = Enemy Player
        [ A ] = Ally Bot
        [ * ] = Items on ground
        [ . ] = Empty hex
        """
        bot_q, bot_r = game_state.q, game_state.r
        grid: Dict[Tuple[int, int], str] = {}

        # 1. Daftarkan diri bot di koordinat pusat
        grid[(0, 0)] = "[ P ]"

        # 2. Daftarkan musuh-musuh asing
        for enemy in game_state.enemies:
            eq = int(enemy.get("q", 0)) - bot_q
            er = int(enemy.get("r", 0)) - bot_r
            grid[(eq, er)] = "[ E ]"

        # 3. Daftarkan sekutu bot kita
        for ally in game_state.allies_nearby:
            aq = int(ally.get("q", 0)) - bot_q
            ar = int(ally.get("r", 0)) - bot_r
            grid[(aq, ar)] = "[ A ]"

        # 4. Daftarkan item di tanah
        for item in game_state.items_on_ground:
            iq = int(item.get("q", 0)) - bot_q
            ir = int(item.get("r", 0)) - bot_r
            # Cegah penindihan jika ada player berdiri di atas item
            if (iq, ir) not in grid:
                grid[(iq, ir)] = "[ * ]"

        # 5. Susun format visual string heksagonal axial
        lines = []
        for r in range(-view_radius, view_radius + 1):
            # Indentasi heksagonal agar membentuk grid hex murni
            indent = "   " * abs(r)
            line_parts = []
            
            for q in range(-view_radius, view_radius + 1):
                # Validasi jangkauan heksagonal axial (abs(q + r) <= radius)
                if abs(q + r) <= view_radius:
                    symbol = grid.get((q, r), "[ . ]")
                    line_parts.append(symbol)
            
            if line_parts:
                lines.append(f"{indent}{' '.join(line_parts)}")

        return "\n".join(lines)