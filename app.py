"""
app.py — Intelligent Food Calorie Estimation System
Main Streamlit application entry point.

Run:  streamlit run app.py
"""

from __future__ import annotations

import io
import os
import sys
from datetime import date, datetime

import streamlit as st

# Ensure modules are importable regardless of working directory
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from modules.database   import init_db, add_meal, get_meals_for_date, update_meal, \
                               delete_meal, get_daily_totals, get_setting, set_setting, \
                               clear_all_meals
from modules.nutrition  import get_all_foods, get_food_names, get_food_by_key, \
                               find_food_by_name, calculate_nutrition, search_foods, \
                               get_macro_percentages
from modules.food_classifier import classify_image, validate_image, preprocess_image, \
                                     is_model_available
from modules.analytics  import build_weekly_calorie_chart, build_macro_pie_chart, \
                               build_calorie_gauge, get_meal_history_records, \
                               get_weekly_summary_records

from PIL import Image

# ─── Page config ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Food Calorie Estimation System",
    page_icon="🥗",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── CSS ─────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
    color: #E2E8F0;
}

/* Main background */
.stApp { background-color: #0D1117; }

/* Sidebar */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #161B27 0%, #0D1117 100%);
    border-right: 1px solid #2D3748;
}

/* Cards */
.metric-card {
    background: linear-gradient(135deg, #1A1F2E 0%, #252B3B 100%);
    border: 1px solid #2D3748;
    border-radius: 16px;
    padding: 20px 24px;
    text-align: center;
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}
.metric-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 32px rgba(46,204,113,0.15);
}
.metric-value {
    font-size: 2rem;
    font-weight: 700;
    line-height: 1.1;
}
.metric-label {
    font-size: 0.8rem;
    color: #A0AEC0;
    margin-top: 4px;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}

