"""
food_classifier.py — Food image classification using a pretrained ViT model.

Model: nateraw/food (ViT fine-tuned on Food-101 + Indian foods via Hugging Face)
Fallback: If model loading fails, returns a clear FALLBACK_MODE flag so the UI
          can offer a manual food selector instead of silently lying.

Label mapping: maps model's Food-101 class labels to our nutrition DB keys.
"""

from __future__ import annotations

import io
import os
import logging
from typing import Optional

from PIL import Image

logger = logging.getLogger(__name__)

# ─── Model configuration ─────────────────────────────────────────────────────

# Primary model: ViT fine-tuned on Food-101
MODEL_ID = "nateraw/food"

# Map Food-101 labels (as returned by the model) → our nutrition DB keys.
# Only include labels that have an entry in foods.json.
LABEL_TO_FOOD_KEY: dict[str, str] = {
    # South Indian
    "dosa":             "dosa",
    "idli":             "idli",        # not in Food-101, covered by fallback
    # Rice / grain
    "rice":             "plain_rice",
    "fried_rice":       "plain_rice",
    "biryani":          "biryani",     # not in standard Food-101
    # Bread / roti
    "chapati":          "chapati",
    "naan":             "chapati",
    # Lentils
    "dal":              "dal",
    # Paneer
    "paneer":           "paneer_curry",
    "palak_paneer":     "paneer_curry",
    # Snacks
    "samosa":           "samosa",
    # Other Indian
    "poha":             "poha",
    "upma":             "upma",
    "chicken_curry":    "chicken_curry",
    # International
    "pizza":            "pizza",
    "hamburger":        "burger",
    "spaghetti_bolognese":  "pasta",
    "spaghetti_carbonara":  "pasta",
    "macaroni_and_cheese":  "pasta",
    "club_sandwich":    "sandwich",
    "grilled_cheese_sandwich": "sandwich",
    "hot_and_sour_soup": "salad",      # approximate
    "caesar_salad":     "salad",
    "greek_salad":      "salad",
    # Fruit
    "apple_pie":        "apple",
    "banana_foster":    "banana",
    # Eggs
    "eggs_benedict":    "eggs",
    "deviled_eggs":     "eggs",
    "huevos_rancheros": "eggs",
}

# A second broader fallback: partial-match keywords → food keys
KEYWORD_TO_FOOD_KEY: dict[str, str] = {
    "pizza":     "pizza",
    "burger":    "burger",
    "hamburger": "burger",
    "sandwich":  "sandwich",
    "salad":     "salad",
    "pasta":     "pasta",
    "spaghetti": "pasta",
    "rice":      "plain_rice",
    "egg":       "eggs",
    "banana":    "banana",
    "apple":     "apple",
    "chicken":   "chicken_curry",
    "curry":     "chicken_curry",
    "dosa":      "dosa",
    "idli":      "idli",
    "samosa":    "samosa",
    "chapati":   "chapati",
    "roti":      "chapati",
    "dal":       "dal",
    "naan":      "chapati",
    "biryani":   "biryani",
    "paneer":    "paneer_curry",
    "upma":      "upma",
    "poha":      "poha",
}

CONFIDENCE_THRESHOLD = 0.15   # below this we warn "low confidence"


# ─── Cached model loader ──────────────────────────────────────────────────────

_model_cache: dict = {}

def _load_model() -> tuple:
    """
    Load the ViT food classifier. Returns (processor, model, labels, True)
    on success, or (None, None, None, False) on failure.
    Uses an in-process cache so the model is loaded only once per session.
    """
    global _model_cache
    if "loaded" in _model_cache:
        return (
            _model_cache.get("processor"),
            _model_cache.get("model"),
            _model_cache.get("labels"),
            _model_cache.get("ok", False),
        )

    try:
        from transformers import AutoImageProcessor, AutoModelForImageClassification
        import torch

        logger.info(f"Loading model {MODEL_ID} …")
        processor = AutoImageProcessor.from_pretrained(MODEL_ID)
        model     = AutoModelForImageClassification.from_pretrained(MODEL_ID)
        model.eval()

        # Retrieve id2label mapping
        labels = model.config.id2label  # {0: "apple_pie", 1: "baby_back_ribs", …}

        _model_cache = {"processor": processor, "model": model, "labels": labels, "ok": True, "loaded": True}
        logger.info("Model loaded successfully.")
        return processor, model, labels, True

    except Exception as e:
        logger.warning(f"Model load failed: {e}")
        _model_cache = {"processor": None, "model": None, "labels": None, "ok": False, "loaded": True}
        return None, None, None, False


