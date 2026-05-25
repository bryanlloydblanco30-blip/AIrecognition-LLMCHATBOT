#!/usr/bin/env python3
"""
Create train/val splits for:
1. Top-level type classifier (Metal, Organic, Paper, Plastic, Non_Organic)
   - Flatten all images from each type's categories into type folders
2. Category classifiers for each type
"""
import os
import shutil
import random
from pathlib import Path

def flatten_type_images(source_dir, output_dir):
    """Flatten all images from type's subdirectories into type folder."""
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    for item in os.listdir(source_dir):
        item_path = os.path.join(source_dir, item)
        if not os.path.isdir(item_path):
            # It's a file, copy directly
            dst = os.path.join(output_dir, item)
            shutil.copy2(item_path, dst)
        else:
            # It's a subdirectory, recurse to get all images
            for file in os.listdir(item_path):
                file_path = os.path.join(item_path, file)
                if os.path.isfile(file_path) and file.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp', '.webp')):
                    dst = os.path.join(output_dir, file)
                    if not os.path.exists(dst):  # Don't overwrite
                        shutil.copy2(file_path, dst)

def split_dataset(source_dir, output_dir, train_ratio=0.8, seed=42):
    """Split a dataset directory into train/val subdirectories."""
    random.seed(seed)
    
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    train_dir = os.path.join(output_dir, "train")
    val_dir = os.path.join(output_dir, "val")
    
    # For each class folder in source_dir
    class_dirs = {}
    for item in os.listdir(source_dir):
        item_path = os.path.join(source_dir, item)
        if os.path.isdir(item_path):
            class_dirs[item] = item_path
    
    for class_name, class_path in class_dirs.items():
        # Create train/val subdirectories for this class
        train_class_dir = os.path.join(train_dir, class_name)
        val_class_dir = os.path.join(val_dir, class_name)
        Path(train_class_dir).mkdir(parents=True, exist_ok=True)
        Path(val_class_dir).mkdir(parents=True, exist_ok=True)
        
        # Get all image files (recursively for nested structure)
        images = []
        for root, dirs, files in os.walk(class_path):
            for f in files:
                if f.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp', '.webp')):
                    images.append(os.path.join(root, f))
        
        if not images:
            print(f"  {class_name}: 0 images found")
            continue
        
        # Shuffle and split
        random.shuffle(images)
        split_idx = int(len(images) * train_ratio)
        train_images = images[:split_idx]
        val_images = images[split_idx:]
        
        # Copy to train
        for src in train_images:
            dst = os.path.join(train_class_dir, os.path.basename(src))
            shutil.copy2(src, dst)
        
        # Copy to val
        for src in val_images:
            dst = os.path.join(val_class_dir, os.path.basename(src))
            shutil.copy2(src, dst)
        
        print(f"  {class_name}: {len(train_images)} train, {len(val_images)} val")

def main():
    # Dynamically find the project root directory
    root_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(root_dir, "backend", "trash-uibackend", "data")
    base_path = os.path.join(data_dir, "Cleaned Dataset")
    
    # 1. Create splits for top-level types (flattened)
    print("Creating type-level splits (flattened)...")
    types_flat_source = os.path.join(data_dir, "types_flat")
    Path(types_flat_source).mkdir(parents=True, exist_ok=True)
    
    main_types = ["Metal", "Non_Organic", "Organic", "Paper", "Plastic"]
    
    for type_name in main_types:
        src_type = os.path.join(base_path, type_name)
        dst_type = os.path.join(types_flat_source, type_name)
        print(f"  Flattening {type_name}...")
        flatten_type_images(src_type, dst_type)
    
    types_output = os.path.join(data_dir, "types_split")
    print(f"\nSplitting types into train/val at {types_output}...")
    split_dataset(types_flat_source, types_output, train_ratio=0.8)
    print()
    
    # 2. Create splits for each type's categories (with recursive image search)
    print("Creating category-level splits for each type...")
    for type_name in main_types:
        type_path = os.path.join(base_path, type_name)
        if not os.path.isdir(type_path):
            print(f"  Skipping {type_name} (not found)")
            continue
        
        category_output = os.path.join(data_dir, f"category_{type_name.lower()}_split")
        print(f"  {type_name}:")
        split_dataset(type_path, category_output, train_ratio=0.8)
    
    print("\nAll splits created successfully!")
    print(f"Type classifier data: {types_output}")
    print(f"Category classifiers: data/category_<type>_split/")

if __name__ == "__main__":
    main()
