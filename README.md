<div align="center">

# 🥗 Intelligent Food Calorie Estimation System

**An AI-powered web application that identifies food from photos and delivers instant nutritional insights.**

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.66-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://streamlit.io)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.x-EE4C2C?style=for-the-badge&logo=pytorch&logoColor=white)](https://pytorch.org)
[![Hugging Face](https://img.shields.io/badge/HuggingFace-Transformers-FFD21E?style=for-the-badge&logo=huggingface&logoColor=black)](https://huggingface.co/nateraw/food)
[![SQLite](https://img.shields.io/badge/SQLite-Database-003B57?style=for-the-badge&logo=sqlite&logoColor=white)](https://sqlite.org)
[![Plotly](https://img.shields.io/badge/Plotly-Charts-3F4F75?style=for-the-badge&logo=plotly&logoColor=white)](https://plotly.com)
[![Tests](https://img.shields.io/badge/Tests-36%20Passing-2ECC71?style=for-the-badge&logo=checkmarx&logoColor=white)]()
[![License](https://img.shields.io/badge/License-MIT-blue?style=for-the-badge)](LICENSE)

<br/>

> Upload a photo of your food → AI identifies it → See full nutritional breakdown → Log your meal.
> That's it.

<br/>

![App Demo](https://img.shields.io/badge/Live%20Demo-localhost%3A8501-2ECC71?style=flat-square&logo=streamlit)

</div>

---

## 📌 Table of Contents

- [Overview](#-overview)
- [Features](#-features)
- [Tech Stack](#-tech-stack)
- [Project Structure](#-project-structure)
- [How the AI Works](#-how-the-ai-works)
- [Food Database](#-food-database)
- [Getting Started](#-getting-started)
- [Running Tests](#-running-tests)
- [Screenshots](#-screenshots)
- [Limitations](#-limitations)
- [Contributing](#-contributing)
- [License](#-license)

---

## 🧠 Overview

The **Intelligent Food Calorie Estimation System** is a college AI/ML project that combines **computer vision**, **deep learning**, and **nutritional science** into a clean, interactive web application.

Most calorie tracking apps require you to manually search for every food item — a tedious, error-prone process. This app solves that by letting you simply **upload a photo**. A Vision Transformer (ViT) model fine-tuned on the Food-101 dataset classifies the food, and the app instantly displays:

- 🔢 Calories, Protein, Carbohydrates, and Fat
- ⚖️ Adjustable serving weight with live recalculation
- 📊 Daily and weekly intake analytics
- 💾 Persistent meal logging with full edit/delete support

The nutritional database is sourced from **ICMR** (Indian Council of Medical Research) and **USDA FoodData Central**, covering both Indian and international foods.

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 📸 **AI Food Classification** | ViT model identifies food from an uploaded photo with confidence scores |
| ✍️ **Manual Fallback** | Dropdown food selector when AI is uncertain or unavailable |
| 🔢 **Nutritional Breakdown** | Calories, Protein, Carbs, Fat — per your exact serving weight |
| ⚖️ **Adjustable Serving** | Slide serving weight → nutrition recalculates instantly |
| 💾 **Meal Logging** | Save meals to a local SQLite database with timestamp |
| ✏️ **Edit / Delete Meals** | Full CRUD operations on every logged meal |
| 📈 **Daily Summary** | Real-time progress bar and macro breakdown for today |
| 📊 **Weekly Analytics** | Interactive bar chart, macro donut chart, and calorie gauge |
| 🎯 **Custom Calorie Target** | Set your own daily calorie goal (500–8000 kcal) |
| 🔁 **Demo Reset** | One-click wipe of all meal data |
| ✅ **36 Unit Tests** | Full test suite covering all modules — all passing |

---

## 🛠️ Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Language** | Python 3.10+ | Core language |
| **Web Framework** | Streamlit 1.66 | Interactive UI — no HTML/JS needed |
| **AI Model** | `nateraw/food` (ViT) | Food image classification |
| **ML Framework** | PyTorch 2.x | Deep learning inference |
| **Model Hub** | Hugging Face Transformers | Model loading via `AutoModelForImageClassification` |
| **Image Processing** | Pillow (PIL) | Validation, conversion, preprocessing |
| **Database** | SQLite | Serverless local meal storage |
| **Visualization** | Plotly | Interactive bar, pie/donut, and gauge charts |
| **Data Sources** | USDA FoodData Central + ICMR | Authoritative nutritional reference data |

---

## 📁 Project Structure

```
Food-Calorie-Estimation-system/
│
├── app.py                      # Streamlit entry point — all 5 pages
├── requirements.txt            # Python dependencies
├── README.md
├── .gitignore
│
├── data/
│   ├── foods.json              # Nutritional database — 21 foods
│   └── food_tracker.db         # SQLite database (auto-created on first run)
│
├── modules/
│   ├── __init__.py
│   ├── food_classifier.py      # ViT AI inference pipeline
│   ├── nutrition.py            # Nutritional lookup & calculation
│   ├── database.py             # SQLite CRUD — meals & settings
│   └── analytics.py            # Plotly chart builders & summaries
│
├── tests/
│   ├── __init__.py
│   └── test_suite.py           # 36 automated unit tests
│
└── venv/                       # Virtual environment (not tracked)
```

---

## 🤖 How the AI Works

### Model: `nateraw/food` — Vision Transformer (ViT)

The [Vision Transformer](https://huggingface.co/nateraw/food) is a deep learning architecture that applies the **Transformer self-attention mechanism** to images. Instead of using convolutional filters like CNNs, ViT splits the image into fixed-size **patches** and treats them like tokens in a sentence — learning spatial relationships across the whole image.

This model is fine-tuned on **Food-101** — a benchmark dataset of 101,000 food images across 101 categories.

### Classification Pipeline

```
User uploads image
        ↓
validate_image()        ← file type, size, corruption check
        ↓
preprocess_image()      ← convert to RGB PIL image
        ↓
AutoImageProcessor      ← resize & normalise for ViT input
        ↓
ViT Model inference     ← forward pass (no_grad)
        ↓
Softmax → Top-5 probs   ← confidence scores per class
        ↓
_map_label()            ← Food-101 label → our DB key
        ↓
calculate_nutrition()   ← look up foods.json, scale to serving
```

### Confidence Thresholds

| Badge | Confidence | Meaning |
|-------|-----------|---------|
| 🟢 **High** | > 50% | Strong prediction — likely correct |
| 🟡 **Medium** | 20–50% | Reasonable — worth verifying |
| 🔴 **Low** | < 15% | Uncertain — please select manually |

If the model fails to load (no internet on first run), the app switches to **Fallback Mode** — full manual selection with complete nutritional data still available.

---

## 🍱 Food Database

21 foods sourced from **ICMR** and **USDA FoodData Central**:

### 🇮🇳 Indian Foods (12)
`Idli` · `Dosa` · `Plain Rice` · `Biryani` · `Chapati/Roti` · `Dal` · `Paneer Curry` · `Samosa` · `Poha` · `Upma` · `Chicken Curry` · `Curd/Yogurt`

### 🌍 International Foods (9)
`Pizza` · `Burger` · `Pasta` · `Sandwich` · `Salad` · `Apple` · `Banana` · `Eggs` · `Oatmeal`

**Formula:** `nutrient = (nutrient_per_100g × serving_g) / 100`

---

## 🚀 Getting Started

### Prerequisites

- Python 3.10 or higher
- Internet connection (first run downloads the AI model — ~350 MB)
- ~2 GB free disk space

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/thecountershadow/Food-Calorie-Estimation-system.git
cd Food-Calorie-Estimation-system

# 2. Create virtual environment
python -m venv venv

# 3. Activate it
# Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# macOS/Linux:
source venv/bin/activate

# 4. Install dependencies
pip install -r requirements.txt
```

> **CPU-only PyTorch (faster install):**
> ```bash
> pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
> ```

### Run the App

```powershell
# Windows
$env:PYTHONIOENCODING="utf-8"
.\venv\Scripts\streamlit.exe run app.py
```

```bash
# macOS / Linux
streamlit run app.py
```

The app opens automatically at **http://localhost:8501**

> **Note:** The AI model downloads on first use (~350 MB). Subsequent runs load from cache instantly.

---

## 🧪 Running Tests

```bash
python tests/test_suite.py
```

Expected output:
```
Ran 36 tests in ~0.6s
OK
```

### Test Coverage

| Group | Tests | What's Covered |
|-------|-------|----------------|
| Nutrition Calculations | 13 | DB loading, `calculate_nutrition()`, proportional scaling, search, macro % |
| Database Operations | 11 | Table creation, CRUD, daily/weekly totals, settings, edge cases |
| Image Validation | 5 | Valid PNG, bad extension, file too large, corrupt file, RGB conversion |
| Label Mapping | 4 | Exact match, unknown label, keyword partial match |
| Fallback Mode | 1 | AI unavailable → correct fallback response |

---

## 📱 App Pages

| Page | Description |
|------|-------------|
| 🏠 **Dashboard** | Today's calories, macros, progress bar, recent meals |
| 🔍 **Analyze Food** | Upload image → AI classify → adjust serving → log meal |
| 📋 **Meal History** | Browse, edit, delete meals by date |
| 📊 **Analytics** | Weekly chart, macro donut, calorie gauge, summary tables |
| ⚙️ **Settings** | Daily target, AI model info, data reset |

---

## ⚠️ Limitations

- The ViT model is trained on **Food-101** which is predominantly Western foods. Some Indian dishes (Idli, Biryani) may not be directly classified — keyword fallback and manual selection cover these cases.
- Nutritional values are **estimates** based on standard reference data. Actual values vary by recipe, ingredients, and preparation method.
- This is a **local desktop application** — not deployed to a cloud server.
- The AI classifier covers ~21 foods mapped to our nutrition DB, out of 101 Food-101 categories.

---

## 🤝 Contributing

Contributions are welcome! Here's how:

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Commit your changes: `git commit -m "Add your feature"`
4. Push to the branch: `git push origin feature/your-feature`
5. Open a Pull Request

Please ensure all 36 tests still pass before submitting a PR.

---

## 📄 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

---

## 👨‍💻 Author

**thecountershadow**
- GitHub: [@thecountershadow](https://github.com/thecountershadow)

---

<div align="center">

**Built with ❤️ as a college AI/ML project**

*Python · Streamlit · PyTorch · Hugging Face · SQLite · Plotly*

⭐ Star this repo if you found it helpful!

</div>
