_visited_regions = []
_death_spots = set()
_known_dead_zones = {}
_map_connections = {}

def mark_visited(region_id: str):
    global _visited_regions, _death_spots
    if not region_id:
        return
    if region_id in _visited_regions:
        _visited_regions.remove(region_id)
    _visited_regions.append(region_id)
    if len(_visited_regions) > 5:
        _visited_regions.pop(0)
    if region_id in _death_spots:
        _death_spots.remove(region_id)

def get_visit_count(region_id: str) -> int:
    global _visited_regions
    return _visited_regions.count(region_id)

def mark_death_spot(region_id: str):
    global _death_spots
    if region_id:
        _death_spots.add(region_id)

def is_death_spot(region_id: str) -> bool:
    global _death_spots
    return region_id in _death_spots

def mark_dead_zone(region_id: str, region_name: str):
    global _known_dead_zones
    if region_id and region_name:
        _known_dead_zones[region_id] = region_name

def is_known_dead_zone(region_id: str) -> bool:
    global _known_dead_zones
    return region_id in _known_dead_zones

def get_all_known_dead_zones() -> dict:
    global _known_dead_zones
    return dict(_known_dead_zones)

def record_map_connections(region_id: str, connections: list):
    global _map_connections
    if region_id and isinstance(connections, list):
        _map_connections[region_id] = list(connections)

def get_region_connections(region_id: str) -> list:
    global _map_connections
    return _map_connections.get(region_id, [])

def get_visited_history() -> list:
    global _visited_regions
    return list(_visited_regions)

def clear_memory():
    global _visited_regions, _death_spots, _known_dead_zones, _map_connections
    _visited_regions = []
    _death_spots = set()
    _known_dead_zones = {}
    _map_connections = {}