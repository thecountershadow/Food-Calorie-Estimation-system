"""
test_suite.py — Automated tests for the Food Calorie Estimation System.
Run: python -m pytest tests/test_suite.py -v
  or: python tests/test_suite.py  (standalone)
"""

import sys
import os
import io
import json
import tempfile
import unittest
from datetime import date, timedelta
from unittest.mock import patch, MagicMock

# Make sure root is on path
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from modules.nutrition import (
    load_food_db, get_food_by_key, calculate_nutrition,
    search_foods, get_macro_percentages, find_food_by_name,
)
from modules.food_classifier import (
    validate_image, preprocess_image, _map_label, CONFIDENCE_THRESHOLD,
)


# ─── Use an in-memory test database ──────────────────────────────────────────

import modules.database as db_module

_ORIGINAL_DB_PATH = db_module.DB_PATH


def _use_temp_db():
    """Redirect DB_PATH to a temporary file for tests."""
    tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    tmp.close()
    db_module.DB_PATH = tmp.name
    db_module.init_db()
    return tmp.name


def _restore_db(tmp_path: str):
    db_module.DB_PATH = _ORIGINAL_DB_PATH
    try:
        os.unlink(tmp_path)
    except Exception:
        pass


# ════════════════════════════════════════════════════════════════════════════
# 1. Nutrition tests
# ════════════════════════════════════════════════════════════════════════════

class TestNutritionCalculations(unittest.TestCase):

    def test_load_food_db_returns_dict(self):
        db = load_food_db()
        self.assertIsInstance(db, dict)
        self.assertGreater(len(db), 0)

    def test_all_required_foods_present(self):
        """Every required food key must exist in the database."""
        required = ["idli", "dosa", "plain_rice", "biryani", "chapati", "dal",
                    "paneer_curry", "samosa", "poha", "upma", "chicken_curry",
                    "salad", "pizza", "burger", "pasta", "sandwich",
                    "apple", "banana", "eggs"]
        db = load_food_db()
        for key in required:
            self.assertIn(key, db, f"Missing required food key: {key}")

    def test_food_has_required_fields(self):
        db = load_food_db()
        for key, food in db.items():
            for field in ["name", "calories_per_100g", "protein_per_100g",
                          "carbs_per_100g", "fat_per_100g",
                          "serving_description", "default_serving_g"]:
                self.assertIn(field, food, f"{key} missing field: {field}")

    def test_calculate_nutrition_100g(self):
        food = get_food_by_key("plain_rice")
        self.assertIsNotNone(food)
        n = calculate_nutrition(food, 100.0)
        self.assertAlmostEqual(n["calories"], food["calories_per_100g"], places=1)
        self.assertAlmostEqual(n["protein"],  food["protein_per_100g"],  places=1)
        self.assertAlmostEqual(n["carbs"],    food["carbs_per_100g"],    places=1)
        self.assertAlmostEqual(n["fat"],      food["fat_per_100g"],      places=1)

    def test_calculate_nutrition_proportional(self):
        food = get_food_by_key("plain_rice")
        n200 = calculate_nutrition(food, 200.0)
        n100 = calculate_nutrition(food, 100.0)
        self.assertAlmostEqual(n200["calories"], n100["calories"] * 2, places=1)
        self.assertAlmostEqual(n200["protein"],  n100["protein"]  * 2, places=1)

    def test_calculate_nutrition_zero_serving(self):
        food = get_food_by_key("apple")
        n = calculate_nutrition(food, 0)
        self.assertEqual(n["calories"], 0.0)

    def test_calculate_nutrition_idli_40g(self):
        food = get_food_by_key("idli")
        n = calculate_nutrition(food, 40.0)
        expected_cal = round(food["calories_per_100g"] * 40 / 100, 1)
        self.assertAlmostEqual(n["calories"], expected_cal, places=1)

    def test_calculate_nutrition_pizza_slice(self):
        food = get_food_by_key("pizza")
        n = calculate_nutrition(food, 100.0)
        self.assertAlmostEqual(n["calories"], 266.0, places=0)
        self.assertAlmostEqual(n["protein"],  11.0,  places=0)

    def test_macro_percentages_sum_to_100(self):
        nutrition = {"calories": 400, "protein": 20, "carbs": 50, "fat": 10}
        pct = get_macro_percentages(nutrition)
        total = pct["protein_pct"] + pct["carbs_pct"] + pct["fat_pct"]
        self.assertAlmostEqual(total, 100.0, places=0)

    def test_macro_percentages_zero(self):
        nutrition = {"calories": 0, "protein": 0, "carbs": 0, "fat": 0}
        pct = get_macro_percentages(nutrition)
        self.assertEqual(pct["protein_pct"], 0)

    def test_search_foods_finds_pizza(self):
        results = search_foods("pizza")
        keys = [k for k, _ in results]
        self.assertIn("pizza", keys)

    def test_search_foods_empty_query_returns_all(self):
        db = load_food_db()
        results = search_foods("")
        self.assertEqual(len(results), len(db))

    def test_find_food_by_name_case_insensitive(self):
        result = find_food_by_name("APPLE")
        self.assertIsNotNone(result)
        key, _ = result
        self.assertEqual(key, "apple")

    def test_find_food_by_name_unknown(self):
        result = find_food_by_name("XYZ Unknown Food 12345")
        self.assertIsNone(result)


