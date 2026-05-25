"""
Trash Classifier - Full Training Script
Trains all 6 YOLO models sequentially on RTX 3050 4GB

Models trained:
  1. type_classifier        → Metal, Non_Organic, Organic, Paper, Plastic
  2. category_metal         → subcategories
  3. category_non_organic   → subcategories (includes Glass)
  4. category_organic       → subcategories
  5. category_paper         → subcategories
  6. category_plastic       → subcategories

Output: all .pt files copied to /models/ automatically
"""

import torch
import shutil
import os
from ultralytics import YOLO

# ─────────────────────────────────────────────
# Change working directory to this script's location (project root)
# ─────────────────────────────────────────────
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# ─────────────────────────────────────────────
# Sanity check — confirm GPU is visible
# ─────────────────────────────────────────────
print("\n🔍 Checking GPU...")
if not torch.cuda.is_available():
    print("❌ CUDA not available — training will fall back to CPU.")
    print("   Make sure you installed: pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118")
    device = "cpu"
else:
    print(f"✅ GPU found: {torch.cuda.get_device_name(0)}")
    print(f"   VRAM: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB")
    device = 0

# ─────────────────────────────────────────────
# Config — paths relative to FinalCognate root
# ─────────────────────────────────────────────

DATA_ROOT   = "backend/trash-uibackend/data"
MODELS_DIR  = "models"
BASE_MODEL  = "yolo11n-cls.pt"   # nano — fastest, good enough for classification

TRAIN_JOBS = [
    {
        "name":   "type_classifier",
        "data":   f"{DATA_ROOT}/types_split",
        "output": "type_classifier.pt",
    },
    {
        "name":   "category_metal",
        "data":   f"{DATA_ROOT}/category_metal_split",
        "output": "category_metal.pt",
    },
    {
        "name":   "category_non_organic",
        "data":   f"{DATA_ROOT}/category_non_organic_split",
        "output": "category_non_organic.pt",
    },
    {
        "name":   "category_organic",
        "data":   f"{DATA_ROOT}/category_organic_split",
        "output": "category_organic.pt",
    },
    {
        "name":   "category_paper",
        "data":   f"{DATA_ROOT}/category_paper_split",
        "output": "category_paper.pt",
    },
    {
        "name":   "category_plastic",
        "data":   f"{DATA_ROOT}/category_plastic_split",
        "output": "category_plastic.pt",
    },
]

# ─────────────────────────────────────────────
# Training settings tuned for RTX 3050 4GB
# ─────────────────────────────────────────────

TRAIN_ARGS = {
    "epochs":   50,
    "imgsz":    160,     # ⚡ 160 vs 224 = ~2x faster (pixels scale quadratically), minimal accuracy loss
    "batch":    64,      # ⚡ AMP halves VRAM usage, so 64 is safe on 4 GB
    "device":   device,
    "workers":  8,       # ⚡ Ryzen 5 5500U has 12 threads — use 8 for data loading
    "cache":    True,    # loads dataset into RAM — safe with 32 GB
    "patience": 15,      # early-stop if no improvement for 15 epochs
    "verbose":  True,
    "amp":      True,    # ⚡ mixed precision FP16 — ~2x GPU throughput on RTX 3050
    "optimizer": "AdamW", # ⚡ faster convergence than SGD default
    "lr0":      0.001,   # AdamW works best with lower learning rate
    "cos_lr":   True,    # cosine LR schedule — better final accuracy
}

# ─────────────────────────────────────────────
# Pre-flight: verify all data folders exist
# ─────────────────────────────────────────────
print("\n🗂  Verifying data folders...")
all_ok = True
for job in TRAIN_JOBS:
    exists = os.path.isdir(job["data"])
    status = "✅" if exists else "❌ MISSING"
    print(f"  {status}  {job['data']}")
    if not exists:
        all_ok = False

if not all_ok:
    print("\n❌ One or more data folders are missing. Fix paths and re-run.")
    raise SystemExit(1)

# ─────────────────────────────────────────────
# Create models output directory
# ─────────────────────────────────────────────

os.makedirs(MODELS_DIR, exist_ok=True)

# ─────────────────────────────────────────────
# Train all models sequentially
# ─────────────────────────────────────────────

results_summary = []

for i, job in enumerate(TRAIN_JOBS, 1):
    print(f"\n{'='*60}")
    print(f"  Training {i}/{len(TRAIN_JOBS)}: {job['name']}")
    print(f"  Data:   {job['data']}")
    print(f"  Output: {MODELS_DIR}/{job['output']}")
    print(f"{'='*60}\n")

    # Remove stale runs folder for this job to avoid exist_ok conflicts
    stale_run = os.path.join("runs", "classify", job["name"])
    if os.path.exists(stale_run):
        print(f"  🧹 Removing old run folder: {stale_run}")
        shutil.rmtree(stale_run)

    # Fresh model for each job
    model = YOLO(BASE_MODEL)

    model.train(
        data=job["data"],
        name=job["name"],
        **TRAIN_ARGS,
    )

    # Copy best weights to /models/
    best_weights = os.path.join("runs", "classify", job["name"], "weights", "best.pt")
    dest = os.path.join(MODELS_DIR, job["output"])

    if os.path.exists(best_weights):
        shutil.copy(best_weights, dest)
        print(f"\n✅ Saved: {dest}")
        results_summary.append((job["name"], "✅ done", dest))
    else:
        print(f"\n⚠️  Could not find weights at {best_weights}")
        results_summary.append((job["name"], "⚠️  weights not found", "-"))

# ─────────────────────────────────────────────
# Final summary
# ─────────────────────────────────────────────

print(f"\n{'='*60}")
print("  Training complete — summary")
print(f"{'='*60}")
for name, status, path in results_summary:
    print(f"  {status}  {name:<28} → {path}")

print(f"\n🚀 Restart your backend to load the new models:")
print(f"   uvicorn main:app --host 0.0.0.0 --port 8000 --reload\n")
