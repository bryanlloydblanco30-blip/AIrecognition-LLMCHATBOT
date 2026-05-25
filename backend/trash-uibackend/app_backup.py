"""
Hierarchical trash classification backend.
Two-level inference: Type classifier -> Category classifier
"""
from fastapi import FastAPI, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from ultralytics import YOLO
import tempfile
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Type classifier - predicts: Metal, Organic, Paper, Plastic, Non_Organic
type_model = None

# Category classifiers - one for each type
category_models = {
    "Metal": None,
    "Organic": None,
    "Paper": None,
    "Plastic": None,
    "Non_Organic": None,
}

def load_models():
    """Load all required models."""
    global type_model, category_models
    
    models_dir = "models"
    
    # Load type classifier
    type_model_path = os.path.join(models_dir, "type_classifier.pt")
    if os.path.exists(type_model_path):
        type_model = YOLO(type_model_path)
        print(f"✅ Loaded type classifier: {type_model_path}")
    else:
        print(f"⚠️  Type classifier not found: {type_model_path}")
    
    # Load category classifiers for each type
    for trash_type in category_models.keys():
        category_path = os.path.join(models_dir, f"category_{trash_type.lower()}.pt")
        if os.path.exists(category_path):
            category_models[trash_type] = YOLO(category_path)
            print(f"✅ Loaded {trash_type} classifier: {category_path}")
        else:
            print(f"⚠️  {trash_type} classifier not found: {category_path}")

@app.on_event("startup")
async def startup_event():
    """Load models on startup."""
    load_models()

@app.get("/")
def root():
    return {
        "status": "running",
        "type_model": "loaded" if type_model else "not found",
        "category_models": {k: "loaded" if v else "not found" for k, v in category_models.items()}
    }

@app.post("/predict")
async def predict(file: UploadFile):
    """
    Hierarchical inference:
    1. Predict trash type (Metal, Organic, Paper, Plastic, Non_Organic)
    2. Predict category within that type
    3. Return: type, category, type_confidence, category_confidence
    """
    if not type_model:
        raise HTTPException(status_code=500, detail="Type model not loaded")
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as f:
        f.write(await file.read())
        temp_path = f.name
    
    try:
        # Step 1: Predict type
        type_results = type_model.predict(temp_path)
        type_idx = type_results[0].probs.top1
        predicted_type = type_results[0].names[type_idx]
        type_confidence = float(type_results[0].probs.top1conf)
        
        # Step 2: Predict category within the type
        category = "Unknown"
        category_confidence = 0.0
        
        if predicted_type in category_models and category_models[predicted_type]:
            category_model = category_models[predicted_type]
            category_results = category_model.predict(temp_path)
            category_idx = category_results[0].probs.top1
            category = category_results[0].names[category_idx]
            category_confidence = float(category_results[0].probs.top1conf)
        
        return {
            "type": predicted_type,
            "category": category,
            "type_confidence": round(type_confidence, 4),
            "category_confidence": round(category_confidence, 4),
        }
    
    finally:
        # Clean up temp file
        if os.path.exists(temp_path):
            os.remove(temp_path)
