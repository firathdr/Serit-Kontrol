from PyQt5.QtWidgets import QWidget, QLabel
from PyQt5 import uic, QtGui, QtCore
from database.db_config import get_connection
import cv2
import numpy as np

class DBVideo(QWidget):
    def __init__(self, arac_id, video_name):
        super().__init__()
        self.arac_id = arac_id
        self.path_video = video_name
        uic.loadUi("player.ui", self)
        self.paused = False
        self.label: QLabel = self.findChild(QLabel, "video_label")

        self.connection = get_connection()
        self.cursor = self.connection.cursor()

        self.template_image = None
        self.cursor.execute("SELECT goruntu FROM arac_goruntu WHERE arac_id = %s AND video_name = %s",
                            (self.arac_id, self.path_video))
        blob_data = self.cursor.fetchone()

        if blob_data and blob_data[0]:
            nparr = np.frombuffer(blob_data[0], np.uint8)
            self.template_image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            if self.template_image is None:
                pass
        else:
            self.label.setText("Veritabanında bu araç için görsel bulunamadı.")

        self.cursor.close()
        self.connection.close()

        self.pushButton.clicked.connect(self.durdur_baslat)
        self.pushButton_2.clicked.connect(self.tekrar_oynat)

        self.connection = get_connection()  # Yeniden bağlantı açıyoruz
        cursor = self.connection.cursor()
        cursor.execute("SELECT giris_zamani FROM arac_goruntu WHERE arac_id = %s and video_name=%s",
                       (self.arac_id, self.path_video,))
        giris = cursor.fetchone()
        cursor.execute("SELECT saat FROM araclar WHERE arac_id = %s and video_name=%s ",
                       (self.arac_id, self.path_video,))
        saat = cursor.fetchone()
        cursor.close()
        self.connection.close()

        if not (giris and saat):
            print("Zaman bilgileri bulunamadı, video oynatılmayacak.")
            self.cap = None
            return

        self.start_sec = giris[0]
        self.end_sec = saat[0]
        self.cap = cv2.VideoCapture("../videos/" + self.path_video + ".mp4")
        if not self.cap.isOpened():
            print(f"Hata: Video dosyası açılamadı: ../videos/{self.path_video}.mp4")
            self.cap = None
            return

        self.fps = self.cap.get(cv2.CAP_PROP_FPS)
        if not self.fps or self.fps <= 0:
            print("FPS okunamadı, varsayılan FPS = 25 kullanılıyor!")
            self.fps = 25  # Fallback

        self.start_frame = int(self.start_sec * self.fps)
        self.end_frame = int(self.end_sec * self.fps)

        self.cap.set(cv2.CAP_PROP_POS_FRAMES, self.start_frame)

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.next_frame)
        self.timer.start(int(1000 / self.fps))

        self.match_threshold = 0.6938

    def next_frame(self):
        if self.cap is None:
            return

        current_frame_pos = self.cap.get(cv2.CAP_PROP_POS_FRAMES)

        if current_frame_pos >= self.end_frame:
            self.timer.stop()
            self.cap.release()
            return

        ret, frame = self.cap.read()
        if not ret:
            self.timer.stop()
            self.cap.release()
            return


        processed_frame = self.process_and_find_template(frame)#şablonu aradıgımız kısım
        self.show_frame(processed_frame)

    def process_and_find_template(self, frame):

        if self.template_image is None:
            return frame

        h_template, w_template, _ = self.template_image.shape

        if w_template > frame.shape[1] or h_template > frame.shape[0]:
            return frame

        gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray_template = cv2.cvtColor(self.template_image, cv2.COLOR_BGR2GRAY)

        res = cv2.matchTemplate(gray_frame, gray_template, cv2.TM_CCOEFF_NORMED)

        loc = np.where(res >= self.match_threshold)

        for pt in zip(*loc[::-1]):
            cv2.rectangle(frame, pt, (pt[0] + w_template, pt[1] + h_template), (0, 255, 0), 2)

        return frame

    def show_frame(self, frame):
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = frame.shape
        bytes_per_line = ch * w
        qimg = QtGui.QImage(frame.data, w, h, bytes_per_line, QtGui.QImage.Format_RGB888)
        pixmap = QtGui.QPixmap.fromImage(qimg)

        scaled_pixmap = pixmap.scaled(
            self.label.width(),
            self.label.height(),
            QtCore.Qt.KeepAspectRatio,
            QtCore.Qt.SmoothTransformation
        )
        self.label.setPixmap(scaled_pixmap)

    def durdur_baslat(self):
        self.paused = not self.paused
        if self.paused:
            self.timer.stop()
        else:
            self.timer.start(int(1000 / self.fps))

    def tekrar_oynat(self):
        if self.cap is None:
            print("Video oynatmak için hazır değil.")
            return

        self.cap.set(cv2.CAP_PROP_POS_FRAMES, self.start_frame)
        self.paused = False
        if not self.timer.isActive():
            self.timer.start(int(1000 / self.fps))