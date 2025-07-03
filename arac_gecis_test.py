import cv2
import numpy as np
from core.detector import ObjectDetector
from deep_sort_realtime.deepsort_tracker import DeepSort

from core.arac_yol import Yol_Secici

model_path = "models/yolov8m.pt"
video_path = "videos/video1.mp4"
mask_path = "masks/mask1.png"

roi_mask = cv2.imread(mask_path, cv2.IMREAD_GRAYSCALE)
if roi_mask.max() > 1:
    _, roi_mask = cv2.threshold(roi_mask, 127, 255, cv2.THRESH_BINARY)

detector = ObjectDetector(model_path, device="cuda")
tracker = DeepSort(max_age=15, n_init=2, nms_max_overlap=0.7, max_cosine_distance=0.2)

cap = cv2.VideoCapture(video_path)

yol_secim = Yol_Secici()
cv2.namedWindow("DeepSORT")
cv2.setMouseCallback("DeepSORT", yol_secim.mouse_callback)

track_memory = {}
ihlal = set()
while True:
    ret, frame = cap.read()
    if not ret:
        break

    if (roi_mask.shape[0] != frame.shape[0]) or (roi_mask.shape[1] != frame.shape[1]):
        roi_mask = cv2.resize(roi_mask, (frame.shape[1], frame.shape[0]), interpolation=cv2.INTER_NEAREST)
    masked_frame = cv2.bitwise_and(frame, frame, mask=roi_mask)

    results = detector.detect(masked_frame, conf=0.3, imgsz=640, iou=0.42)

    detections = []
    for result in results:
        for box in result.boxes:
            x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
            conf = box.conf[0].cpu().numpy()
            cls = int(box.cls[0].cpu().numpy())
            detections.append(([x1, y1, x2 - x1, y2 - y1], conf, cls))

    tracks = tracker.update_tracks(detections, frame=frame)

    alive_cars = []

    for track in tracks:
        if not track.is_confirmed():
            continue

        track_id = track.track_id
        alive_cars.append(track_id)
        ltrb = track.to_ltrb()
        x1, y1, x2, y2 = map(int, ltrb)
        cx, cy = (x1 + x2) // 2, (y1 + y2) // 2

        if len(yol_secim.corridors) > 0:
            if track_id in track_memory:
                prev_cx, prev_cy = track_memory[track_id]

                for corridor in yol_secim.corridors:
                    if Yol_Secici.is_crossing_line( #giris kontrol
                        (cx, cy), (prev_cx, prev_cy), corridor.entry_line):
                        if track_id not in corridor.entered_ids:
                            corridor.entered_ids.add(track_id)
                            print(f" {track_id} girişini {corridor.entry_line} yoluna yaptı")
                    #cikis kontrol
                    if track_id in corridor.entered_ids and track_id not in corridor.exited_ids:
                        if Yol_Secici.is_crossing_line(
                            (cx, cy), (prev_cx, prev_cy), corridor.exit_line):
                            corridor.exited_ids.add(track_id)
                            print(f" {track_id} çıkışını {corridor.exit_line} yoluna yaptı")

            track_memory[track_id] = (cx, cy)

        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
        cv2.putText(frame, f'ID {track_id}', (x1, y1 - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 0, 0), 2)

    # her döngü sonrası ihlal kontrolleri
    for corridor in yol_secim.corridors:
        for entered_id in list(corridor.entered_ids):
            if entered_id not in alive_cars and entered_id not in corridor.exited_ids:
                if entered_id not in ihlal:
                    ihlal.add(entered_id)
                    print(f"Ihlal: {entered_id}")


    yol_secim.draw_corridors(frame)

    y_offset = 30
    for idx, corridor in enumerate(yol_secim.corridors):
        cv2.putText(frame, f'Corridor {idx+1} Entered: {len(corridor.entered_ids)} Exited: {len(corridor.exited_ids)}',
                    (10, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        y_offset += 30

    cv2.imshow("DeepSORT", frame)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        print(ihlal)
        break


cap.release()
cv2.destroyAllWindows()
