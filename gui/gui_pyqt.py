import sys
import cv2
from PyQt5 import QtWidgets, uic, QtGui, QtCore
import os

from PyQt5.QtGui import QOpenGLWindow
from PyQt5.QtWidgets import QLabel
from filterpy.kalman import update
from torch import parse_ir

from core.pipeline import Pipeline
from core.detector import ObjectDetector
from deep_sort_realtime.deepsort_tracker import DeepSort
from core.arac_yol import Yol_Secici
from db_gui import DBPage

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        uic.loadUi("untitled.ui", self)
        self.setStyleSheet("""
    QMainWindow {
        background-color: #384042;
    }
    QFrame#goruntu {
        background-color: #ffffff;
        border: 2px solid #021F59;
    }
    QPushButton {
        background-color: #049DD9;
        color: white;
        border: none;
        border-radius: 5px;
        padding: 5px 10px;
    }
    QPushButton:hover {
        background-color: #243E73;
        

    }
    QLabel {
        color: #021F59;
    }
    QComboBox {
        background-color: #F2F2F2;
        color: #243E73;
        border: 1px solid #243E73;
        padding: 2px 5px;
    }
    QMenuBar {
        background-color: #021F59;
    }
    QMenuBar::item {
        color: white;
    }
""")
        self.text_Area = self.findChild(QLabel, 'textlabel')
        if self.text_Area:
            self.text_Area.setText("İhlal Durumu: Bekleniyor...")
            self.text_Area.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignTop)
            self.text_Area.setWordWrap(True)
            self.text_Area.setStyleSheet("color: red; font-weight: bold; font-size: 14px;")
        self.comboBox = self.findChild(QtWidgets.QComboBox, "comboBox")
        path_model = "../models"
        if os.path.exists(path_model):
            files1 = os.listdir(path_model)
            files1 = [f for f in files1 if os.path.isfile(os.path.join(path_model, f))]
            files1.remove(files1[0])
            self.comboBox.clear()
            self.comboBox.addItems(files1)

        self.comboBox2 = self.findChild(QtWidgets.QComboBox, "comboBox_2")
        path_mask = "../masks"
        if os.path.exists(path_mask):
            files2 = os.listdir(path_mask)
            files2 = [f for f in files2 if os.path.isfile(os.path.join(path_mask, f))]
            self.comboBox2.clear()
            self.comboBox2.addItems(files2)

        self.comboBox3 = self.findChild(QtWidgets.QComboBox, "comboBox_3")
        path_video = "../videos"
        if os.path.exists(path_video):
            files3 = os.listdir(path_video)
            files3 = [f for f in files3 if os.path.isfile(os.path.join(path_video, f))]
            files3.remove(files3[0])
            self.comboBox3.clear()
            self.comboBox3.addItems(files3)

        self.comboBox4 = self.findChild(QtWidgets.QComboBox, "comboBox_4")
        path_corridor = "../corridors"
        if os.path.exists(path_corridor):
            files4 = os.listdir(path_corridor)
            files4 = [f for f in files4 if os.path.isfile(os.path.join(path_corridor, f))]
            files4.remove(files4[0])
            self.comboBox4.clear()
            self.comboBox4.addItems(files4)


        self.pushButton_6.clicked.connect(self.start_pipeline)
        self.pushButton_4.clicked.connect(self.exit_button)
        self.pushButton.clicked.connect(self.paused_button)
        self.pushButton_7.clicked.connect(self.fullscreen_button)  #ŞİMDİLİK ÇALIŞMIYOR
        self.pushButton_8.clicked.connect(self.database_page)


        self.label = GoruntuLabel(main_window=self, parent=self.goruntu)
        self.yol_secici = Yol_Secici()
        corridor_file= self.comboBox4.currentText()

        self.pushButton_2.clicked.connect(
            lambda: self.yol_secici.save_corridors( os.path.join("../corridors", corridor_file))
        )
        self.pushButton_3.clicked.connect(self.cizim_sil_button)

        self.pushButton_5.clicked.connect(self.load_corridors_button)
        label=QLabel("textlabel")
        label.show()

        self.label.setGeometry(0, 0, self.goruntu.width(), self.goruntu.height())
        self.label.setScaledContents(True)

        self.paused = True
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)

    def start_pipeline(self):
        model_file = self.comboBox.currentText()
        mask_file = self.comboBox2.currentText()
        video_file = self.comboBox3.currentText()
        corridor_file= self.comboBox4.currentText()
        model_path = os.path.join("../models", model_file)
        mask_path = os.path.join("../masks", mask_file)
        video_path = os.path.join("../videos", video_file)
        corridor_path = os.path.join("../corridors", corridor_file)

        detector = ObjectDetector(model_path, device="cuda")
        tracker = DeepSort(max_age=15, n_init=2)
        self.pipeline = Pipeline(model_path, mask_path, video_path, detector, tracker, self.yol_secici,ciz_status=True)
        self.paused = False

        self.pipeline.ihlal_detected_signal.connect(self.update_ihlal_display)


    def fullscreen_button(self):
        pixmap=self.label.pixmap()       #henüz çalışmıyor
        if pixmap:
            self.fullscreen=FullscreenWindow(pixmap)
            self.fullscreen.label.setPixmap(pixmap)

    def update_frame(self):
        if not self.paused:
            ret, frame = self.pipeline.read_frame()
            if not ret:
                #self.pipeline.save_ihlaller()
                self.pipeline.release()
                self.close()
                return
            frame= self.pipeline.process_frame(frame)
            self.show_frame(frame)
    global frame

    def show_frame(self, frame):
        self.yol_secici.draw_corridors(frame)
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = frame.shape
        self.current_frame_shape = (w, h)  # Ekle!
        bytes_per_line = ch * w
        qimg = QtGui.QImage(frame.data, w, h, bytes_per_line, QtGui.QImage.Format_RGB888)
        pixmap = QtGui.QPixmap.fromImage(qimg)
        self.label.setPixmap(pixmap)

    def gecis_log(self):
        label=QtWidgets.QLabel(self.goruntu)
        yazi=QtWidgets.QLabel(label)
        for idx, corridor in enumerate(self.yol_secim.corridors):
            yazi.setText(str(idx,corridor))
    def paused_button(self):
        self.paused = not self.paused
        if self.paused == True:
            self.timer.stop()
        else:
            self.timer.start()
    def ihlal_yaz(self,text):
        self.text_Area.setText(text)

    def exit_button(self):
        try:
            if self.pipeline.track_memory is not None:
                self.pipeline.release()
        except Exception as e:
            pass
        self.close()

    def gecici_buton(self):
        for i in enumerate(self.pipeline.basarili_gecisler):
            print(i)
        for i in enumerate(self.pipeline.ihlaller):
            print(i)


    def load_corridors_button(self):
        corridor_file = self.comboBox4.currentText()
        corridor_path = os.path.join("../corridors", corridor_file)
        self.pipeline.yol_secim.load_corridors(corridor_path)
    def cizim_sil_button(self):
        self.pipeline.cizim_sil()
    def update_ihlal_display(self, ihlal_messages):
        current_text = self.text_Area.text()
        if current_text == "İhlal Durumu: Bekleniyor..." or current_text == "Pipeline başlatıldı. İzleniyor...":
            current_text = ""
        for msg in ihlal_messages:
            current_text += f"\n{msg}"
        self.text_Area.setText(current_text.strip())
    def database_page(self):
        self.second_page = DBPage(self.comboBox3.currentText())
        self.second_page.show()

class GoruntuLabel(QtWidgets.QLabel):
    def __init__(self,  main_window,parent):
        super().__init__(parent)
        self.main_window = main_window

    def mousePressEvent(self, event):
        x = event.x()
        y = event.y()
        gui_w = self.width()
        gui_h = self.height()
        frame_w, frame_h = self.main_window.current_frame_shape
        gercekx = int(x * frame_w / gui_w)
        gerceky = int(y * frame_h / gui_h)
        self.main_window.yol_secici.mouse_callback(
            cv2.EVENT_LBUTTONDOWN, gercekx, gerceky, True, False
        )




class FullscreenWindow(QtWidgets.QMainWindow):
    def __init__(self, pixmap):
        super().__init__()
        self.setWindowTitle("Tam Ekran")
        self.label = GoruntuLabel(main_window=self,parent=self)
        self.setCentralWidget(self.label)
        self.label.setAlignment(QtCore.Qt.AlignCenter)
        self.label.setScaledContents(True)
        self.label.setPixmap(pixmap)
        self.showFullScreen()


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


