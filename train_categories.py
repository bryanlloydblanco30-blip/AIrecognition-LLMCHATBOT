"""
Retrain category_organic and category_paper to hit 90%+.
25 epochs, patience=5, all GPU optimizations ON.
"""
import torch, shutil, os
from ultralytics import YOLO

os.chdir(os.path.dirname(os.path.abspath(__file__)))

device = 0 if torch.cuda.is_available() else "cpu"
print(f"\n GPU: {torch.cuda.get_device_name(0) if device==0 else 'CPU'}\n")

DATA_ROOT  = "backend/trash-uibackend/data"
MODELS_DIR = "models"
BASE_MODEL = "yolo11n-cls.pt"

JOBS = [
    {"name": "category_organic", "data": f"{DATA_ROOT}/category_organic_split", "output": "category_organic.pt"},
    {"name": "category_paper",   "data": f"{DATA_ROOT}/category_paper_split",   "output": "category_paper.pt"},
]

ARGS = dict(
    epochs   = 25,
    patience = 5,
    imgsz    = 160,
    batch    = 64,
    device   = device,
    workers  = 8,
    cache    = True,
    verbose  = True,
    amp      = True,
    optimizer= "AdamW",
    lr0      = 0.001,
    cos_lr   = True,
)

os.makedirs(MODELS_DIR, exist_ok=True)
summary = []

for i, job in enumerate(JOBS, 1):
    print(f"\n{'='*55}")
    print(f"  {i}/{len(JOBS)}: {job['name']}  (25 epochs, target >90%)")
    print(f"{'='*55}\n")

    stale = os.path.join("runs", "classify", job["name"])
    if os.path.exists(stale):
        shutil.rmtree(stale)

    YOLO(BASE_MODEL).train(data=job["data"], name=job["name"], **ARGS)

    best = os.path.join("runs", "classify", job["name"], "weights", "best.pt")
    dest = os.path.join(MODELS_DIR, job["output"])

    if os.path.exists(best):
        shutil.copy(best, dest)
        size_mb = os.path.getsize(dest) / 1024**2
        print(f"\n [SAVED] {dest}  ({size_mb:.1f} MB)")
        summary.append((job["name"], "DONE", dest))
    else:
        summary.append((job["name"], "FAILED", "-"))

print(f"\n{'='*55}")
print("  RETRAIN COMPLETE")
print(f"{'='*55}")
for name, status, path in summary:
    print(f"  [{status}]  {name:<28} -> {path}")
print()
