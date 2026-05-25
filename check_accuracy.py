import os
import random
from ultralytics import YOLO

def main():
    model = YOLO("models/type_classifier.pt")
    val_dir = "backend/trash-uibackend/data/types_split/val"
    
    classes = os.listdir(val_dir)
    print("Classes in validation set:", classes)
    
    correct = 0
    total = 0
    predictions_per_class = {c: {"correct": 0, "total": 0} for c in classes if os.path.isdir(os.path.join(val_dir, c))}
    
    # Gather a sample of 100 random validation images
    all_images = []
    for cls in classes:
        cls_dir = os.path.join(val_dir, cls)
        if not os.path.isdir(cls_dir):
            continue
        for img_name in os.listdir(cls_dir):
            if img_name.lower().endswith(('.png', '.jpg', '.jpeg')):
                all_images.append((os.path.join(cls_dir, img_name), cls))
                
    random.seed(42)
    sample = random.sample(all_images, min(100, len(all_images)))
    
    print(f"\nRunning validation test on {len(sample)} random images...\n")
    
    for img_path, true_label in sample:
        results = model.predict(img_path, verbose=False)
        top = results[0].probs.top1
        pred_label = results[0].names[top]
        
        is_correct = (pred_label.lower() == true_label.lower())
        if is_correct:
            correct += 1
            predictions_per_class[true_label]["correct"] += 1
        predictions_per_class[true_label]["total"] += 1
        total += 1
        
    print(f"Overall Accuracy: {correct}/{total} ({correct/total*100:.1f}%)")
    print("\nAccuracy per class:")
    for cls, stats in predictions_per_class.items():
        if stats["total"] > 0:
            acc = stats["correct"] / stats["total"] * 100
            print(f"  - {cls}: {stats['correct']}/{stats['total']} ({acc:.1f}%)")
        else:
            print(f"  - {cls}: No images tested")

if __name__ == "__main__":
    main()
