def create_move_action(destination_id):
    return {
        "type": "action",
        "data": {
            "actionType": "move",
            "params": {
                "destination": destination_id
            }
        }
    }

def create_attack_action(target_id):
    return {
        "type": "action",
        "data": {
            "actionType": "attack",
            "params": {
                "targetId": target_id
            }
        }
    }

def create_loot_action(item_id):
    return {
        "type": "action",
        "data": {
            "actionType": "loot",
            "params": {
                "itemId": item_id
            }
        }
    }

def create_search_action():
    return {
        "type": "action",
        "data": {
            "actionType": "search",
            "params": {}
        }
    }

def create_use_item_action(item_id):
    return {
        "type": "action",
        "data": {
            "actionType": "useItem",
            "params": {
                "itemId": item_id
            }
        }
    }

def create_equip_action(item_id):
    return {
        "type": "action",
        "data": {
            "actionType": "equip",
            "params": {
                "itemId": item_id
            }
        }
    }

def create_rest_action():
    return {
        "type": "action",
        "data": {
            "actionType": "rest",
            "params": {}
        }
    }