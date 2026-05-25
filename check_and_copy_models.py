#!/usr/bin/env python3
"""
Monitor training and copy all completed models to models/ directory.
Run this periodically to check if all trainings are done.
"""
import os
import shutil
from pathlib import Path

def copy_models():
    """Copy all trained category models to models/ directory."""
    root_dir = os.path.dirname(os.path.abspath(__file__))
    base_runs = os.path.join(root_dir, "runs", "classify")
    models_dir = os.path.join(root_dir, "models")
    Path(models_dir).mkdir(parents=True, exist_ok=True)
    
    categories = ["metal", "organic", "paper", "plastic", "non_organic"]
    all_done = True
    
    for category in categories:
        train_dir = os.path.join(base_runs, f"category_{category}")
        weights_best = os.path.join(train_dir, "weights", "best.pt")
        dst = os.path.join(models_dir, f"category_{category}.pt")
        
        if os.path.exists(weights_best):
            # Check if results.csv has 30 epochs (31 lines = header + 30 epochs)
            results_csv = os.path.join(train_dir, "results.csv")
            if os.path.exists(results_csv):
                with open(results_csv) as f:
                    epochs = len(f.readlines()) - 1  # -1 for header
                
                if epochs >= 10:
                    print(f"[OK] {category.capitalize()}: {epochs} epochs complete")
                    if not os.path.exists(dst) or os.path.getmtime(weights_best) > os.path.getmtime(dst):
                        shutil.copy2(weights_best, dst)
                        print(f"   Copied to {dst}")
                else:
                    print(f"[WAIT] {category.capitalize()}: {epochs}/10 epochs")
                    all_done = False
            else:
                print(f"❌ {category.capitalize()}: No results.csv yet")
                all_done = False
        else:
            print(f"[WAIT] {category.capitalize()}: Training not started")
            all_done = False
    
    if all_done:
        print("\n[OK] All trainings complete! Models ready in models/ directory:")
        for f in sorted(os.listdir(models_dir)):
            if f.endswith('.pt'):
                size = os.path.getsize(os.path.join(models_dir, f)) / (1024*1024)
                print(f"  - {f} ({size:.1f} MB)")
    else:
        print("\n[WAIT] Some trainings still in progress. Check again later.")
    
    return all_done

if __name__ == "__main__":
    copy_models()
