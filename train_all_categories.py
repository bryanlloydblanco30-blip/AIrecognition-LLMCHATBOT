#!/usr/bin/env python3
"""
Train all category classifiers with 10 epochs (quick mode).
Run this to complete the model training.
"""
import os
import subprocess
import sys
import shutil

def train_category_models(root_dir):
    """Train all 5 category classifiers."""
    categories = [
        ("metal", "Metal"),
        ("organic", "Organic"),
        ("paper", "Paper"),
        ("plastic", "Plastic"),
        ("non_organic", "Non_Organic"),
    ]
    
    # Auto-detects device by omitting device=mps (Windows will use CUDA/CPU automatically)
    base_cmd = "yolo classify train model=yolo11n-cls.pt data=\"backend/trash-uibackend/data/category_{}_split\" epochs=10 imgsz=224 name=category_{} batch=32 exist_ok=True"
    
    for cat_lower, cat_title in categories:
        model_path = os.path.join(root_dir, "models", f"category_{cat_lower}.pt")
        
        # Skip if already trained
        if os.path.exists(model_path):
            print(f"[OK] {cat_title} classifier already exists at {model_path}")
            continue
        
        print(f"\n{'='*60}")
        print(f"Training {cat_title} Classifier ({cat_lower.upper()})")
        print(f"{'='*60}")
        
        # Delete old training run folder to prevent any collision
        run_folder = os.path.join(root_dir, "runs", "classify", f"category_{cat_lower}")
        if os.path.exists(run_folder):
            print(f"  [CLEAN] Removing old run folder: {run_folder}")
            shutil.rmtree(run_folder)
            
        cmd = base_cmd.format(cat_lower, cat_lower)
        result = subprocess.run(cmd, shell=True, cwd=root_dir)
        
        if result.returncode == 0:
            # Copy to models
            src = os.path.join(root_dir, "runs", "classify", f"category_{cat_lower}", "weights", "best.pt")
            dst = model_path
            if os.path.exists(src):
                # Ensure target directory exists
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                shutil.copy2(src, dst)
                print(f"[OK] Copied {cat_lower} model to {dst}")
        else:
            print(f"[WARN]  {cat_title} training failed with code {result.returncode}")
    
    print(f"\n{'='*60}")
    print("Training Complete!")
    print(f"{'='*60}")
    
    models_dir = os.path.join(root_dir, "models")
    if os.path.exists(models_dir):
        print("\nModels available in models/:")
        for f in sorted(os.listdir(models_dir)):
            if f.endswith(".pt"):
                size_mb = os.path.getsize(os.path.join(models_dir, f)) / (1024*1024)
                print(f"  [OK] {f} ({size_mb:.1f} MB)")

if __name__ == "__main__":
    # Dynamically find the root directory of this script
    root_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(root_dir)
    train_category_models(root_dir)
