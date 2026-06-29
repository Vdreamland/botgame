from typing import Dict, Any, List, Optional
from src.strategy.brain.game_context import GameContext
from src.strategy.navigation.weight_map import WeightMap

class Pathfinder:
    
    @staticmethod
    def find_shortest_path(
        start_id: str, 
        target_id: str, 
        context: GameContext, 
        weather_type: str = "clear"
    ) -> Optional[List[str]]:
        if start_id == target_id:
            return [start_id]
            
        distances = {start_id: 0.0}
        previous = {}
        nodes = set(context.map_graph.keys())
        
        if start_id not in nodes or target_id not in nodes:
            return None

        while nodes:
            smallest = min(nodes, key=lambda node: distances.get(node, float('inf')))
            
            if smallest == target_id:
                path = []
                while smallest in previous:
                    path.insert(0, smallest)
                    smallest = previous[smallest]
                path.insert(0, start_id)
                return path
                
            if distances.get(smallest, float('inf')) == float('inf'):
                break
                
            nodes.remove(smallest)
            
            for neighbor in context.map_graph.get(smallest, []):
                if neighbor not in context.map_graph:
                    continue
                
                region_dummy = {"id": neighbor, "terrain": "plains"}
                weight = WeightMap.calculate_weight(region_dummy, context, weather_type)
                
                alt = distances[smallest] + weight
                if alt < distances.get(neighbor, float('inf')):
                    distances[neighbor] = alt
                    previous[neighbor] = smallest
                    
        return None