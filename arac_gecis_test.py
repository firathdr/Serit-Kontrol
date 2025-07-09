import cv2
import numpy as np
import json
from core.detector import ObjectDetector
from deep_sort_realtime.deepsort_tracker import DeepSort
from core.arac_yol import Yol_Secici
from database.ihlal_ekle import ihlal_ekle_db

#import subprocess
# yt-dlp -g 'https://www.youtube.com/watch?v=ByED80IKdIU&ab_channel=CityofColdwaterMI'  #canlı video kullanımı için


model_path = "models/yolov8m.pt"
video_path = "videos/video1.mp4"
mask_path = "masks/mask1.png"

roi_mask = cv2.imread(mask_path, cv2.IMREAD_GRAYSCALE)
if roi_mask.max() > 1:
    _, roi_mask = cv2.threshold(roi_mask, 127, 255, cv2.THRESH_BINARY)

detector = ObjectDetector(model_path, device="cuda")
tracker = DeepSort(max_age=15, n_init=2, nms_max_overlap=0.7, max_cosine_distance=0.2)

cap = cv2.VideoCapture(video_path) # + cv2.CAP_FFMPEG =canlı videolar için eklenir

genislik = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
yukseklik = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

yol_secim = Yol_Secici()
yol_secim.load_corridors()

cv2.namedWindow("ihlal_kontrol", cv2.WINDOW_NORMAL)
cv2.setMouseCallback("ihlal_kontrol", yol_secim.mouse_callback)

cv2.setWindowProperty("ihlal_kontrol", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

# cv2.resizeWindow("İhlal Kontrol", 1280, 720) # Manuel Pencere Boyutu

track_memory = {}
ihlaller = []
basarili_gecisler = []

paused = False

while True:
    if not paused:
        ret, frame = cap.read()
        if not ret:
            break

        # Maske boyutunu çerçeveye göre yeniden boyutlandır
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

            for idx, corridor in enumerate(yol_secim.corridors):

                if not hasattr(corridor, "id"):
                    corridor.id = idx + 1

            if len(yol_secim.corridors) > 0:
                if track_id in track_memory:
                    prev_cx, prev_cy = track_memory[track_id]

                    for corridor in yol_secim.corridors:
                        if Yol_Secici.is_crossing_line(
                            (cx, cy), (prev_cx, prev_cy), corridor.entry_line):
                            if track_id not in corridor.entered_ids:
                                corridor.entered_ids.add(track_id)
                                print(f" {track_id} girişini {corridor.id} yoluna yaptı")
                        if track_id in corridor.entered_ids and track_id not in corridor.exited_ids:
                            if Yol_Secici.is_crossing_line(

                                (cx, cy), (prev_cx, prev_cy), corridor.exit_line):
                                corridor.exited_ids.add(track_id)
                                print(f" {track_id} çıkışını {corridor.id} yoluna yaptı")
                                gecis_zamani = cap.get(cv2.CAP_PROP_POS_MSEC) / 1000.0
                                basarili_gecisler.append({
                                    "track_id": entered_id,     #buranın çalışıp çalışmadığını tekrar kontrol et
                                    "time_seconds": round(gecis_zamani, 2),
                                    "corridor_id": corridor.id,
                                    "ihlal_durum":False
                                })

                track_memory[track_id] = (cx, cy)

            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(frame, f'ID {track_id}', (x1, y1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 0, 0), 2)

            for corridor in yol_secim.corridors:
                for entered_id in list(corridor.entered_ids):
                    if entered_id not in alive_cars and entered_id not in corridor.exited_ids and not any(g['track_id'] == entered_id for g in basarili_gecisler):

                        if not any(i['track_id'] == entered_id for i in ihlaller):
                            ihlal_zamani = cap.get(cv2.CAP_PROP_POS_MSEC) / 1000.0
                            ihlaller.append({
                                "track_id": entered_id,
                                "time_seconds": round(ihlal_zamani,2),
                                "corridor_id": corridor.id,
                                "ihlal_durum":True
                            })
                            print(f"Ihlal: {entered_id} @ {ihlal_zamani:.2f} s (Corridor ID: {corridor.id})")

        yol_secim.draw_corridors(frame)

        y_offset = 30
        for idx, corridor in enumerate(yol_secim.corridors):
            cv2.putText(frame, f'Corridor {corridor.id} Entered: {len(corridor.entered_ids)} Exited: {len(corridor.exited_ids)}',
                        (10, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            y_offset += 30

    cv2.imshow("ihlal_kontrol", frame) # Pencere adını belirttik

    key = cv2.waitKey(1) & 0xFF
    if key == ord("q"):
        break
    elif key == ord("p"):
        paused = not paused
        print("Durduruldu" if paused else "Başlatıldı")
    elif cv2.waitKey(1) & 0xFF == ord("s"):
        yol_secim.save_corridors()

cap.release()
cv2.destroyAllWindows()

temiz_ihlaller = []
for ihlal in ihlaller:
    track_id = ihlal["track_id"]
    if not any(g['track_id'] == track_id for g in basarili_gecisler):
        temiz_ihlaller.append(ihlal)
ihlaller = temiz_ihlaller


with open("ihlaller.json", "w") as f:
    json.dump(ihlaller, f, indent=4)


for ihlal in ihlaller:
    ihlal_ekle_db(ihlal["track_id"],ihlal["time_seconds"],ihlal["corridor_id"],ihlal["ihlal_durum"])
for i in basarili_gecisler:
    ihlal_ekle_db(i["track_id"],i["time_seconds"],i["corridor_id"],i["ihlal_durum"])

print("Ihlaller Veritabanına kaydedildi", ihlaller)