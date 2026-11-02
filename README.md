# Intelligent Food Calorie Estimation System

An AI-powered web application for food identification and nutritional tracking, built as a college AI/ML project demonstration.

---

## Features

| Feature | Status |
|---------|--------|
| Food image upload & AI classification | ✅ Complete |
| Manual food selection fallback | ✅ Complete |
| Nutritional breakdown (calories, protein, carbs, fat) | ✅ Complete |
| Adjustable serving weight with live recalculation | ✅ Complete |
| Meal logging with SQLite | ✅ Complete |
| Edit / delete meals | ✅ Complete |
| Daily calorie & macro summary | ✅ Complete |
| Weekly calorie bar chart (Plotly) | ✅ Complete |
| Macro donut chart | ✅ Complete |
| Calorie gauge | ✅ Complete |
| Configurable daily calorie target | ✅ Complete |
| Demo data reset | ✅ Complete |
| 36 automated tests (all passing) | ✅ Complete |

---

## Architecture

```
Food-Calorie-Estimation-system/
├── app.py                    # Streamlit entry point & all page rendering
├── requirements.txt          # Python dependencies
├── data/
│   ├── foods.json            # Nutritional reference database (21 foods)
│   └── food_tracker.db       # SQLite database (auto-created on startup)
├── modules/
│   ├── __init__.py
│   ├── database.py           # SQLite CRUD — meals & settings
│   ├── nutrition.py          # Nutritional lookup & proportional calculations
│   ├── food_classifier.py    # ViT food image classifier (nateraw/food)
│   └── analytics.py          # Plotly charts, daily/weekly summaries
├── tests/
│   ├── __init__.py
│   └── test_suite.py         # 36 automated unit tests
├── venv/                     # Python virtual environment
├── .gitignore
└── README.md
```

---

## Technology Stack

| Component | Technology |
|-----------|-----------|
| Language | Python 3.14 |
| Web framework | Streamlit 1.66 |
| Machine learning | PyTorch 2.x + Hugging Face Transformers |
| Image processing | Pillow |
| Database | SQLite (built-in) |
| Visualization | Plotly |
| Dependency management | Python venv + requirements.txt |

---

## Installation & Setup

### Prerequisites
- Python 3.10 or higher (tested on 3.14)
- Internet connection (required for first-time model download, ~350 MB)
- 2 GB free disk space

### Step 1 — Clone / navigate to the project
```powershell
cd C:\Projects\Food-Calorie-Estimation-system
```

### Step 2 — Create and activate virtual environment
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### Step 3 — Install dependencies
```powershell
pip install -r requirements.txt
```

> **Note for PyTorch (CPU-only):** The requirements.txt installs standard PyTorch.
> If the default index is slow, use the CPU-specific wheel:
> ```powershell
> pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
> ```

### Step 4 — Run the application
```powershell
.\venv\Scripts\streamlit.exe run app.py
```

The app will open at: **http://localhost:8501**

---

## Running Tests

```powershell
.\venv\Scripts\python.exe tests\test_suite.py
```

Expected output:
```
Ran 36 tests in ~0.6s
OK
```

---

## Machine Learning Model

### Model: `nateraw/food`
- **Architecture:** Vision Transformer (ViT-base-patch16-224)
- **Training dataset:** Food-101 (101 food categories, 101,000 images)
- **Source:** [Hugging Face Hub](https://huggingface.co/nateraw/food)
- **Weights download:** Automatic on first use (~350 MB, cached in `~/.cache/huggingface/`)

### Supported Food Categories (Food-101 labels mapped to nutrition DB)
Pizza, Burger/Hamburger, Pasta (spaghetti variants), Sandwich, Caesar/Greek Salad, Eggs Benedict/Deviled Eggs, Dosa, Biryani, Apple, Banana, and 40+ more Food-101 categories.

### Fallback Mode
When the model cannot be loaded (no internet, first startup, or environment restrictions), the app automatically:
1. Displays a clear **"⚠️ Fallback Mode Active"** warning
2. Enables the **"✍️ Select Manually"** button
3. Provides the full nutrition database for manual selection
4. Never pretends to have run AI inference

---

## Nutritional Database

Location: `data/foods.json`

Contains 21 foods with per-100g values for calories, protein, carbohydrates, and fat:

**Indian foods:** Idli, Dosa, Plain Rice, Biryani, Chapati/Roti, Dal, Paneer Curry, Samosa, Poha, Upma, Chicken Curry, Curd/Yogurt

**International foods:** Salad, Pizza, Burger, Pasta, Sandwich, Oatmeal

**Fruits/Proteins:** Apple, Banana, Eggs

**Sources:** ICMR Nutritive Value of Indian Foods, USDA FoodData Central

> ⚠️ Values are **reference estimates**. Actual nutritional content varies by recipe, preparation method, ingredient brands, and portion measurement accuracy.

---

## Calculation Method

```
nutrient_total = nutrient_per_100g × serving_weight_g / 100
```

This is applied for calories, protein, carbohydrates, and fat independently. All values are rounded to 1 decimal place.

---

## Known Limitations

1. **Indian food recognition:** Food-101 has limited Indian food labels. Idli, Chapati, Poha, Upma, Paneer Curry, Dal are not in the standard Food-101 class list — these require manual selection.

2. **Model confidence:** Food images with complex backgrounds, poor lighting, or uncommon plating may yield low-confidence predictions. Always verify the AI's suggestion.

3. **Pandas incompatibility on Windows:** On systems with Windows Application Control policies (Defender / AppLocker), `pandas` compiled extension DLLs may be blocked. This app was redesigned to eliminate the pandas dependency entirely — data tables use native Python and HTML.

4. **Calorie estimates are approximate:** The nutritional database uses standardised reference values. Home-cooked and restaurant versions vary significantly.

5. **No multi-food detection:** The model classifies the dominant food in an image. Meals with multiple dishes on one plate may be classified as only one item.

6. **Internet required for model download:** The first run downloads ~350 MB of model weights. Subsequent runs use the local cache.

---

## Disclaimer

This application provides nutritional estimates for **educational and informational purposes only**. It is **not** a medical or dietary diagnostic tool. Nutritional values are approximations based on reference datasets and may not reflect your specific preparation method, ingredient brands, or portion sizes. Consult a registered dietitian or healthcare professional for personalised dietary guidance.
