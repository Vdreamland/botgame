# -*- coding: utf-8 -*-
"""
ClawRoyale Weather and Terrain Tactical Calculator.
Modifies path costs and attack multipliers based on current environmental conditions.
"""

from typing import Dict, Any, Tuple
from config.game_constants import TERRAIN_MODIFIERS, WEATHER_EFFECTS
from core.state.game_state import GameState


class WeatherTerrainHandler:
    def __init__(self, game_state: GameState):
        self.game_state = game_state

    def get_movement_ep_cost(self, target_terrain_type: str) -> float:
        """
        Calculates the real EP cost multiplier for moving onto a specific terrain.
        Example: Swamp multiplier is 1.8x, Glacier is 1.5x.
        """
        modifier = TERRAIN_MODIFIERS.get(target_terrain_type.lower(), {})
        # Jika terrain tidak terdaftar, asumsikan biaya dasar (1.0x)
        return float(modifier.get("ep_cost_multiplier", 1.0))

    def get_defensive_modifier(self, terrain_type: str) -> float:
        """
        Returns the absolute defense bonus or penalty granted by the terrain type.
        Example: Forest grants +3.0 DEF, Swamp gives -2.0 DEF.
        """
        modifier = TERRAIN_MODIFIERS.get(terrain_type.lower(), {})
        return float(modifier.get("def_bonus", 0.0))

    def calculate_effective_attack(self, base_attack: float) -> Tuple[float, float]:
        """
        Modifies attack power and sight range based on current active weather effects.
        Example: Storm weather cuts ATK to 70% and limits visual range to 1 hex.
        :return: Tuple of (effective_attack_value, visual_range_limit)
        """
        weather = self.game_state.current_weather.lower()
        effects = WEATHER_EFFECTS.get(weather, {"atk_multiplier": 1.0, "visibility_radius": 3.0})

        multiplier = float(effects.get("atk_multiplier", 1.0))
        visibility = float(effects.get("visibility_radius", 3.0))

        return base_attack * multiplier, visibility