# ════════════════════════════════════════════════════════════════════════════
# 2. Database tests
# ════════════════════════════════════════════════════════════════════════════

class TestDatabase(unittest.TestCase):

    def setUp(self):
        self._tmp = _use_temp_db()

    def tearDown(self):
        _restore_db(self._tmp)

    def test_init_db_creates_tables(self):
        import sqlite3
        conn = sqlite3.connect(db_module.DB_PATH)
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = {row[0] for row in cur.fetchall()}
        conn.close()
        self.assertIn("meals", tables)
        self.assertIn("settings", tables)

    def test_default_calorie_target(self):
        val = db_module.get_setting("daily_calorie_target", "2000")
        self.assertEqual(val, "2000")

    def test_set_and_get_setting(self):
        db_module.set_setting("daily_calorie_target", "1800")
        val = db_module.get_setting("daily_calorie_target")
        self.assertEqual(val, "1800")

    def test_add_and_retrieve_meal(self):
        today = date.today().isoformat()
        mid = db_module.add_meal(today, "Apple", 182, 94.6, 0.5, 25.5, 0.4)
        self.assertIsInstance(mid, int)
        meals = db_module.get_meals_for_date(today)
        self.assertEqual(len(meals), 1)
        self.assertEqual(meals[0]["food_name"], "Apple")
        self.assertAlmostEqual(meals[0]["calories"], 94.6, places=1)

    def test_daily_totals_empty(self):
        totals = db_module.get_daily_totals("2000-01-01")
        self.assertEqual(totals["total_calories"], 0.0)
        self.assertEqual(totals["meal_count"], 0)

    def test_daily_totals_with_meals(self):
        today = date.today().isoformat()
        db_module.add_meal(today, "Banana", 118, 105.0, 1.3, 27.1, 0.4)
        db_module.add_meal(today, "Eggs",   100, 155.0, 13.0, 1.1, 11.0)
        totals = db_module.get_daily_totals(today)
        self.assertAlmostEqual(totals["total_calories"], 260.0, places=0)
        self.assertEqual(totals["meal_count"], 2)

    def test_update_meal(self):
        today = date.today().isoformat()
        mid = db_module.add_meal(today, "Pizza", 100, 266.0, 11.0, 33.0, 10.0)
        success = db_module.update_meal(mid, "Pizza", 200, 532.0, 22.0, 66.0, 20.0)
        self.assertTrue(success)
        meals = db_module.get_meals_for_date(today)
        self.assertAlmostEqual(meals[0]["calories"], 532.0, places=1)
        self.assertAlmostEqual(meals[0]["serving_g"], 200.0, places=1)

    def test_delete_meal(self):
        today = date.today().isoformat()
        mid = db_module.add_meal(today, "Samosa", 70, 183.4, 4.1, 22.4, 8.4)
        success = db_module.delete_meal(mid)
        self.assertTrue(success)
        meals = db_module.get_meals_for_date(today)
        self.assertEqual(len(meals), 0)

    def test_delete_nonexistent_meal(self):
        success = db_module.delete_meal(99999)
        self.assertFalse(success)

    def test_no_duplicate_on_save(self):
        """Calling add_meal twice creates two distinct records, not one duplicate."""
        today = date.today().isoformat()
        db_module.add_meal(today, "Dal", 200, 232.0, 15.2, 34.0, 4.4)
        db_module.add_meal(today, "Dal", 200, 232.0, 15.2, 34.0, 4.4)
        meals = db_module.get_meals_for_date(today)
        self.assertEqual(len(meals), 2)

    def test_clear_all_meals(self):
        today = date.today().isoformat()
        db_module.add_meal(today, "Dosa", 100, 133.0, 3.9, 23.2, 3.0)
        db_module.clear_all_meals()
        meals = db_module.get_meals_for_date(today)
        self.assertEqual(len(meals), 0)

    def test_weekly_totals(self):
        today = date.today().isoformat()
        yesterday = (date.today() - timedelta(days=1)).isoformat()
        db_module.add_meal(today, "Idli", 40, 23.2, 0.8, 4.4, 0.2)
        db_module.add_meal(yesterday, "Upma", 200, 200.0, 5.2, 33.0, 5.6)
        rows = db_module.get_weekly_totals(yesterday, today)
        self.assertEqual(len(rows), 2)


