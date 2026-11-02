"""
nutrition.py — Nutritional lookup and calculation module.
Loads food data from data/foods.json and provides calculation utilities.
"""

import json
import os
from typing import Optional

_FOODS_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "foods.json")
_FOOD_DB: dict = {}


def load_food_db() -> dict:
    """Load food database from JSON. Caches after first load."""
    global _FOOD_DB
    if _FOOD_DB:
        return _FOOD_DB
    if not os.path.exists(_FOODS_PATH):
        raise FileNotFoundError(f"Food database not found at: {_FOODS_PATH}")
    with open(_FOODS_PATH, "r", encoding="utf-8") as f:
        _FOOD_DB = json.load(f)
    return _FOOD_DB


def get_all_foods() -> dict:
    """Return the full food database."""
    return load_food_db()


def get_food_names() -> list[str]:
    """Return a sorted list of food display names."""
    db = load_food_db()
    return sorted(item["name"] for item in db.values())


def get_food_keys() -> list[str]:
    """Return a sorted list of food database keys."""
    db = load_food_db()
    return sorted(db.keys())


def get_food_by_key(key: str) -> Optional[dict]:
    """Retrieve a food entry by its database key."""
    db = load_food_db()
    return db.get(key)


def find_food_by_name(name: str) -> Optional[tuple[str, dict]]:
    """
    Search the database for a food by display name (case-insensitive).
    Returns (key, food_dict) or None.
    """
    db = load_food_db()
    name_lower = name.lower().strip()
    for key, item in db.items():
        if item["name"].lower() == name_lower:
            return key, item
    return None


def calculate_nutrition(food: dict, serving_g: float) -> dict:
    """
    Calculate nutritional values for a given serving weight in grams.

    Formula: nutrient_total = nutrient_per_100g * serving_g / 100

    Returns a dict with calories, protein, carbs, fat (all rounded to 1 dp).
    """
    if serving_g <= 0:
        return {"calories": 0.0, "protein": 0.0, "carbs": 0.0, "fat": 0.0}

    factor = serving_g / 100.0
    return {
        "calories": round(food["calories_per_100g"] * factor, 1),
        "protein":  round(food["protein_per_100g"]  * factor, 1),
        "carbs":    round(food["carbs_per_100g"]    * factor, 1),
        "fat":      round(food["fat_per_100g"]      * factor, 1),
    }


def search_foods(query: str) -> list[tuple[str, dict]]:
    """
    Case-insensitive substring search on food name and tags.
    Returns a list of (key, food_dict) tuples.
    """
    db = load_food_db()
    q = query.lower().strip()
    if not q:
        return [(k, v) for k, v in db.items()]
    results = []
    for key, item in db.items():
        name_match = q in item["name"].lower()
        tag_match  = any(q in t for t in item.get("tags", []))
        cat_match  = q in item.get("category", "").lower()
        if name_match or tag_match or cat_match:
            results.append((key, item))
    return results


def get_macro_percentages(nutrition: dict) -> dict:
    """
    Given a nutrition dict (calories, protein, carbs, fat),
    return the percentage of total calories from each macro.
    Protein and carbs = 4 kcal/g; fat = 9 kcal/g.
    """
    cal_from_protein = nutrition["protein"] * 4
    cal_from_carbs   = nutrition["carbs"]   * 4
    cal_from_fat     = nutrition["fat"]     * 9
    total_macro_cal  = cal_from_protein + cal_from_carbs + cal_from_fat

    if total_macro_cal == 0:
        return {"protein_pct": 0, "carbs_pct": 0, "fat_pct": 0}

    return {
        "protein_pct": round(cal_from_protein / total_macro_cal * 100, 1),
        "carbs_pct":   round(cal_from_carbs   / total_macro_cal * 100, 1),
        "fat_pct":     round(cal_from_fat     / total_macro_cal * 100, 1),
    } 