import cv2
from PyQt5.QtCore import QObject, pyqtSignal  # QObject ve pyqtSignal import edin
from database.ihlal_ekle import ihlal_ekle_db
from database.db_config import get_connection
class Pipeline(QObject):
    ihlal_detected_signal = pyqtSignal(list)
    def __init__(self, model_path, mask_path, video_path, detector, tracker, yol_secici, ciz_status):
        super().__init__()
        self.detector = detector
        self.tracker = tracker
        self.yol_secim = yol_secici
        self.video_path = video_path
        self.cap = cv2.VideoCapture(video_path)
        self.alive_cars = []
        self.track_memory = {}
        self.ihlaller = []
        self.basarili_gecisler = []
        self.ciz_status = ciz_status
        self.roi_mask = cv2.imread(mask_path, cv2.IMREAD_GRAYSCALE)
        if self.roi_mask is None:  # Maske dosyasının yüklendiğini kontrol edin
            pass
        else:
            if self.roi_mask.max() > 1:
                _, self.roi_mask = cv2.threshold(self.roi_mask, 127, 255, cv2.THRESH_BINARY)

    def pipeline_load(self, yol_secici):
        yol_secici.load_corridors("../corridors/corridors.json") #kullanılmıyor artık sil bu satırı

    def cizim_sil(self):
        self.ciz_status = False
        self.yol_secim.corridors = []

    def read_frame(self):
        return self.cap.read()

    def process_frame(self, frame):
        if self.roi_mask is None:
            return frame

        if (self.roi_mask.shape[0] != frame.shape[0]) or (self.roi_mask.shape[1] != frame.shape[1]):
            self.roi_mask = cv2.resize(self.roi_mask, (frame.shape[1], frame.shape[0]), interpolation=cv2.INTER_NEAREST)
        masked_frame = cv2.bitwise_and(frame, frame, mask=self.roi_mask)

        results = self.detector.detect(masked_frame, conf=0.3, imgsz=640, iou=0.42)

        detections = []
        for result in results:
            for box in result.boxes:
                if box.xyxy is not None and len(box.xyxy) > 0:
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                    conf = box.conf[0].cpu().numpy()
                    cls = int(box.cls[0].cpu().numpy())
                    detections.append(([x1, y1, x2 - x1, y2 - y1], conf, cls))

        if not detections:
            tracks = self.tracker.update_tracks([], frame=frame)
        else:
            tracks = self.tracker.update_tracks(detections, frame=frame)

        ihlal_text = []
        self.alive_cars = []
        for track in tracks:
            if not track.is_confirmed():
                continue
            self.alive_cars.append(track.track_id)
        for track in tracks:
            if not track.is_confirmed():
                continue

            track_id = track.track_id
            ltrb = track.to_ltrb()
            x1, y1, x2, y2 = map(int, ltrb)
            cx, cy = (x1 + x2) // 2, (y1 + y2) // 2

            for idx, corridor in enumerate(self.yol_secim.corridors):
                if not hasattr(corridor, "id"):
                    corridor.id = idx + 1  # Eğer corridor objesi id'ye sahip değilse atarız

            if len(self.yol_secim.corridors) > 0:
                if track_id in self.track_memory:
                    prev_cx, prev_cy = self.track_memory[track_id]

                    for corridor in self.yol_secim.corridors:
                        if self.yol_secim.is_crossing_line((cx, cy), (prev_cx, prev_cy), corridor.entry_line):
                            if track_id not in corridor.entered_ids:
                                corridor.entered_ids.add(track_id)
                                giris_zamani = self.cap.get(cv2.CAP_PROP_POS_MSEC) / 1000.0
                                # print(f"{track_id} girişini {corridor.id} yoluna yaptı")
                                #roi = frame[round(y1/2):round(y2*2), round(x1/2):round(x2*2)]
                                roi = frame[y1:y2, x1:x2]
                                retval, buffer = cv2.imencode('.jpg', roi)
                                image_bytes = buffer.tobytes()
                                try:
                                    conn = get_connection()
                                    cursor = conn.cursor()
                                    sql = "INSERT INTO arac_goruntu (arac_id, goruntu,giris_zamani,video_name) VALUES (%s, %s,%s,%s)"
                                    cursor.execute(sql, (track_id, image_bytes,giris_zamani,self.video_path.replace("\\", "/").split("/")[-1].split(".")[0]))
                                    conn.commit()
                                    cursor.close()
                                    conn.close()
                                    #print(f"TrackID {track_id} için görüntü veritabanına kaydedildi.")
                                except Exception as e:
                                    print(f"Görüntü DB kaydetme hatası: {e}")


                        if track_id in corridor.entered_ids and track_id not in corridor.exited_ids:
                            if self.yol_secim.is_crossing_line((cx, cy), (prev_cx, prev_cy), corridor.exit_line):
                                corridor.exited_ids.add(track_id)
                                # print(f"{track_id} çıkışını {corridor.id} yoluna yaptı")
                                gecis_zamani = self.cap.get(cv2.CAP_PROP_POS_MSEC) / 1000.0
                                basarili_gecis = {
                                    "track_id": track_id,
                                    "time_seconds": round(gecis_zamani, 2),
                                    "corridor_id": corridor.id,
                                    "ihlal_durum": False,
                                    "video_name":self.video_path.replace("\\", "/").split("/")[-1].split(".")[0]
                                }
                                self.basarili_gecisler.append(basarili_gecis)
                                try:
                                    ihlal_ekle_db(basarili_gecis['track_id'], basarili_gecis['time_seconds'],
                                                  basarili_gecis['corridor_id'], basarili_gecis['ihlal_durum'],basarili_gecis['video_name'])
                                except Exception as e:
                                    print(f"Bağlantı hatası: {e}")

                self.track_memory[track_id] = (cx, cy)

            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(frame, f'ID {track_id}', (x1, y1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 0, 0), 2)

            for corridor in self.yol_secim.corridors:
                current_alive_track_ids = set(self.alive_cars)

                for entered_id in list(corridor.entered_ids):
                    if entered_id not in current_alive_track_ids and \
                            entered_id not in corridor.exited_ids and \
                            not any(g['track_id'] == entered_id for g in self.basarili_gecisler):
                        if not any(i['track_id'] == entered_id for i in self.ihlaller):
                            ihlal_zamani = self.cap.get(cv2.CAP_PROP_POS_MSEC) / 1000.0
                            ihlal_data = {
                                "track_id": entered_id,
                                "time_seconds": round(ihlal_zamani, 2),
                                "corridor_id": corridor.id,
                                "ihlal_durum": True,
                                "video_name": self.video_path.replace("\\", "/").split("/")[-1].split(".")[0]

                            }
                            self.ihlaller.append(ihlal_data)

                            ihlal_text.append(f"İhlal: ID {entered_id} @ {ihlal_zamani:.2f}s (Koridor: {corridor.id})")
                            ihlal_ekle_db(ihlal_data['track_id'], ihlal_data['time_seconds'], ihlal_data['corridor_id'], ihlal_data['ihlal_durum'],ihlal_data['video_name'])
                            # print(f"İhlal: {entered_id} @ {ihlal_zamani:.2f}s (Corridor ID: {corridor.id})")

        if ihlal_text:
            self.ihlal_detected_signal.emit(ihlal_text)

        if self.ciz_status:
            self.yol_secim.draw_corridors(frame)
        return frame

    def release(self):
        self.cap.release()

    def save_ihlaller(self):
        temiz_ihlaller = []
        for ihlal in self.ihlaller:
            if not any(g['track_id'] == ihlal["track_id"] for g in self.basarili_gecisler):
                temiz_ihlaller.append(ihlal)
        self.ihlaller = temiz_ihlaller


