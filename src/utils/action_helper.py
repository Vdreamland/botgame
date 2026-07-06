def create_move_action(destination_id):
    return {
        "type": "action",
        "data": {
            "type": "move",
            "regionId": destination_id
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

def create_search_action():
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
            "type": "use_item",
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