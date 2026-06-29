from typing import Dict, Any
from config.game_data import TERRAIN, WEATHER
from src.strategy.brain.game_context import GameContext

class WeightMap:
    
    @staticmethod
    def calculate_weight(region: Dict[str, Any], context: GameContext, weather_type: str = "clear") -> float:
        region_id = region.get("id")
        
        if not region_id:
            return float('inf')
            
        if region_id in context.pending_deathzones or region_id in context.active_deathzones:
            return float('inf')
            
        terrain_type = region.get("terrain", "plains")
        static_terrain = TERRAIN.get(terrain_type, {"vision_modifier": 0, "extra_ep": 0})
        static_weather = WEATHER.get(weather_type, {"vision_modifier": 0, "extra_ep": 0})
        
        base_cost = 1.0
        extra_ep = static_terrain.get("extra_ep", 0) + static_weather.get("extra_ep", 0)
        
        return base_cost + float(extra_ep)