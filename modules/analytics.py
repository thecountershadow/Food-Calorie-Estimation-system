"""
analytics.py — Daily and weekly statistics aggregation for charts and summaries.
Wraps database queries and formats data for Plotly visualisations.
No pandas dependency — uses plain Python dicts and lists.
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Optional

import plotly.graph_objects as go

from modules.database import get_weekly_totals, get_daily_totals, get_meals_for_date

# ─── Colour palette ───────────────────────────────────────────────────────────
GREEN   = "#2ECC71"
ORANGE  = "#F39C12"
RED     = "#E74C3C"
BLUE    = "#3498DB"
PURPLE  = "#9B59B6"
BG      = "#0E1117"
CARD_BG = "#1A1F2E"
TEXT    = "#FAFAFA"
SUBTEXT = "#A0AEC0"


# ─── Weekly calorie chart ─────────────────────────────────────────────────────

def build_weekly_calorie_chart(target_calories: int = 2000, days: int = 7) -> go.Figure:
    """
    Bar chart of daily calorie intake for the last `days` days,
    with a dashed target line.
    """
    end   = date.today()
    start = end - timedelta(days=days - 1)

    rows = get_weekly_totals(start.isoformat(), end.isoformat())
    data_by_date = {r["meal_date"]: r for r in rows}

    dates, calories = [], []
    for i in range(days):
        d = (start + timedelta(days=i)).isoformat()
        dates.append(d)
        calories.append(data_by_date.get(d, {}).get("total_calories", 0))

    bar_colours = [GREEN if c <= target_calories else RED for c in calories]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=dates,
        y=calories,
        marker_color=bar_colours,
        name="Calories",
        hovertemplate="<b>%{x}</b><br>Calories: %{y:.0f} kcal<extra></extra>",
        text=[f"{c:.0f}" if c > 0 else "" for c in calories],
        textposition="outside",
        textfont=dict(color=TEXT, size=11),
    ))

    fig.add_hline(
        y=target_calories,
        line_dash="dash",
        line_color=ORANGE,
        annotation_text=f"Target: {target_calories} kcal",
        annotation_font_color=ORANGE,
    )

    fig.update_layout(
        title=dict(text="📊 Weekly Calorie Intake", font=dict(color=TEXT, size=16)),
        paper_bgcolor=CARD_BG,
        plot_bgcolor=CARD_BG,
        font=dict(color=SUBTEXT),
        xaxis=dict(
            title="Date",
            tickformat="%b %d",
            gridcolor="#2D3748",
            title_font=dict(color=SUBTEXT),
        ),
        yaxis=dict(
            title="Calories (kcal)",
            gridcolor="#2D3748",
            title_font=dict(color=SUBTEXT),
        ),
        margin=dict(t=60, b=40, l=60, r=20),
        height=340,
        showlegend=False,
    )
    return fig


# ─── Macro pie chart ──────────────────────────────────────────────────────────

def build_macro_pie_chart(total_protein: float, total_carbs: float,
                          total_fat: float) -> Optional[go.Figure]:
    """Donut chart of macronutrient breakdown (by calories)."""
    cal_p = total_protein * 4
    cal_c = total_carbs   * 4
    cal_f = total_fat     * 9
    total = cal_p + cal_c + cal_f
    if total == 0:
        return None

    fig = go.Figure(go.Pie(
        labels=["Protein", "Carbs", "Fat"],
        values=[cal_p, cal_c, cal_f],
        hole=0.55,
        marker=dict(colors=[BLUE, GREEN, ORANGE]),
        textinfo="label+percent",
        hovertemplate="<b>%{label}</b><br>%{value:.0f} kcal (%{percent})<extra></extra>",
    ))

    fig.update_layout(
        title=dict(text="🥗 Macro Breakdown (by calories)", font=dict(color=TEXT, size=15)),
        paper_bgcolor=CARD_BG,
        plot_bgcolor=CARD_BG,
        font=dict(color=SUBTEXT),
        margin=dict(t=60, b=20, l=20, r=20),
        height=300,
        showlegend=True,
        legend=dict(font=dict(color=SUBTEXT)),
    )
    return fig


# ─── Calorie progress gauge ───────────────────────────────────────────────────

def build_calorie_gauge(consumed: float, target: int) -> go.Figure:
    """Gauge chart for today's calorie progress."""
    pct = min(consumed / target, 1.0) if target > 0 else 0
    colour = GREEN if pct <= 0.85 else (ORANGE if pct <= 1.0 else RED)

    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=consumed,
        delta={"reference": target, "valueformat": ".0f",
               "prefix": "vs target: ", "suffix": " kcal"},
        number={"suffix": " kcal", "font": {"color": TEXT, "size": 28}},
        gauge={
            "axis": {"range": [0, max(target * 1.3, consumed * 1.1 if consumed > 0 else target * 1.3)],
                     "tickcolor": SUBTEXT},
            "bar":  {"color": colour},
            "bgcolor": "#2D3748",
            "bordercolor": CARD_BG,
            "threshold": {
                "line": {"color": ORANGE, "width": 3},
                "thickness": 0.75,
                "value": target,
            },
        },
        title={"text": "Today's Calories", "font": {"color": TEXT, "size": 14}},
    ))
    fig.update_layout(
        paper_bgcolor=CARD_BG,
        font=dict(color=SUBTEXT),
        margin=dict(t=40, b=20, l=20, r=20),
        height=240,
    )
    return fig


# ─── Meal history as list of dicts (no pandas) ────────────────────────────────

def get_meal_history_records(meal_date: str) -> list[dict]:
    """Return a formatted list of meal records for a given date."""
    meals = get_meals_for_date(meal_date)
    if not meals:
        return []
    result = []
    for m in meals:
        result.append({
            "Food":            m["food_name"],
            "Serving (g)":    m["serving_g"],
            "Calories (kcal)": round(m["calories"], 1),
            "Protein (g)":    m["protein"],
            "Carbs (g)":      m["carbs"],
            "Fat (g)":        m["fat"],
            "Logged At":      m.get("created_at", "")[:16],
        })
    return result


# ─── Weekly summary as list of dicts (no pandas) ─────────────────────────────

def get_weekly_summary_records(days: int = 7) -> list[dict]:
    """Return a list of daily totals for the past `days` days."""
    end   = date.today()
    start = end - timedelta(days=days - 1)
    rows  = get_weekly_totals(start.isoformat(), end.isoformat())
    if not rows:
        return []
    result = []
    for r in rows:
        result.append({
            "Date":         r["meal_date"],
            "Calories":     round(r["total_calories"], 1),
            "Protein (g)":  round(r["total_protein"],  1),
            "Carbs (g)":    round(r["total_carbs"],    1),
            "Fat (g)":      round(r["total_fat"],      1),
            "Meals":        r["meal_count"],
        })
    return result
