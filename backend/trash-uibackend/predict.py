from ultralytics import YOLO
import sys
import os

# Get models directory dynamically (two levels up from backend/trash-uibackend)
current_dir = os.path.dirname(os.path.abspath(__file__))
models_dir = os.path.join(os.path.dirname(os.path.dirname(current_dir)), "models")
model_path = os.path.join(models_dir, "metal_classifier.pt")

model = YOLO(model_path)

results = model.predict(sys.argv[1])

top = results[0].probs.top1
name = results[0].names[top]

print(name)