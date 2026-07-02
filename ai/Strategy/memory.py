_visited_regions = []

def mark_visited(region_id: str):
    global _visited_regions
    if not region_id:
        return
    if region_id in _visited_regions:
        _visited_regions.remove(region_id)
    _visited_regions.append(region_id)
    if len(_visited_regions) > 5:
        _visited_regions.pop(0)

def get_visit_count(region_id: str) -> int:
    global _visited_regions
    return _visited_regions.count(region_id)

def get_visited_history() -> list:
    global _visited_regions
    return list(_visited_regions)

def clear_memory():
    global _visited_regions
    _visited_regions = []