"""
Hierarchical trash classification backend.
Two-level inference: Type classifier -> Category classifier

Dataset structure (as of current training data):
  Types:    Metal | Non_Organic | Organic | Paper | Plastic
  
  Metal       → Aluminum_Can, Bottle_Cap, Coat_Hanger, Foil,
                Metal_Utensils, Nails, Screws, Steel_Wire, Tin_Cans

  Non_Organic → Battery, Carton, E-Waste, Glass, Lightbulb
                NOTE: Glass is a CATEGORY under Non_Organic, not a top-level type.

  Organic     → Bread, Coffee_Grounds, Cooked_Food, Egg_Shells, Food_Scraps,
                Fruit_Peels, Garden_Trimmings, Leaves, Meat_Scraps, Rice,
                Tea_Bags, Vegetable_Cuttings

  Paper       → Bond_paper, Carton, Envelope, Gift_Wrapper, Magazine,
                Newspaper, Notebook_Paper, Paper_Cup, Tissue_Paper
                NOTE: Carton also appears in Non_Organic — potential label conflict.

  Plastic     → Plastic Bottle, Plastic Container, Plastic Wrapper

⚠️  Known data issues to fix before retraining:
    1. Remove Metal_split/ and runs/ from Cleaned Dataset_split/train & val
       — these are not real classes and will pollute the type classifier.
    2. Resolve Carton appearing in both Paper and Non_Organic
       — pick one or rename (e.g. "Paper_Carton" vs "Cardboard_Box").
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
# pyrefly: ignore [missing-import]
from ultralytics import YOLO
from PIL import Image, ImageEnhance
import tempfile
import os
import io

# ─────────────────────────────────────────────────────────────────────────────
# Configuration — tweak these without touching inference logic
# ─────────────────────────────────────────────────────────────────────────────

TYPE_THRESHOLD = 0.30       # below this → "Unrecognized"
CAT_THRESHOLD  = 0.25       # below this → "General <Type>"
MAX_FILE_SIZE  = 10 * 1024 * 1024      # 10 MB
TARGET_SIZE    = (640, 640)            # YOLO native input size
CONTRAST_BOOST = 1.2                   # mild contrast enhancement
ALLOWED_CONTENT_TYPES = {
    "image/jpeg", "image/png", "image/webp", "image/bmp"
}

# ─────────────────────────────────────────────────────────────────────────────
# Ground-truth category labels per type (mirrors your dataset exactly)
# Use these for validation / frontend hints — not used in inference itself.
# ─────────────────────────────────────────────────────────────────────────────

KNOWN_CATEGORIES: dict[str, list[str]] = {
    "Metal": [
        "Aluminum_Can", "Bottle_Cap", "Coat_Hanger", "Foil",
        "Metal_Utensils", "Nails", "Screws", "Steel_Wire", "Tin_Cans",
    ],
    "Non_Organic": [
        "Battery", "Carton", "E-Waste", "Glass", "Lightbulb",
    ],
    "Organic": [
        "Bread", "Coffee_Grounds", "Cooked_Food", "Egg_Shells", "Food_Scraps",
        "Fruit_Peels", "Garden_Trimmings", "Leaves", "Meat_Scraps", "Rice",
        "Tea_Bags", "Vegetable_Cuttings",
    ],
    "Paper": [
        "Bond_paper", "Paper_Carton", "Envelope", "Gift_Wrapper", "Magazine",
        "Newspaper", "Notebook_Paper", "Paper_Cup", "Tissue_Paper",
    ],
    "Plastic": [
        "Plastic Bottle", "Plastic Container", "Plastic Wrapper",
    ],
}

# Supported types — driven by KNOWN_CATEGORIES keys
SUPPORTED_TYPES = list(KNOWN_CATEGORIES.keys())

# ─────────────────────────────────────────────────────────────────────────────
# Model registry
# ─────────────────────────────────────────────────────────────────────────────

type_model = None
category_models: dict = {t: None for t in SUPPORTED_TYPES}


def get_models_dir() -> str:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(os.path.dirname(os.path.dirname(current_dir)), "models")


def load_models():
    global type_model, category_models

    models_dir = get_models_dir()
    print(f"\n📦 Loading YOLO models from: {models_dir}\n")

    type_path = os.path.join(models_dir, "type_classifier.pt")
    if os.path.exists(type_path):
        type_model = YOLO(type_path)
        print(f"✅ Type classifier loaded")
    else:
        print(f"⚠️  Type classifier NOT found: {type_path}")

    for trash_type in SUPPORTED_TYPES:
        cat_path = os.path.join(models_dir, f"category_{trash_type.lower()}.pt")
        if os.path.exists(cat_path):
            category_models[trash_type] = YOLO(cat_path)
            print(f"✅ [{trash_type:<12}] category model loaded  "
                  f"({len(KNOWN_CATEGORIES[trash_type])} classes)")
        else:
            print(f"⏳ [{trash_type:<12}] category model not found (optional)")
    print()


# ─────────────────────────────────────────────────────────────────────────────
# Lifespan
# ─────────────────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    load_models()
    yield


app = FastAPI(title="Group-6 Trash Classifier API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def preprocess_image(image_bytes: bytes, temp_path: str) -> str:
    """Resize to 640×640 and mildly boost contrast before inference."""
    with Image.open(io.BytesIO(image_bytes)) as img:
        img = img.convert("RGB")
        img = img.resize(TARGET_SIZE, Image.LANCZOS)
        img = ImageEnhance.Contrast(img).enhance(CONTRAST_BOOST)
        img.save(temp_path, format="JPEG", quality=95)
    return temp_path


def get_top3(results) -> list[dict]:
    """Return top-3 {label, confidence} from a YOLO classification result."""
    names = results[0].names
    probs = results[0].probs.data.tolist()
    ranked = sorted(
        [{"label": names[i], "confidence": round(probs[i], 4)} for i in range(len(probs))],
        key=lambda x: x["confidence"],
        reverse=True,
    )
    return ranked[:3]


# ─────────────────────────────────────────────────────────────────────────────
# Routes
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/")
def root():
    return {
        "status": "running",
        "thresholds": {"type": TYPE_THRESHOLD, "category": CAT_THRESHOLD},
        "supported_types": SUPPORTED_TYPES,
        "known_categories": KNOWN_CATEGORIES,
        "type_model": "loaded" if type_model else "not found",
        "category_models": {
            k: "loaded" if v else "not found"
            for k, v in category_models.items()
        },
    }


@app.get("/categories/{trash_type}")
def get_categories(trash_type: str):
    """Return the known category labels for a given type."""
    if trash_type not in KNOWN_CATEGORIES:
        raise HTTPException(
            status_code=404,
            detail=f"Unknown type '{trash_type}'. Valid: {SUPPORTED_TYPES}"
        )
    return {
        "type": trash_type,
        "categories": KNOWN_CATEGORIES[trash_type],
    }


@app.post("/predict")
async def predict(file: UploadFile):
    """
    Hierarchical inference:
      1. Validate file (content-type, size, readability)
      2. Preprocess image (resize 640×640 + contrast boost)
      3. Type prediction  → top-3 returned for debugging
      4. Category prediction within type → top-3 returned for debugging
      5. Return: type, category, confidences, top3_type, top3_category,
                 disposal_note (human-friendly hint)
    """
    if not type_model:
        raise HTTPException(status_code=500, detail="Type model not loaded")

    # File type guard
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{file.content_type}'. "
                   f"Allowed: {', '.join(sorted(ALLOWED_CONTENT_TYPES))}",
        )

    content = await file.read()

    # File size guard
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"File too large ({len(content)//1024} KB). "
                   f"Max allowed: {MAX_FILE_SIZE//1024} KB",
        )

    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as f:
        f.write(content)
        temp_path = f.name

    try:
        # Validate image is readable
        try:
            with Image.open(temp_path) as img:
                img_format  = img.format
                img_width, img_height = img.size
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Cannot read image: {e}")

        print(f"\n📥 Prediction request")
        print(f"   File  : {file.filename} ({len(content):,} bytes)")
        print(f"   Image : {img_width}×{img_height}  {img_format}")

        # Preprocess
        preprocess_image(content, temp_path)
        print(f"   Pre   : resized to {TARGET_SIZE[0]}×{TARGET_SIZE[1]}, "
              f"contrast ×{CONTRAST_BOOST}")

        # ── Step 1: Type ──────────────────────────────────────────────────
        type_results    = type_model.predict(temp_path, verbose=False)
        type_idx        = type_results[0].probs.top1
        raw_type        = type_results[0].names[type_idx]
        type_confidence = float(type_results[0].probs.top1conf)
        top3_type       = get_top3(type_results)

        print(f"\n   🔍 Type classifier  (threshold ≥ {TYPE_THRESHOLD}):")
        for i, e in enumerate(top3_type):
            marker = " ◀" if i == 0 else ""
            print(f"      #{i+1}  {e['label']:<14} {e['confidence']*100:5.1f}%{marker}")

        # Below type threshold → Unrecognized
        if type_confidence < TYPE_THRESHOLD:
            print(f"   [!] {type_confidence*100:.1f}% < {TYPE_THRESHOLD*100:.0f}% → Unrecognized")
            return {
                "type": "Unrecognized",
                "category": "Please try a clearer photo",
                "type_confidence": round(type_confidence, 4),
                "category_confidence": 0.0,
                "top3_type": top3_type,
                "top3_category": [],
                "disposal_note": "Could not classify. Try better lighting or a closer shot.",
            }

        predicted_type = raw_type

        # ── Step 2: Category ──────────────────────────────────────────────
        category            = "Unknown"
        category_confidence = 0.0
        top3_category       = []

        cat_model = category_models.get(predicted_type)

        if cat_model is None:
            category = "Category model not trained yet"
            print(f"   ⏳ No category model for {predicted_type}")
        else:
            cat_results         = cat_model.predict(temp_path, verbose=False)
            cat_idx             = cat_results[0].probs.top1
            raw_category        = cat_results[0].names[cat_idx]
            category_confidence = float(cat_results[0].probs.top1conf)
            top3_category       = get_top3(cat_results)

            print(f"\n   🔍 Category classifier [{predicted_type}]  "
                  f"(threshold ≥ {CAT_THRESHOLD}):")
            for i, e in enumerate(top3_category):
                marker = " ◀" if i == 0 else ""
                print(f"      #{i+1}  {e['label']:<22} {e['confidence']*100:5.1f}%{marker}")

            if category_confidence < CAT_THRESHOLD:
                category = f"General {predicted_type}"
                print(f"   [!] {category_confidence*100:.1f}% < "
                      f"{CAT_THRESHOLD*100:.0f}% → {category}")
            else:
                category = raw_category

        # Disposal hint (Glass lives under Non_Organic — call it out clearly)
        disposal_note = build_disposal_note(predicted_type, category)

        print(f"\n   ✅ {predicted_type} / {category}  "
              f"({type_confidence*100:.1f}% / {category_confidence*100:.1f}%)\n")

        return {
            "type": predicted_type,
            "category": category,
            "type_confidence": round(type_confidence, 4),
            "category_confidence": round(category_confidence, 4),
            "top3_type": top3_type,
            "top3_category": top3_category,
            "disposal_note": disposal_note,
        }

    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


def build_disposal_note(trash_type: str, category: str) -> str:
    """Return a short human-readable disposal hint based on type + category."""
    notes = {
        ("Non_Organic", "Glass"):     "Glass — dispose in a dedicated glass bin or recycling center.",
        ("Non_Organic", "Battery"):   "Battery — hazardous waste. Bring to an e-waste collection point.",
        ("Non_Organic", "E-Waste"):   "E-Waste — bring to an authorized e-waste recycling facility.",
        ("Non_Organic", "Lightbulb"): "Lightbulb — handle carefully; dispose at e-waste/hazardous collection.",
        ("Non_Organic", "Carton"):    "Carton — check if recyclable; dispose in recyclables bin.",
        ("Paper",       "Paper_Carton"): "Paper carton — flatten and place in paper recycling bin.",
        ("Metal",       "Aluminum_Can"): "Aluminum can — crush and place in metals recycling bin.",
        ("Plastic",     "Plastic Bottle"): "Plastic bottle — rinse and place in plastics recycling bin.",
    }
    fallback = {
        "Metal":       "Metal — place in metals recycling bin.",
        "Non_Organic": "Non-organic waste — check local guidelines for proper disposal.",
        "Organic":     "Organic — compost or place in organic waste bin.",
        "Paper":       "Paper — place in paper recycling bin.",
        "Plastic":     "Plastic — rinse and place in plastics recycling bin.",
    }
    return notes.get((trash_type, category), fallback.get(trash_type, "Dispose responsibly."))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)