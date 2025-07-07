import cv2
import numpy as np
import json
from core.detector import ObjectDetector
from deep_sort_realtime.deepsort_tracker import DeepSort
from core.arac_yol import Yol_Secici

#import subprocess
# yt-dlp -g 'https://www.youtube.com/watch?v=ByED80IKdIU&ab_channel=CityofColdwaterMI'  #canlı video kullanımı için

stream_url = """https://manifest.googlevideo.com/api/manifest/hls_playlist/expire/1751913359/ei/L79raKO1HdrlxN8Pj6DmOQ/ip/178.233.41.211/id/ByED80IKdIU.3/itag/96/source/yt_live_broadcast/requiressl/yes/ratebypass/yes/live/1/sgoap/gir%3Dyes%3Bitag%3D140/sgovp/gir%3Dyes%3Bitag%3D137/rqh/1/hls_chunk_host/rr7---sn-8vq54voxu-5qce.googlevideo.com/xpc/EgVo2aDSNQ%3D%3D/playlist_duration/30/manifest_duration/30/bui/AY1jyLPn8YrjRJnhlyaomDJ-waqYE7_cCzHR_FLpBiQggdY8XwK93OQpoV263ZEYHujDoGnB4XaQrH6c/spc/l3OVKcrjkfpX8CZh1ztWY9jQ1eAV1TfJXy62CS_W6TxxQDTCdrgF7JjOc8f3J
e_Edg2n51bBt7k/vprv/1/playlist_type/DVR/initcwndbps/1967500/met/1751891761,/mh/jK/mm/44/mn/sn-8vq54voxu-5qce/ms/lva/mv/m/mvi/7/pl/24/rms/lva,lva/dover/11/pacing/0/keepalive/yes/fex
p/51355912/mt/1751891572/sparams/expire,ei,ip,id,itag,source,requiressl,ratebypass,live,sgoap,sgovp,rqh,xpc,playlist_duration,manifest_duration,bui,spc,vprv,playlist_type/sig/AJfQd
SswRQIgKvAMZu2YvF6i1BGPfTzf0hjhPPMrV6qfGXJ7ab_IfVUCIQDA7IhIjWj1XFZyYeCvq54ousIVQbwpc_lPNZXz0vjNxA%3D%3D/lsparams/hls_chunk_host,initcwndbps,met,mh,mm,mn,ms,mv,mvi,pl,rms/lsig/APaTxxMwRQIhANfrvJbXPahYZkRwJqI-m2tJQnFlS8YeTn4Y4VhJo3UuAiArlDt0owuBbXOtQLjzDdWqUIcvyfKBx9ppw-MeNRnx4w%3D%3D/playlist/index.m3u8"""  # yt-dlp çıktısı

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
cv2.namedWindow("ihlal_kontrol", cv2.WINDOW_NORMAL)
cv2.setMouseCallback("ihlal_kontrol", yol_secim.mouse_callback)

cv2.setWindowProperty("ihlal_kontrol", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

# cv2.resizeWindow("İhlal Kontrol", 1280, 720) # Manuel Pencere Boyutu

track_memory = {}
ihlaller = []

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
                                print(f" {track_id} girişini {corridor.entry_line} yoluna yaptı")
                        if track_id in corridor.entered_ids and track_id not in corridor.exited_ids:
                            if Yol_Secici.is_crossing_line(
                                (cx, cy), (prev_cx, prev_cy), corridor.exit_line):
                                corridor.exited_ids.add(track_id)
                                print(f" {track_id} çıkışını {corridor.exit_line} yoluna yaptı")
                            # deneysel kod, doğruluğu düşük.
                            #    for other_corridor in yol_secim.corridors: #aynı giriş farklı çıkış kontrol
                            #        if other_corridor is not corridor:
                            #            if track_id in other_corridor.entered_ids and track_id not in other_corridor.exited_ids:
                            #                other_corridor.exited_ids.add(track_id)
                            #                print(
                            #                    f" {track_id} diğer Corridor {other_corridor.id} için de çıkış işaretlendi")

                track_memory[track_id] = (cx, cy)

            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(frame, f'ID {track_id}', (x1, y1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 0, 0), 2)

        for corridor in yol_secim.corridors:
            for entered_id in list(corridor.entered_ids):
                if entered_id not in alive_cars and entered_id not in corridor.exited_ids:
                    if not any(i['track_id'] == entered_id for i in ihlaller):
                        ihlal_zamani = cap.get(cv2.CAP_PROP_POS_MSEC) / 1000.0
                        ihlaller.append({
                            "track_id": entered_id,
                            "time_seconds": round(ihlal_zamani,2),
                            "corridor_id": corridor.id
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

cap.release()
cv2.destroyAllWindows()

with open("ihlaller.json", "w") as f:
    json.dump(ihlaller, f, indent=4)

print("Ihlaller JSON dosyasına kaydedildi:", ihlaller)