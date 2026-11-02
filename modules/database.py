"""
database.py — SQLite database operations for the Food Calorie Estimation System.
Handles initialization, CRUD for meal logs, and settings persistence.
"""

import sqlite3
import os
from datetime import date, datetime
from typing import Optional

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "food_tracker.db")


def get_connection() -> sqlite3.Connection:
    """Return a SQLite connection with row_factory set."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Initialize all database tables if they do not already exist."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS meals (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                meal_date   TEXT    NOT NULL,
                food_name   TEXT    NOT NULL,
                serving_g   REAL    NOT NULL,
                calories    REAL    NOT NULL,
                protein     REAL    NOT NULL,
                carbs       REAL    NOT NULL,
                fat         REAL    NOT NULL,
                created_at  TEXT    NOT NULL DEFAULT (datetime('now', 'localtime'))
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key     TEXT PRIMARY KEY,
                value   TEXT NOT NULL
            )
        """)
        # Default settings
        cur.execute("""
            INSERT OR IGNORE INTO settings (key, value) VALUES ('daily_calorie_target', '2000')
        """)
        conn.commit()


# ─── Meal CRUD ───────────────────────────────────────────────────────────────

def add_meal(meal_date: str, food_name: str, serving_g: float,
             calories: float, protein: float, carbs: float, fat: float) -> int:
    """Insert a new meal record. Returns the new row id."""
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO meals (meal_date, food_name, serving_g, calories, protein, carbs, fat)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (meal_date, food_name, round(serving_g, 1), round(calories, 1),
              round(protein, 1), round(carbs, 1), round(fat, 1)))
        conn.commit()
        return cur.lastrowid


def get_meals_for_date(meal_date: str) -> list[dict]:
    """Return all meals for a given date string (YYYY-MM-DD)."""
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT id, meal_date, food_name, serving_g, calories, protein, carbs, fat, created_at
            FROM meals WHERE meal_date = ? ORDER BY created_at ASC
        """, (meal_date,))
        return [dict(row) for row in cur.fetchall()]


def get_meals_for_range(start_date: str, end_date: str) -> list[dict]:
    """Return meals between two date strings inclusive."""
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT id, meal_date, food_name, serving_g, calories, protein, carbs, fat, created_at
            FROM meals WHERE meal_date BETWEEN ? AND ? ORDER BY meal_date ASC, created_at ASC
        """, (start_date, end_date))
        return [dict(row) for row in cur.fetchall()]


def update_meal(meal_id: int, food_name: str, serving_g: float,
                calories: float, protein: float, carbs: float, fat: float) -> bool:
    """Update an existing meal record. Returns True on success."""
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            UPDATE meals SET food_name=?, serving_g=?, calories=?, protein=?, carbs=?, fat=?
            WHERE id=?
        """, (food_name, round(serving_g, 1), round(calories, 1),
              round(protein, 1), round(carbs, 1), round(fat, 1), meal_id))
        conn.commit()
        return cur.rowcount > 0


def delete_meal(meal_id: int) -> bool:
    """Delete a meal record. Returns True on success."""
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM meals WHERE id = ?", (meal_id,))
        conn.commit()
        return cur.rowcount > 0


def get_daily_totals(meal_date: str) -> dict:
    """Return summed calories and macros for a given date."""
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT
                COALESCE(SUM(calories), 0) AS total_calories,
                COALESCE(SUM(protein), 0)  AS total_protein,
                COALESCE(SUM(carbs), 0)    AS total_carbs,
                COALESCE(SUM(fat), 0)      AS total_fat,
                COUNT(*) AS meal_count
            FROM meals WHERE meal_date = ?
        """, (meal_date,))
        row = cur.fetchone()
        return dict(row) if row else {
            "total_calories": 0.0, "total_protein": 0.0,
            "total_carbs": 0.0, "total_fat": 0.0, "meal_count": 0
        }


def get_weekly_totals(start_date: str, end_date: str) -> list[dict]:
    """Return per-day calorie totals for a date range."""
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT meal_date,
                   COALESCE(SUM(calories), 0) AS total_calories,
                   COALESCE(SUM(protein), 0)  AS total_protein,
                   COALESCE(SUM(carbs), 0)    AS total_carbs,
                   COALESCE(SUM(fat), 0)      AS total_fat,
                   COUNT(*) AS meal_count
            FROM meals
            WHERE meal_date BETWEEN ? AND ?
            GROUP BY meal_date ORDER BY meal_date ASC
        """, (start_date, end_date))
        return [dict(row) for row in cur.fetchall()]


def clear_all_meals() -> None:
    """Delete all meal records (used for demo reset)."""
    with get_connection() as conn:
        conn.execute("DELETE FROM meals")
        conn.commit()


# ─── Settings ────────────────────────────────────────────────────────────────

def get_setting(key: str, default: str = "") -> str:
    """Retrieve a setting value by key."""
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT value FROM settings WHERE key = ?", (key,))
        row = cur.fetchone()
        return row["value"] if row else default


def set_setting(key: str, value: str) -> None:
    """Insert or update a setting value."""
    with get_connection() as conn:
        conn.execute("""
            INSERT INTO settings (key, value) VALUES (?, ?)
            ON CONFLICT(key) DO UPDATE SET value = excluded.value
        """, (key, value))
        conn.commit()