/* Nutrition breakdown card */
.nutrition-card {
    background: linear-gradient(135deg, #1A1F2E 0%, #1E2436 100%);
    border: 1px solid #2D3748;
    border-radius: 12px;
    padding: 16px 20px;
    margin-bottom: 12px;
}

/* Food result card */
.result-card {
    background: linear-gradient(135deg, #0F2027 0%, #203A43 50%, #2C5364 100%);
    border: 1px solid #3182CE;
    border-radius: 16px;
    padding: 20px 24px;
    margin: 12px 0;
}

/* Prediction badge */
.confidence-badge {
    display: inline-block;
    padding: 4px 12px;
    border-radius: 20px;
    font-size: 0.78rem;
    font-weight: 600;
    letter-spacing: 0.04em;
}
.badge-high   { background: rgba(46,204,113,0.2); color: #2ECC71; border: 1px solid #2ECC71; }
.badge-medium { background: rgba(243,156,18,0.2); color: #F39C12; border: 1px solid #F39C12; }
.badge-low    { background: rgba(231,76,60,0.2);  color: #E74C3C; border: 1px solid #E74C3C; }

/* Macro progress bar */
.macro-bar-wrap { background: #2D3748; border-radius: 8px; height: 10px; margin-top: 4px; }
.macro-bar      { border-radius: 8px; height: 10px; }

/* Alert boxes */
.info-box {
    background: rgba(49,130,206,0.12);
    border: 1px solid #3182CE;
    border-radius: 10px;
    padding: 12px 16px;
    margin: 8px 0;
    font-size: 0.9rem;
}
.warning-box {
    background: rgba(237,137,54,0.12);
    border: 1px solid #ED8936;
    border-radius: 10px;
    padding: 12px 16px;
    margin: 8px 0;
    font-size: 0.9rem;
}
.success-box {
    background: rgba(72,187,120,0.12);
    border: 1px solid #48BB78;
    border-radius: 10px;
    padding: 12px 16px;
    margin: 8px 0;
    font-size: 0.9rem;
}

/* Section header */
.section-header {
    font-size: 1.3rem;
    font-weight: 700;
    color: #E2E8F0;
    border-left: 4px solid #2ECC71;
    padding-left: 12px;
    margin: 24px 0 16px;
}

/* Streamlit elements */
.stButton > button {
    border-radius: 10px;
    font-weight: 600;
    transition: all 0.2s ease;
}
.stButton > button:hover { transform: translateY(-1px); }

div[data-testid="stMetric"] {
    background: #1A1F2E;
    border: 1px solid #2D3748;
    border-radius: 12px;
    padding: 12px 16px;
}

/* Data table styling */
.meal-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.875rem;
}
.meal-table th {
    background: #252B3B;
    color: #A0AEC0;
    padding: 10px 12px;
    text-align: left;
    font-weight: 600;
    text-transform: uppercase;
    font-size: 0.72rem;
    letter-spacing: 0.05em;
    border-bottom: 2px solid #2D3748;
}
.meal-table td {
    padding: 10px 12px;
    border-bottom: 1px solid #2D3748;
    color: #E2E8F0;
}
.meal-table tr:hover td { background: rgba(255,255,255,0.03); }
.meal-table-wrap {
    background: #1A1F2E;
    border: 1px solid #2D3748;
    border-radius: 12px;
    overflow: hidden;
    margin-bottom: 16px;
}
</style>
""", unsafe_allow_html=True)

# ─── Database initialisation ──────────────────────────────────────────────────
init_db()

# ─── Session state defaults ───────────────────────────────────────────────────
if "page" not in st.session_state:
    st.session_state.page = "Dashboard"
if "analysis_result" not in st.session_state:
    st.session_state.analysis_result = None
if "selected_food_key" not in st.session_state:
    st.session_state.selected_food_key = None
if "serving_g" not in st.session_state:
    st.session_state.serving_g = 100.0
if "edit_meal_id" not in st.session_state:
    st.session_state.edit_meal_id = None


# ─── Helper: render HTML table from list of dicts ────────────────────────────
def render_html_table(records: list[dict], highlight_col: str = "") -> str:
    if not records:
        return ""
    headers = list(records[0].keys())
    rows_html = ""
    for rec in records:
        cells = ""
        for h in headers:
            val = rec.get(h, "")
            style = "color:#2ECC71; font-weight:600;" if h == highlight_col else ""
            cells += f'<td style="{style}">{val}</td>'
        rows_html += f"<tr>{cells}</tr>"
    header_html = "".join(f"<th>{h}</th>" for h in headers)
    return f"""
    <div class="meal-table-wrap">
    <table class="meal-table">
        <thead><tr>{header_html}</tr></thead>
        <tbody>{rows_html}</tbody>
    </table>
    </div>"""


# ─── Sidebar navigation ───────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="text-align:center; padding: 12px 0 8px;">
        <div style="font-size:2.2rem;">🥗</div>
        <div style="font-size:1.1rem; font-weight:700; color:#2ECC71; letter-spacing:0.02em;">
            Food Calorie AI
        </div>
        <div style="font-size:0.72rem; color:#718096; margin-top:2px;">
            Intelligent Estimation System
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("---")

    pages = {
        "Dashboard":      "🏠  Dashboard",
        "Analyze Food":   "🔍  Analyze Food",
        "Meal History":   "📋  Meal History",
        "Analytics":      "📊  Analytics",
        "Settings":       "⚙️  Settings",
    }
    for key, label in pages.items():
        is_active = st.session_state.page == key
        if st.button(label, key=f"nav_{key}", use_container_width=True,
                     type="primary" if is_active else "secondary"):
            st.session_state.page = key
            st.rerun()

    st.markdown("---")
    today_totals = get_daily_totals(date.today().isoformat())
    target_cal   = int(get_setting("daily_calorie_target", "2000"))
    consumed     = today_totals["total_calories"]
    remaining    = max(0, target_cal - consumed)
    pct          = int(min(consumed / target_cal * 100, 100)) if target_cal > 0 else 0

    st.markdown(f"""
    <div style="font-size:0.8rem; color:#A0AEC0; margin-bottom:6px; text-transform:uppercase; letter-spacing:0.05em;">
        Today's Progress
    </div>
    <div style="font-size:1.5rem; font-weight:700; color:#2ECC71;">{consumed:.0f} kcal</div>
    <div style="font-size:0.78rem; color:#718096;">of {target_cal} target · {remaining:.0f} remaining</div>
    """, unsafe_allow_html=True)
    st.progress(pct / 100, text=f"{pct}%")

    st.markdown("---")
    model_ok = is_model_available()
    if model_ok:
        st.markdown('<div style="font-size:0.78rem;color:#2ECC71;">✅ AI Model: Active</div>',
                    unsafe_allow_html=True)
    else:
        st.markdown('<div style="font-size:0.78rem;color:#F39C12;">⚠️ AI Model: Loading/Fallback</div>',
                    unsafe_allow_html=True)
        st.caption("Select food manually if model unavailable")


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: DASHBOARD
# ═══════════════════════════════════════════════════════════════════════════════
def page_dashboard():
    st.markdown("""
    <div style="margin-bottom:24px;">
        <h1 style="font-size:2rem; font-weight:800; color:#E2E8F0; margin:0;">
            🥗 Intelligent Food Calorie Estimation
        </h1>
        <p style="color:#718096; margin-top:4px; font-size:0.95rem;">
            AI-powered nutritional tracking · Real-time calorie insights
        </p>
    </div>
    """, unsafe_allow_html=True)

    today_str    = date.today().isoformat()
    today_totals = get_daily_totals(today_str)
    target_cal   = int(get_setting("daily_calorie_target", "2000"))
    consumed_cal = today_totals["total_calories"]
    pct_consumed = min(consumed_cal / target_cal * 100, 100) if target_cal else 0
    remaining    = max(0, target_cal - consumed_cal)

    # ── Hero metric row ──
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        cal_color = "#2ECC71" if consumed_cal <= target_cal else "#E74C3C"
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value" style="color:{cal_color};">{consumed_cal:.0f}</div>
            <div class="metric-label">Calories Today</div>
        </div>""", unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value" style="color:#F39C12;">{remaining:.0f}</div>
            <div class="metric-label">Remaining (kcal)</div>
        </div>""", unsafe_allow_html=True)
    with c3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value" style="color:#3498DB;">{today_totals['meal_count']}</div>
            <div class="metric-label">Meals Logged</div>
        </div>""", unsafe_allow_html=True)
    with c4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value" style="color:#9B59B6;">{target_cal}</div>
            <div class="metric-label">Daily Target (kcal)</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Calorie progress bar ──
    st.markdown('<div class="section-header">📈 Today\'s Calorie Progress</div>', unsafe_allow_html=True)
    bar_color = "#2ECC71" if pct_consumed <= 85 else ("#F39C12" if pct_consumed <= 100 else "#E74C3C")
    st.markdown(f"""
    <div style="background:#2D3748; border-radius:10px; height:18px; width:100%; overflow:hidden;">
        <div style="background:{bar_color}; width:{pct_consumed:.1f}%; height:100%; border-radius:10px;
                    transition:width 0.5s ease; display:flex; align-items:center; justify-content:flex-end;
                    padding-right:8px;">
            <span style="font-size:0.72rem; font-weight:700; color:#0D1117; white-space:nowrap;">
                {pct_consumed:.0f}%
            </span>
        </div>
    </div>
    <div style="display:flex; justify-content:space-between; margin-top:4px; font-size:0.8rem; color:#718096;">
        <span>0 kcal</span>
        <span>{consumed_cal:.0f} consumed of {target_cal} target</span>
        <span>{target_cal} kcal</span>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Macro summary ──
    col_a, col_b = st.columns([2, 1])
    with col_a:
        st.markdown('<div class="section-header">🧬 Macro Nutrients (Today)</div>', unsafe_allow_html=True)
        mc1, mc2, mc3 = st.columns(3)
        macros = [
            ("Protein",       today_totals["total_protein"], "#3498DB", 50),
            ("Carbohydrates", today_totals["total_carbs"],   "#2ECC71", 250),
            ("Fat",           today_totals["total_fat"],     "#F39C12", 65),
        ]
        for col, (label, val, color, ref) in zip([mc1, mc2, mc3], macros):
            p = min(val / ref * 100, 100) if ref else 0
            with col:
                st.markdown(f"""
                <div class="nutrition-card">
                    <div style="font-size:1.4rem; font-weight:700; color:{color};">{val:.1f}g</div>
                    <div style="font-size:0.78rem; color:#A0AEC0;">{label}</div>
                    <div class="macro-bar-wrap" style="margin-top:8px;">
                        <div class="macro-bar" style="background:{color}; width:{p:.0f}%;"></div>
                    </div>
                    <div style="font-size:0.7rem; color:#4A5568; margin-top:3px;">{p:.0f}% of ~{ref}g ref</div>
                </div>""", unsafe_allow_html=True)

    with col_b:
        st.markdown('<div class="section-header">🚀 Quick Action</div>', unsafe_allow_html=True)
        if st.button("📸  Analyze Food Image", use_container_width=True, type="primary"):
            st.session_state.page = "Analyze Food"
            st.rerun()
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("📋  View Meal History", use_container_width=True):
            st.session_state.page = "Meal History"
            st.rerun()
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("📊  View Analytics", use_container_width=True):
            st.session_state.page = "Analytics"
            st.rerun()

    # ── Recent meals ──
    st.markdown('<div class="section-header">🍽️ Recent Meals (Today)</div>', unsafe_allow_html=True)
    meals = get_meals_for_date(today_str)
    if not meals:
        st.markdown("""
        <div class="info-box">
            🌟 No meals logged today yet. Upload a food photo to get started!
        </div>""", unsafe_allow_html=True)
    else:
        for meal in meals[-5:][::-1]:
            t = meal.get("created_at", "")[:16]
            st.markdown(f"""
            <div class="nutrition-card" style="display:flex; justify-content:space-between; align-items:center;">
                <div>
                    <span style="font-weight:600; color:#E2E8F0;">{meal['food_name']}</span>
                    <span style="color:#718096; font-size:0.82rem; margin-left:8px;">· {meal['serving_g']}g</span>
                    <br><span style="font-size:0.75rem; color:#4A5568;">{t}</span>
                </div>
                <div style="text-align:right;">
                    <div style="font-size:1.2rem; font-weight:700; color:#2ECC71;">{meal['calories']:.0f}</div>
                    <div style="font-size:0.72rem; color:#718096;">kcal</div>
                </div>
            </div>""", unsafe_allow_html=True)

    # ── Disclaimer ──
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("""
    <div class="warning-box">
        ⚠️ <b>Disclaimer:</b> Nutritional values are <em>estimates</em> based on reference data.
        They vary by preparation method, ingredient brand, and portion measurement.
        This application is for informational purposes only and is <strong>not a medical or
        dietary diagnostic tool</strong>. Consult a registered dietitian for personalised advice.
    </div>""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: ANALYZE FOOD
# ═══════════════════════════════════════════════════════════════════════════════
def page_analyze():
    st.markdown("""
    <h1 style="font-size:1.8rem; font-weight:800; color:#E2E8F0; margin-bottom:4px;">
        🔍 Food Image Analysis
    </h1>
    <p style="color:#718096; font-size:0.92rem; margin-bottom:20px;">
        Upload a food photo · AI identifies the food · View nutritional breakdown
    </p>
    """, unsafe_allow_html=True)

    model_ok = is_model_available()
    if not model_ok:
        st.markdown("""
        <div class="warning-box">
            ⚠️ <b>Fallback Mode Active</b> — The AI model is not currently loaded (first-time download
            may take a few minutes). You can still select food manually and get accurate nutritional data.
            To enable AI inference, ensure you have an active internet connection and restart the app.
        </div>""", unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="success-box">
            ✅ <b>AI Model Active</b> — Upload a food image to classify it automatically.
            Results are classification estimates; always verify and correct if needed.
        </div>""", unsafe_allow_html=True)

    col_upload, col_result = st.columns([1, 1], gap="large")

    with col_upload:
        st.markdown('<div class="section-header">📤 Upload Food Image</div>', unsafe_allow_html=True)
        uploaded = st.file_uploader(
            "Choose an image file",
            type=["jpg", "jpeg", "png"],
            help="Supported formats: JPG, JPEG, PNG · Max 10 MB",
            key="food_uploader",
        )

        if uploaded:
            file_bytes = uploaded.read()
            is_valid, err_msg = validate_image(file_bytes, uploaded.name)

            if not is_valid:
                st.error(f"❌ {err_msg}")
            else:
                img = preprocess_image(file_bytes)
                st.image(img, caption=f"Uploaded: {uploaded.name}",
                         use_container_width=True)
                st.markdown(f"""
                <div style="font-size:0.78rem; color:#718096; text-align:center; margin-top:4px;">
                    {uploaded.name} · {len(file_bytes)//1024} KB · {img.size[0]}×{img.size[1]} px
                </div>""", unsafe_allow_html=True)

                col_btn1, col_btn2 = st.columns(2)
                with col_btn1:
                    analyze_btn = st.button("🤖 Analyze with AI", use_container_width=True,
                                            type="primary", disabled=not model_ok)
                with col_btn2:
                    skip_btn = st.button("✍️ Select Manually", use_container_width=True)

                if analyze_btn and model_ok:
                    with st.spinner("🔍 Running AI inference…"):
                        result = classify_image(img, top_k=5)
                    st.session_state.analysis_result = result
                    if result.get("top_food_key"):
                        st.session_state.selected_food_key = result["top_food_key"]
                        food = get_food_by_key(result["top_food_key"])
                        if food:
                            st.session_state.serving_g = float(food["default_serving_g"])
                    st.rerun()

                if skip_btn:
                    st.session_state.analysis_result = {
                        "fallback_mode": True, "success": False,
                        "predictions": [], "top_food_key": None,
                        "top_label": "Manual", "top_score": 0.0,
                        "low_confidence": False, "error": None,
                    }
                    st.rerun()

    with col_result:
        st.markdown('<div class="section-header">🧪 Analysis Results</div>', unsafe_allow_html=True)
        result = st.session_state.analysis_result

        if result is None:
            st.markdown("""
            <div style="text-align:center; padding:60px 20px; color:#4A5568;">
                <div style="font-size:3rem;">📷</div>
                <div style="font-size:1rem; margin-top:12px;">Upload an image and click Analyze</div>
                <div style="font-size:0.8rem; margin-top:6px;">AI will identify the food automatically</div>
            </div>""", unsafe_allow_html=True)
        else:
            _render_analysis_result(result)


def _render_analysis_result(result: dict):
    """Render the AI result and food selector / nutrition panel."""
    db = get_all_foods()
    food_keys_sorted = sorted(db.keys(), key=lambda k: db[k]["name"])
    food_display_names = [db[k]["name"] for k in food_keys_sorted]

    # ── AI prediction display ──
    if result.get("success") and result.get("predictions"):
        top = result["predictions"][0]
        score = top["score"]
        badge_cls = "badge-high" if score > 0.5 else ("badge-medium" if score > 0.2 else "badge-low")
        badge_txt = f"{score*100:.1f}% confidence"

        low_conf_html = (
            "<br><span style='color:#F39C12;font-size:0.82rem;margin-top:6px;display:block;'>"
            "⚠️ Low confidence – please verify the food below</span>"
            if result.get("low_confidence") else ""
        )

        st.markdown(f"""
        <div class="result-card">
            <div style="font-size:0.78rem; color:#A0AEC0; text-transform:uppercase; letter-spacing:0.05em;">
                AI Prediction
            </div>
            <div style="font-size:1.6rem; font-weight:700; color:#E2E8F0; margin:6px 0;">
                {top['label']}
            </div>
            <span class="confidence-badge {badge_cls}">{badge_txt}</span>
            {low_conf_html}
        </div>""", unsafe_allow_html=True)

        if len(result["predictions"]) > 1:
            with st.expander("📋 Alternative predictions"):
                for pred in result["predictions"][1:]:
                    pct = pred["score"] * 100
                    st.markdown(f"""
                    <div style="display:flex; justify-content:space-between; padding:4px 0;
                                border-bottom:1px solid #2D3748; font-size:0.88rem;">
                        <span style="color:#CBD5E0;">{pred['label']}</span>
                        <span style="color:#718096;">{pct:.1f}%</span>
                    </div>""", unsafe_allow_html=True)
    elif result.get("error"):
        st.markdown(f'<div class="warning-box">⚠️ {result["error"]}</div>', unsafe_allow_html=True)
    elif result.get("fallback_mode"):
        st.markdown("""
        <div class="info-box">✍️ Manual selection mode — choose the food from the list below.</div>
        """, unsafe_allow_html=True)

    # ── Food selector (correction / manual) ──
    st.markdown("**Select / Confirm Food:**")
    current_key = st.session_state.get("selected_food_key")
    current_idx = 0
    if current_key and current_key in food_keys_sorted:
        current_idx = food_keys_sorted.index(current_key)

    selected_name = st.selectbox(
        "Food", options=food_display_names,
        index=current_idx, key="food_selector",
        help="The AI's prediction is pre-selected. You can change it."
    )
    matched = find_food_by_name(selected_name)
    if matched:
        sel_key, sel_food = matched
        st.session_state.selected_food_key = sel_key
    else:
        sel_key  = food_keys_sorted[current_idx]
        sel_food = db[sel_key]

    # ── Serving weight ──
    default_s = float(sel_food.get("default_serving_g", 100))
    serving_g = st.number_input(
        f"Serving weight (g) — default: {sel_food['serving_description']}",
        min_value=1.0, max_value=3000.0,
        value=st.session_state.get("serving_g", default_s),
        step=5.0, key="serving_input",
    )
    st.session_state.serving_g = serving_g

    # ── Calculated nutrition ──
    nutrition = calculate_nutrition(sel_food, serving_g)

    st.markdown('<div class="section-header">🥦 Nutritional Breakdown</div>', unsafe_allow_html=True)
    nc1, nc2, nc3, nc4 = st.columns(4)
    macro_data = [
        (nc1, f"{nutrition['calories']:.0f}", "kcal",    "#2ECC71"),
        (nc2, f"{nutrition['protein']:.1f}g", "Protein", "#3498DB"),
        (nc3, f"{nutrition['carbs']:.1f}g",   "Carbs",   "#F39C12"),
        (nc4, f"{nutrition['fat']:.1f}g",     "Fat",     "#E74C3C"),
    ]
    for col, val, label, color in macro_data:
        with col:
            st.markdown(f"""
            <div class="metric-card" style="padding:14px;">
                <div class="metric-value" style="color:{color}; font-size:1.5rem;">{val}</div>
                <div class="metric-label">{label}</div>
            </div>""", unsafe_allow_html=True)

    st.markdown(f"""
    <div class="info-box" style="margin-top:10px; font-size:0.82rem;">
        Per 100g: {sel_food['calories_per_100g']} kcal · P: {sel_food['protein_per_100g']}g ·
        C: {sel_food['carbs_per_100g']}g · F: {sel_food['fat_per_100g']}g
        <br><span style="color:#718096;">Source: {sel_food.get('source','Reference data')}</span>
    </div>""", unsafe_allow_html=True)

    # ── Log meal button ──
    st.markdown("<br>", unsafe_allow_html=True)
    meal_date = st.date_input("Log for date", value=date.today(), key="log_date")
    if st.button("💾  Log This Meal", type="primary", use_container_width=True):
        add_meal(
            meal_date=meal_date.isoformat(),
            food_name=sel_food["name"],
            serving_g=serving_g,
            calories=nutrition["calories"],
            protein=nutrition["protein"],
            carbs=nutrition["carbs"],
            fat=nutrition["fat"],
        )
        st.success(f"✅ Logged **{sel_food['name']}** ({nutrition['calories']:.0f} kcal) for {meal_date}")
        st.session_state.analysis_result = None
        st.session_state.selected_food_key = None
        st.balloons()


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: MEAL HISTORY
# ═══════════════════════════════════════════════════════════════════════════════
def page_meal_history():
    st.markdown("""
    <h1 style="font-size:1.8rem; font-weight:800; color:#E2E8F0; margin-bottom:4px;">
        📋 Meal History
    </h1>
    <p style="color:#718096; font-size:0.92rem; margin-bottom:20px;">
        View, edit, and delete your logged meals
    </p>""", unsafe_allow_html=True)

    selected_date = st.date_input("Select date", value=date.today(), key="history_date")
    date_str = selected_date.isoformat()

    totals = get_daily_totals(date_str)
    meals  = get_meals_for_date(date_str)

    sc1, sc2, sc3, sc4, sc5 = st.columns(5)
    for col, val, label, color in [
        (sc1, f"{totals['total_calories']:.0f}", "Total kcal",  "#2ECC71"),
        (sc2, f"{totals['total_protein']:.1f}g", "Protein",    "#3498DB"),
        (sc3, f"{totals['total_carbs']:.1f}g",   "Carbs",      "#F39C12"),
        (sc4, f"{totals['total_fat']:.1f}g",     "Fat",        "#E74C3C"),
        (sc5, str(totals["meal_count"]),          "Meals",      "#9B59B6"),
    ]:
        with col:
            st.markdown(f"""
            <div class="metric-card" style="padding:14px;">
                <div class="metric-value" style="color:{color}; font-size:1.4rem;">{val}</div>
                <div class="metric-label">{label}</div>
            </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    if not meals:
        st.markdown(f"""
        <div class="info-box">
            🍽️ No meals logged for <strong>{date_str}</strong>.
            Go to <em>Analyze Food</em> to log your first meal.
        </div>""", unsafe_allow_html=True)
        return

    st.markdown(f'<div class="section-header">🍽️ Meals — {date_str}</div>', unsafe_allow_html=True)

    edit_id = st.session_state.get("edit_meal_id")
    db = get_all_foods()

    for meal in meals:
        mid = meal["id"]
        with st.container():
            if edit_id == mid:
                st.markdown(f"**✏️ Editing: {meal['food_name']}**")
                food_keys_sorted   = sorted(db.keys(), key=lambda k: db[k]["name"])
                food_display_names = [db[k]["name"] for k in food_keys_sorted]
                matched = find_food_by_name(meal["food_name"])
                edit_idx = food_keys_sorted.index(matched[0]) if matched else 0
                new_name_sel = st.selectbox("Food", food_display_names,
                                            index=edit_idx, key=f"edit_food_{mid}")
                matched2 = find_food_by_name(new_name_sel)
                new_food = matched2[1] if matched2 else db[food_keys_sorted[edit_idx]]
                new_serving = st.number_input("Serving (g)", min_value=1.0, max_value=3000.0,
                                              value=float(meal["serving_g"]),
                                              step=5.0, key=f"edit_serv_{mid}")
                new_nut = calculate_nutrition(new_food, new_serving)
                st.caption(f"Calories: {new_nut['calories']:.0f} kcal · P: {new_nut['protein']:.1f}g · "
                           f"C: {new_nut['carbs']:.1f}g · F: {new_nut['fat']:.1f}g")
                eb1, eb2 = st.columns(2)
                with eb1:
                    if st.button("💾 Save", key=f"save_{mid}", type="primary", use_container_width=True):
                        update_meal(mid, new_food["name"], new_serving,
                                    new_nut["calories"], new_nut["protein"],
                                    new_nut["carbs"], new_nut["fat"])
                        st.session_state.edit_meal_id = None
                        st.success("✅ Meal updated.")
                        st.rerun()
                with eb2:
                    if st.button("✖ Cancel", key=f"cancel_{mid}", use_container_width=True):
                        st.session_state.edit_meal_id = None
                        st.rerun()
                st.markdown("---")
            else:
                col_a, col_b, col_c = st.columns([3, 2, 1])
                t = meal.get("created_at", "")[:16]
                with col_a:
                    st.markdown(f"""
                    <div style="padding:6px 0;">
                        <span style="font-weight:600; font-size:1rem; color:#E2E8F0;">{meal['food_name']}</span>
                        <span style="color:#718096; font-size:0.82rem; margin-left:8px;">· {meal['serving_g']}g · {t}</span>
                        <br>
                        <span style="font-size:0.82rem; color:#718096;">
                            P: {meal['protein']}g · C: {meal['carbs']}g · F: {meal['fat']}g
                        </span>
                    </div>""", unsafe_allow_html=True)
                with col_b:
                    st.markdown(f"""
                    <div style="text-align:right; padding:6px 0;">
                        <span style="font-size:1.4rem; font-weight:700; color:#2ECC71;">{meal['calories']:.0f}</span>
                        <span style="font-size:0.78rem; color:#718096;"> kcal</span>
                    </div>""", unsafe_allow_html=True)
                with col_c:
                    btn_col1, btn_col2 = st.columns(2)
                    with btn_col1:
                        if st.button("✏️", key=f"edit_{mid}", help="Edit meal"):
                            st.session_state.edit_meal_id = mid
                            st.rerun()
                    with btn_col2:
                        if st.button("🗑️", key=f"del_{mid}", help="Delete meal"):
                            delete_meal(mid)
                            st.success("Meal deleted.")
                            st.rerun()
                st.markdown('<hr style="border-color:#2D3748; margin:4px 0;">', unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: ANALYTICS
# ═══════════════════════════════════════════════════════════════════════════════
def page_analytics():
    st.markdown("""
    <h1 style="font-size:1.8rem; font-weight:800; color:#E2E8F0; margin-bottom:4px;">
        📊 Nutrition Analytics
    </h1>
    <p style="color:#718096; font-size:0.92rem; margin-bottom:20px;">
        Weekly trends, macro distribution, and daily summaries
    </p>""", unsafe_allow_html=True)

    target_cal = int(get_setting("daily_calorie_target", "2000"))
    today_str  = date.today().isoformat()
    today_tots = get_daily_totals(today_str)

    col_g, col_p = st.columns([1, 1])
    with col_g:
        fig_gauge = build_calorie_gauge(today_tots["total_calories"], target_cal)
        st.plotly_chart(fig_gauge, use_container_width=True)
    with col_p:
        fig_pie = build_macro_pie_chart(today_tots["total_protein"],
                                        today_tots["total_carbs"],
                                        today_tots["total_fat"])
        if fig_pie:
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.markdown("""
            <div class="info-box" style="margin-top:40px; text-align:center;">
                🍽️ No meals logged today — macro chart will appear after you log meals.
            </div>""", unsafe_allow_html=True)

    st.markdown('<div class="section-header">📈 Weekly Calorie Intake</div>', unsafe_allow_html=True)
    fig_week = build_weekly_calorie_chart(target_cal, days=7)
    st.plotly_chart(fig_week, use_container_width=True)

    # Weekly summary table
    st.markdown('<div class="section-header">📅 Weekly Summary</div>', unsafe_allow_html=True)
    weekly_records = get_weekly_summary_records(days=7)
    if not weekly_records:
        st.markdown('<div class="info-box">No meals logged in the past 7 days.</div>',
                    unsafe_allow_html=True)
    else:
        st.markdown(render_html_table(weekly_records, "Calories"), unsafe_allow_html=True)

    # Today's meals table
    st.markdown(f'<div class="section-header">🍽️ Today\'s Meals</div>', unsafe_allow_html=True)
    today_records = get_meal_history_records(today_str)
    if not today_records:
        st.markdown('<div class="info-box">No meals logged today.</div>', unsafe_allow_html=True)
    else:
        st.markdown(render_html_table(today_records, "Calories (kcal)"), unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: SETTINGS
# ═══════════════════════════════════════════════════════════════════════════════
def page_settings():
    st.markdown("""
    <h1 style="font-size:1.8rem; font-weight:800; color:#E2E8F0; margin-bottom:4px;">
        ⚙️ Settings & Data Management
    </h1>
    <p style="color:#718096; font-size:0.92rem; margin-bottom:20px;">
        Configure your calorie targets and manage stored data
    </p>""", unsafe_allow_html=True)

    st.markdown('<div class="section-header">🎯 Daily Calorie Target</div>', unsafe_allow_html=True)
    current_target = int(get_setting("daily_calorie_target", "2000"))
    new_target = st.number_input("Daily Calorie Target (kcal)",
                                  min_value=500, max_value=8000,
                                  value=current_target, step=50,
                                  help="Recommended adult range: 1500–3000 kcal/day",
                                  key="target_input")
    if st.button("💾 Save Target", type="primary"):
        set_setting("daily_calorie_target", str(int(new_target)))
        st.success(f"✅ Daily target updated to {int(new_target)} kcal")

    st.markdown('<div class="section-header">📏 Reference Guidelines</div>', unsafe_allow_html=True)
    ref_rows = [
        {"Group": "Sedentary adult (Male)",   "Approx. kcal/day": "2000–2400"},
        {"Group": "Sedentary adult (Female)", "Approx. kcal/day": "1600–2000"},
        {"Group": "Active adult (Male)",      "Approx. kcal/day": "2400–3000"},
        {"Group": "Active adult (Female)",    "Approx. kcal/day": "2000–2400"},
        {"Group": "Athlete",                  "Approx. kcal/day": "3000–5000"},
    ]
    st.markdown(render_html_table(ref_rows), unsafe_allow_html=True)

    st.markdown('<div class="section-header">🤖 AI Model Information</div>', unsafe_allow_html=True)
    model_ok = is_model_available()
    status = "✅ Active" if model_ok else "⚠️ Not loaded (fallback mode)"
    st.markdown(f"""
    <div class="nutrition-card">
        <b>Model:</b> nateraw/food (ViT fine-tuned on Food-101)<br>
        <b>Status:</b> {status}<br>
        <b>Dataset:</b> Food-101 (101 food categories)<br>
        <b>Framework:</b> PyTorch + Hugging Face Transformers<br>
        <b>Note:</b> Not all Indian dishes are in Food-101. Unknown labels fall back to manual selection.
    </div>""", unsafe_allow_html=True)

    st.markdown('<div class="section-header">🗄️ Data Management</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="warning-box">
        ⚠️ The reset action permanently deletes <strong>all</strong> meal records.
        This cannot be undone.
    </div>""", unsafe_allow_html=True)

    confirm = st.checkbox("I understand — delete all meal data", key="confirm_reset")
    if confirm:
        if st.button("🗑️ Reset All Demo Data", type="primary"):
            clear_all_meals()
            st.success("✅ All meal records have been deleted.")
            st.rerun()

    st.markdown('<div class="section-header">⚠️ Disclaimer</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="warning-box">
        <b>This application provides nutritional estimates for educational and informational
        purposes only.</b><br><br>
        • Values are based on standardised reference data and may not reflect your specific
          preparation method, ingredients, or portion sizes.<br>
        • The AI food classifier may misidentify foods; always verify predictions.<br>
        • This tool is <strong>NOT</strong> a substitute for professional medical or dietary advice.<br>
        • Consult a registered dietitian or healthcare professional for personalised guidance.
    </div>""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# ROUTER
# ═══════════════════════════════════════════════════════════════════════════════
page = st.session_state.page
if   page == "Dashboard":    page_dashboard()
elif page == "Analyze Food":  page_analyze()
elif page == "Meal History":  page_meal_history()
elif page == "Analytics":     page_analytics()
elif page == "Settings":      page_settings()
else:
    st.session_state.page = "Dashboard"
    page_dashboard()