# ════════════════════════════════════════════════════════════════════════════
# 3. Image validation tests
# ════════════════════════════════════════════════════════════════════════════

class TestImageValidation(unittest.TestCase):

    def _make_png_bytes(self) -> bytes:
        """Create a minimal valid PNG image as bytes."""
        from PIL import Image
        img = Image.new("RGB", (64, 64), color=(200, 100, 50))
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()

    def test_valid_png_accepted(self):
        data = self._make_png_bytes()
        ok, msg = validate_image(data, "food.png")
        self.assertTrue(ok)
        self.assertEqual(msg, "")

    def test_invalid_extension_rejected(self):
        data = self._make_png_bytes()
        ok, msg = validate_image(data, "food.gif")
        self.assertFalse(ok)
        self.assertIn("gif", msg.lower())

    def test_too_large_rejected(self):
        data = b"x" * (11 * 1024 * 1024)  # 11 MB
        ok, msg = validate_image(data, "food.jpg")
        self.assertFalse(ok)
        self.assertIn("large", msg.lower())

    def test_corrupt_file_rejected(self):
        ok, msg = validate_image(b"not an image at all", "food.png")
        self.assertFalse(ok)

    def test_preprocess_returns_rgb(self):
        data = self._make_png_bytes()
        img = preprocess_image(data)
        self.assertEqual(img.mode, "RGB")
        self.assertIsInstance(img.size, tuple)
        self.assertEqual(len(img.size), 2)


# ════════════════════════════════════════════════════════════════════════════
# 4. Classifier label-mapping tests
# ════════════════════════════════════════════════════════════════════════════

class TestClassifierLabelMapping(unittest.TestCase):

    def test_known_label_mapped(self):
        self.assertEqual(_map_label("pizza"), "pizza")
        self.assertEqual(_map_label("hamburger"), "burger")
        self.assertEqual(_map_label("dosa"), "dosa")

    def test_unknown_label_returns_none(self):
        result = _map_label("xyzzy_unknown_dish_9999")
        self.assertIsNone(result)

    def test_keyword_partial_match(self):
        # "spaghetti_bolognese" should map via keyword "spaghetti" → pasta
        result = _map_label("spaghetti_bolognese")
        self.assertEqual(result, "pasta")

    def test_banana_keyword_match(self):
        result = _map_label("banana_foster")
        self.assertEqual(result, "banana")


# ════════════════════════════════════════════════════════════════════════════
# 5. Classifier fallback mode test
# ════════════════════════════════════════════════════════════════════════════

class TestClassifierFallback(unittest.TestCase):

    def test_fallback_when_model_unavailable(self):
        """When model loading fails, classify_image must return fallback_mode=True
           and never pretend success."""
        from PIL import Image
        import modules.food_classifier as fc
        # Temporarily force a failed load
        original_cache = fc._model_cache.copy()
        fc._model_cache = {"loaded": True, "ok": False,
                           "processor": None, "model": None, "labels": None}
        img = Image.new("RGB", (64, 64))
        result = fc.classify_image(img)
        fc._model_cache = original_cache  # restore

        self.assertFalse(result["success"])
        self.assertTrue(result["fallback_mode"])
        self.assertIsNone(result["top_food_key"])
        self.assertIsNotNone(result["error"])


# ════════════════════════════════════════════════════════════════════════════
# Runner
# ════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    loader  = unittest.TestLoader()
    suite   = loader.loadTestsFromModule(sys.modules[__name__])
    runner  = unittest.TextTestRunner(verbosity=2)
    result  = runner.run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)