# ─── Public API ───────────────────────────────────────────────────────────────

def is_model_available() -> bool:
    """Return True if the model has loaded (or can load) successfully."""
    _, _, _, ok = _load_model()
    return ok


def classify_image(image: Image.Image, top_k: int = 5) -> dict:
    """
    Run food classification on a PIL Image.

    Returns a dict:
    {
        "success": bool,
        "fallback_mode": bool,      # True when model unavailable
        "predictions": [            # list of top-k dicts
            {"label": str, "food_key": str|None, "score": float},
            …
        ],
        "top_food_key": str|None,   # best matched DB key
        "top_label": str,
        "top_score": float,
        "low_confidence": bool,
        "error": str|None,
    }
    """
    processor, model, labels, ok = _load_model()

    if not ok:
        return {
            "success": False,
            "fallback_mode": True,
            "predictions": [],
            "top_food_key": None,
            "top_label": "Unknown",
            "top_score": 0.0,
            "low_confidence": True,
            "error": "AI model could not be loaded. Please select food manually.",
        }

    try:
        import torch

        # Preprocess
        inputs = processor(images=image, return_tensors="pt")

        with torch.no_grad():
            outputs = model(**inputs)
            logits  = outputs.logits

        probs   = torch.softmax(logits, dim=-1)[0]
        top_probs, top_idxs = torch.topk(probs, min(top_k, len(labels)))

        predictions = []
        for prob, idx in zip(top_probs.tolist(), top_idxs.tolist()):
            raw_label = labels[idx].lower().replace(" ", "_")
            food_key  = _map_label(raw_label)
            predictions.append({
                "label":    labels[idx],
                "food_key": food_key,
                "score":    round(prob, 4),
            })

        top = predictions[0]
        return {
            "success":      True,
            "fallback_mode": False,
            "predictions":  predictions,
            "top_food_key": top["food_key"],
            "top_label":    top["label"],
            "top_score":    top["score"],
            "low_confidence": top["score"] < CONFIDENCE_THRESHOLD,
            "error":        None,
        }

    except Exception as e:
        logger.error(f"Inference error: {e}")
        return {
            "success": False,
            "fallback_mode": False,
            "predictions": [],
            "top_food_key": None,
            "top_label": "Error",
            "top_score": 0.0,
            "low_confidence": True,
            "error": f"Inference failed: {e}",
        }


def _map_label(raw_label: str) -> Optional[str]:
    """
    Map a model label to a nutrition DB key.
    First tries exact LABEL_TO_FOOD_KEY, then keyword matching.
    """
    # Exact match
    if raw_label in LABEL_TO_FOOD_KEY:
        return LABEL_TO_FOOD_KEY[raw_label]

    # Keyword partial match
    for keyword, food_key in KEYWORD_TO_FOOD_KEY.items():
        if keyword in raw_label:
            return food_key

    return None  # unsupported / unknown label


def validate_image(file_bytes: bytes, filename: str) -> tuple[bool, str]:
    """
    Validate an uploaded image file.
    Returns (is_valid, error_message).
    """
    MAX_SIZE_MB = 10
    ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png"}

    ext = os.path.splitext(filename.lower())[1]
    if ext not in ALLOWED_EXTENSIONS:
        return False, f"Unsupported file type '{ext}'. Please upload JPG, JPEG, or PNG."

    if len(file_bytes) > MAX_SIZE_MB * 1024 * 1024:
        return False, f"File too large ({len(file_bytes)//1024//1024} MB). Maximum is {MAX_SIZE_MB} MB."

    try:
        img = Image.open(io.BytesIO(file_bytes))
        img.verify()
    except Exception:
        return False, "Could not open the image. The file may be corrupt."

    return True, ""


def preprocess_image(file_bytes: bytes) -> Image.Image:
    """Convert uploaded bytes to a PIL RGB image ready for inference."""
    img = Image.open(io.BytesIO(file_bytes)).convert("RGB")
    return img
