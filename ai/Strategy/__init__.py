from ai.Strategy.navigation_strategy import get_navigation_priorities
from ai.Strategy.ruin_exploration_strategy import get_exploration_priorities
from ai.Strategy.decision_maker import make_decision
from ai.Strategy.memory import (
    mark_visited,
    get_visit_count,
    mark_death_spot,
    is_death_spot,
    mark_dead_zone,
    is_known_dead_zone,
    get_all_known_dead_zones,
    get_visited_history,
    clear_memory
)