import cv2
import numpy as np
from core.sort import Sort
from core.detector import ObjectDetector

model_path = "models/yolov8m.pt"
video_path = "videos/video1.mp4"

detector = ObjectDetector(model_path, device="cuda")

tracker = Sort(max_age=15, min_hits=2, iou_threshold=0.15) #sort default max_age=5,treshold=0.3


cap = cv2.VideoCapture(video_path)

while True:
    ret, frame = cap.read()
    if not ret:
        break


    results = detector.detect(frame, conf=0.3, imgsz=1088)

    detections = []  # SORT format [x1, y1, x2, y2, conf]

    for result in results:
        for box in result.boxes:
            #if int(box.cls) is not None:  #burayı düzenle
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                conf = box.conf[0].cpu().numpy()

                detections.append([x1, y1, x2, y2, conf])

    if len(detections) > 0:
        detections = np.array(detections)
    else:
        detections = np.empty((0, 5))

    tracked_objects = tracker.update(detections) #sort track

    #TODO kaybolan kutucuklar yeni kimlikle ortaya cıkıyor
    for obj in tracked_objects: #islemleri yazdirma
        x1, y1, x2, y2, track_id = obj.astype(int)
        cv2.rectangle(frame, (x1, y1), (x2, y2), color=(0, 255, 0), thickness=2)
        cv2.putText(frame, f'ID {track_id}', (x1, y1 - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 0, 0), 2)

    #width, height = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))


    # Görüntüyü yeniden boyutlandır
    resized_img = cv2.resize(frame, (1000, 1000))
    cv2.imshow("YOLOv8 + SORT Tracking", frame)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()
