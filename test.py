import cv2
import numpy as np
from core.detector import ObjectDetector
#from core.control import KeyboardController

from deep_sort_realtime.deepsort_tracker import DeepSort

model_path = "models/yolov8m.pt"
video_path = "videos/video1.mp4"
mask_path = "masks/mask1.png"

roi_mask = cv2.imread(mask_path, cv2.IMREAD_GRAYSCALE)
if roi_mask.max() > 1:
    _, roi_mask = cv2.threshold(roi_mask, 127, 255, cv2.THRESH_BINARY)
detector = ObjectDetector(model_path, device="cuda")

tracker = DeepSort(max_age=15, n_init=2, nms_max_overlap=0.7, max_cosine_distance=0.2) #nms max overlap degistir

cap = cv2.VideoCapture(video_path)

while True:
    ret, frame = cap.read()
    if not ret:
        break
    if (roi_mask.shape[0] != frame.shape[0]) or (roi_mask.shape[1] != frame.shape[1]):
        roi_mask = cv2.resize(roi_mask, (frame.shape[1], frame.shape[0]), interpolation=cv2.INTER_NEAREST)
    masked_frame = cv2.bitwise_and(frame, frame, mask=roi_mask)

    results = detector.detect(masked_frame, conf=0.3, imgsz=640,iou=0.42) #iou degisitr
    #fps = cap.get(cv2.CAP_PROP_FPS)

    detections = []  # [ [x1,y1,x2,y2,conf, cls], ... ]

    for result in results:
        for box in result.boxes:
            x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
            conf = box.conf[0].cpu().numpy()
            cls = int(box.cls[0].cpu().numpy())

            detections.append(([x1, y1, x2 - x1, y2 - y1], conf, cls))  # deepsort formatı: (coordinates,conf(oranı düsür), class)

    tracks = tracker.update_tracks(detections, frame=frame)

    for track in tracks:
        if not track.is_confirmed():
            continue
        track_id = track.track_id
        ltrb = track.to_ltrb()
        x1, y1, x2, y2 = map(int, ltrb)

        #with open("arackonum.txt", "a") as f:
        #    f.write(str(np.array([x1, y1, x2, y2,track_id])))
        #    f.write("\n")
        #f.close()


        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
        cv2.putText(frame, f'ID {track_id}', (x1, y1 - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 0, 0), 2)

    cv2.putText(frame, f'total araba {tracks.__len__()}', (10 ,30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 0, 0), 2)

    #controller = KeyboardController(cap, fps, skip_seconds=5)

    cv2.imshow("DeepSORT", frame)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()
