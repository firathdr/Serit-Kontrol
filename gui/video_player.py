from PyQt5.QtWidgets import QWidget, QLabel
from PyQt5 import uic, QtGui, QtCore
from database.db_config import get_connection
import cv2

class DBVideo(QWidget):
    def __init__(self, arac_id):
        super().__init__()
        self.arac_id = arac_id
        uic.loadUi("player.ui", self)
        self.paused = False
        self.label: QLabel = self.findChild(QLabel, "video_label")

        # Veritabanından zaman aralığı
        self.connection = get_connection()
        cursor = self.connection.cursor()
        cursor.execute("SELECT giris_zamani FROM arac_goruntu WHERE arac_id = %s", (self.arac_id,))
        giris = cursor.fetchone()
        cursor.execute("SELECT saat FROM araclar WHERE arac_id = %s", (self.arac_id,))
        saat = cursor.fetchone()
        cursor.close()

        self.pushButton.clicked.connect(self.durdur_baslat)
        self.pushButton_2.clicked.connect(self.tekrar_oynat)





        if not (giris and saat):
            print("Zaman bilgileri bulunamadı!")
            return

        self.start_sec = giris[0]
        self.end_sec = saat[0]

        self.video_path = "../videos/video1.mp4"
        self.cap = cv2.VideoCapture(self.video_path)
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

    def next_frame(self):
        current_frame = self.cap.get(cv2.CAP_PROP_POS_FRAMES)

        if current_frame >= self.end_frame:
            self.timer.stop()
            self.cap.release()
            print("Video oynatma bitti.")
            return

        ret, frame = self.cap.read()
        if not ret:
            self.timer.stop()
            self.cap.release()
            print("Video akışı durdu.")
            return
        self.show_frame(frame)

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
            self.timer.start()
    def tekrar_oynat(self):
        self.start_frame = int(self.start_sec * self.fps)
        self.end_frame = int(self.end_sec * self.fps)

        self.cap.set(cv2.CAP_PROP_POS_FRAMES, self.start_frame)

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.next_frame)
        self.timer.start(int(1000 / self.fps))

