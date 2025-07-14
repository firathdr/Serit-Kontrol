import cv2
import json

class Pipeline:
    def __init__(self, model_path, mask_path, video_path, detector, tracker, yol_secici):
        self.detector = detector
        self.tracker = tracker
        self.yol_secim = yol_secici

        self.cap = cv2.VideoCapture(video_path)
        self.track_memory = {}
        self.ihlaller = []
        self.basarili_gecisler = []

        self.roi_mask = cv2.imread(mask_path, cv2.IMREAD_GRAYSCALE)
        if self.roi_mask.max() > 1:
            _, self.roi_mask = cv2.threshold(self.roi_mask, 127, 255, cv2.THRESH_BINARY)

    def read_frame(self):
        return self.cap.read()

    def process_frame(self, frame):
        if (self.roi_mask.shape[0] != frame.shape[0]) or (self.roi_mask.shape[1] != frame.shape[1]):
            self.roi_mask = cv2.resize(self.roi_mask, (frame.shape[1], frame.shape[0]), interpolation=cv2.INTER_NEAREST)
        masked_frame = cv2.bitwise_and(frame, frame, mask=self.roi_mask)

        results = self.detector.detect(masked_frame, conf=0.3, imgsz=640, iou=0.42)

        detections = []
        for result in results:
            for box in result.boxes:
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                conf = box.conf[0].cpu().numpy()
                cls = int(box.cls[0].cpu().numpy())
                detections.append(([x1, y1, x2 - x1, y2 - y1], conf, cls))

        tracks = self.tracker.update_tracks(detections, frame=frame)
        alive_cars = []

        for track in tracks:
            if not track.is_confirmed():
                continue

            track_id = track.track_id
            alive_cars.append(track_id)
            ltrb = track.to_ltrb()
            x1, y1, x2, y2 = map(int, ltrb)
            cx, cy = (x1 + x2) // 2, (y1 + y2) // 2

            for idx, corridor in enumerate(self.yol_secim.corridors):
                if not hasattr(corridor, "id"):
                    corridor.id = idx + 1

            if len(self.yol_secim.corridors) > 0:
                if track_id in self.track_memory:
                    prev_cx, prev_cy = self.track_memory[track_id]

                    for corridor in self.yol_secim.corridors:
                        if self.yol_secim.is_crossing_line((cx, cy), (prev_cx, prev_cy), corridor.entry_line):
                            if track_id not in corridor.entered_ids:
                                corridor.entered_ids.add(track_id)
                                print(f"{track_id} girişini {corridor.id} yoluna yaptı")
                        if track_id in corridor.entered_ids and track_id not in corridor.exited_ids:
                            if self.yol_secim.is_crossing_line((cx, cy), (prev_cx, prev_cy), corridor.exit_line):
                                corridor.exited_ids.add(track_id)
                                print(f"{track_id} çıkışını {corridor.id} yoluna yaptı")
                                gecis_zamani = self.cap.get(cv2.CAP_PROP_POS_MSEC) / 1000.0
                                self.basarili_gecisler.append({
                                    "track_id": track_id,
                                    "time_seconds": round(gecis_zamani, 2),
                                    "corridor_id": corridor.id,
                                    "ihlal_durum": False
                                })

                self.track_memory[track_id] = (cx, cy)

            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(frame, f'ID {track_id}', (x1, y1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 0, 0), 2)

            for corridor in self.yol_secim.corridors:
                for entered_id in list(corridor.entered_ids):
                    if entered_id not in alive_cars and entered_id not in corridor.exited_ids and not any(
                            g['track_id'] == entered_id for g in self.basarili_gecisler):
                        if not any(i['track_id'] == entered_id for i in self.ihlaller):
                            ihlal_zamani = self.cap.get(cv2.CAP_PROP_POS_MSEC) / 1000.0
                            self.ihlaller.append({
                                "track_id": entered_id,
                                "time_seconds": round(ihlal_zamani, 2),
                                "corridor_id": corridor.id,
                                "ihlal_durum": True
                            })
                            print(f"Ihlal: {entered_id} @ {ihlal_zamani:.2f} s (Corridor ID: {corridor.id})")

        self.yol_secim.draw_corridors(frame)

                #cv2.putText(frame,
                 #           f'Corridor {corridor.id} Entered: {len(corridor.entered_ids)} Exited: {len(corridor.exited_ids)}',
                 #           (10, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                #y_offset += 30


        return frame

    def release(self):
        self.cap.release()

    def save_ihlaller(self):
        temiz_ihlaller = []
        for ihlal in self.ihlaller:
            if not any(g['track_id'] == ihlal["track_id"] for g in self.basarili_gecisler):
                temiz_ihlaller.append(ihlal)
        self.ihlaller = temiz_ihlaller

        with open("ihlaller.json", "w") as f:
            json.dump(self.ihlaller, f, indent=4)
