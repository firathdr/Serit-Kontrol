import cv2
from ultralytics import YOLO

import torch
print(torch.cuda.is_available())  # True

model = YOLO("models/yolov8s.pt")  # nano model

model.to('cuda')

cap = cv2.VideoCapture("videos/video1.mp4")
"""
detector = ObjectDetector("yolov8n.pt", device="cuda")
results = detector.detect(frame, conf=0.7, imgsz=(720, 1280))  
"""
while True:
    ret, frame = cap.read()
    if not ret:
        break

    results = model(frame, device='cuda')
    annotated_frame = results[0].plot()

    cv2.imshow("YOLOv8 CUDA", annotated_frame)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()
