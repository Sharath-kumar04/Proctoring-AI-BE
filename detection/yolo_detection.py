import cv2
import torch
from datetime import datetime  # Add this import

# Load YOLO model
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = torch.hub.load("ultralytics/yolov5", "yolov5s", pretrained=True).to(device)

def detect_yolo(frame):
    logs = []
    timestamp = str(datetime.now())  # Use system's timestamp
    results = model(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    print(f"YOLO results: {results}")
    for detection in results.xyxy[0]:
        print(f"Detection: {detection}")
        if len(detection) < 6:
            print("Invalid detection format")
            continue
        label = results.names[int(detection[5])]
        print(f"Detection label: {label}")
        if label == "cell phone":
            logs.append({"time": timestamp, "event": "Phone detected"})
        elif label == "person" and len(results.xyxy[0]) > 1:
            logs.append({"time": timestamp, "event": "Background person detected"})
    return logs
