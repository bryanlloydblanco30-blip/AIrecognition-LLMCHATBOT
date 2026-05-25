import os
import random
import shutil
import subprocess
import sys
from pathlib import Path

def balance_dataset(train_dir, target_count=2000):
    """
    Perform random oversampling and undersampling on the training directory
    to ensure every class has exactly target_count images.
    """
    print(f"\n[BALANCE] Balancing training dataset to {target_count} images per class...")
    
    classes = [c for c in os.listdir(train_dir) if os.path.isdir(os.path.join(train_dir, c))]
    
    for cls in classes:
        cls_dir = os.path.join(train_dir, cls)
        images = [f for f in os.listdir(cls_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        current_count = len(images)
        print(f"  - {cls}: currently has {current_count} images")
        
        if current_count > target_count:
            # Undersample: keep only target_count random images
            random.seed(42)
            to_remove = random.sample(images, current_count - target_count)
            for f in to_remove:
                os.remove(os.path.join(cls_dir, f))
            print(f"    [CUT] Undersampled down to {target_count} images (removed {len(to_remove)}).")
            
        elif current_count < target_count:
            # Oversample: duplicate images randomly until we reach target_count
            random.seed(42)
            additional_needed = target_count - current_count
            duplicated = 0
            
            while duplicated < additional_needed:
                orig_img = random.choice(images)
                orig_path = os.path.join(cls_dir, orig_img)
                name, ext = os.path.splitext(orig_img)
                new_img_name = f"dup_{duplicated}_{name}{ext}"
                new_path = os.path.join(cls_dir, new_img_name)
                shutil.copy2(orig_path, new_path)
                duplicated += 1
                
            print(f"    [ADD] Oversampled up to {target_count} images (duplicated {duplicated}).")
            
    print("[OK] Training dataset balancing complete!")

def main():
    root_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(root_dir)
    
    # print("=" * 60)
    # print("Step 1: Re-creating train/val splits from dataset...")
    # print("=" * 60)
    # subprocess.run([sys.executable, "create_splits.py"], check=True)
    
    # print("=" * 60)
    # print("Step 2: Balancing type classes to remove AI camera bias...")
    # print("=" * 60)
    # train_dir = os.path.join("backend", "trash-uibackend", "data", "types_split", "train")
    # balance_dataset(train_dir, target_count=2000)
    
    print("=" * 60)
    print("Step 3: Training Master Type Classifier (type_classifier.pt)...")
    print("=" * 60)
    
    # Delete existing type_classifier runs directory so it won't auto-increment
    runs_type = os.path.join("runs", "classify", "type_classifier")
    if os.path.exists(runs_type):
        shutil.rmtree(runs_type)
        print(f"  [CLEAN] Removed old training run at {runs_type}")
    
    yolo_cmd = (
        "yolo classify train "
        "model=yolo11n-cls.pt "
        "data=\"backend/trash-uibackend/data/types_split\" "
        "epochs=50 "
        "imgsz=224 "
        "name=type_classifier "
        "batch=32 "
        "exist_ok=True"
    )
    print(f"  Running: {yolo_cmd}")
    result = subprocess.run(yolo_cmd, shell=True)
    
    if result.returncode == 0:
        src = os.path.join("runs", "classify", "type_classifier", "weights", "best.pt")
        dst = os.path.join("models", "type_classifier.pt")
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy2(src, dst)
        print(f"\n[OK] Type classifier trained and saved to {dst}!\n")
    else:
        print("\n[WARN] Type classifier training failed!\n")
        
    print("=" * 60)
    print("Step 4: Training category-specific classifiers...")
    print("=" * 60)
    subprocess.run([sys.executable, "train_all_categories.py"], check=True)
    
    print("=" * 60)
    print("Step 5: Consolidating all final models...")
    print("=" * 60)
    subprocess.run([sys.executable, "check_and_copy_models.py"], check=True)
    
    print("\n" + "=" * 60)
    print("[DONE] ALL AI RETRAINING COMPLETE! Models updated successfully.")
    print("=" * 60 + "\n")

if __name__ == "__main__":
    main()
