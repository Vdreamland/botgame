def create_move_action(region_id):
    return {
        "type": "action",
        "data": {
            "type": "move",
            "regionId": region_id
        }
    }

def create_attack_action(target_id, target_type):
    return {
        "type": "action",
        "data": {
            "type": "attack",
            "targetId": target_id,
            "targetType": target_type
        }
    }

def create_loot_action(item_id):
    return {
        "type": "action",
        "data": {
            "type": "pickup",
            "itemId": item_id
        }
    }

def create_explore_action():
    return {
        "type": "action",
        "data": {
            "type": "explore"
        }
    }

def create_use_item_action(item_id):
    return {
        "type": "action",
        "data": {
            "type": "useItem",
            "itemId": item_id
        }
    }

def create_equip_action(item_id):
    return {
        "type": "action",
        "data": {
            "type": "equip",
            "itemId": item_id
        }
    }

def create_rest_action():
    return {
        "type": "action",
        "data": {
            "type": "rest"
        }
    }

def create_discard_action(item_id):
    return {
        "type": "action",
        "data": {
            "type": "drop",
            "itemId": item_id
        }
    }