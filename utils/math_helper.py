# -*- coding: utf-8 -*-
"""
ClawRoyale coordinate geometry and Utility-based AI math helper.
Handles axial coordinates (q, r) and mathematical scaling functions.
"""

import math
from typing import Tuple

def calculate_hex_distance(coord_a: Tuple[int, int], coord_b: Tuple[int, int]) -> int:
    """
    Calculates the exact distance between two hexagonal points in an axial coordinate system.
    Formula: (abs(dq) + abs(dr) + abs(dq + dr)) / 2
    """
    q1, r1 = coord_a
    q2, r2 = coord_b
    
    dq = q2 - q1
    dr = r2 - r1
    
    return int((abs(dq) + abs(dr) + abs(dq + dr)) / 2)

def calculate_euclidean_distance(pos_a: Tuple[float, float], pos_b: Tuple[float, float]) -> float:
    """
    Calculates standard straight-line distance, useful for threat vectors.
    """
    x1, y1 = pos_a
    x2, y2 = pos_b
    return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)

def normalize_utility_score(value: float, min_val: float, max_val: float) -> float:
    """
    Normalizes any tactical parameter into a standard utility rating of 0.0 to 1.0.
    Ensures safe bounded outputs for decision-making.
    """
    if max_val <= min_val:
        return 0.0
    
    # Bounding
    clamped_val = max(min_val, min(max_val, value))
    return (clamped_val - min_val) / (max_val - min_val)

def calculate_sigmoid_utility(value: float, midpoint: float, k: float) -> float:
    """
    Applies a sigmoid curve to prioritize values around a custom tactical threshold.
    Formula: 1 / (1 + e^(-k * (x - midpoint)))
    """
    try:
        exponent = -k * (value - midpoint)
        # Cegah overflow matematika pada perpangkatan eksponensial ekstrem
        if exponent > 700:
            return 0.0
        elif exponent < -700:
            return 1.0
        return 1.0 / (1.0 + math.exp(exponent))
    except OverflowError:
        return 0.0