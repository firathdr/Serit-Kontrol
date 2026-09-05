import sys
from pathlib import Path

if __package__ in (None, ""):
    # "python gui/gui_pyqt.py" ile dogrudan calistirildiginda proje kokunu
    # iceri alalim; boylece core/, database/ ve gui/ paketleri bulunur.
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import cv2
from PyQt5 import QtWidgets, uic, QtGui, QtCore
from PyQt5.QtWidgets import QLabel

from core.pipeline import Pipeline
from core.detector import ObjectDetector
from deep_sort_realtime.deepsort_tracker import DeepSort
from core.arac_yol import Yol_Secici
from gui.db_gui import DBPage

GUI_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = GUI_DIR.parent
MODELS_DIR = PROJECT_ROOT / "models"
MASKS_DIR = PROJECT_ROOT / "masks"
VIDEOS_DIR = PROJECT_ROOT / "videos"
CORRIDORS_DIR = PROJECT_ROOT / "corridors"


def klasor_dosyalari(klasor):
    """Klasordeki secilebilir dosyalar.

    Alt klasorler, gizli dosyalar ve .gitkeep gibi yer tutucular listeye girmez.
    """
    if not klasor.is_dir():
        return []
    return sorted(
        girdi.name
        for girdi in klasor.iterdir()
        if girdi.is_file() and not girdi.name.startswith(".")
    )

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        uic.loadUi(str(GUI_DIR / "untitled.ui"), self)
        self.setWindowTitle("Şerit Kontrol Sistemi")
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
        self.comboBox2 = self.findChild(QtWidgets.QComboBox, "comboBox_2")
        self.comboBox3 = self.findChild(QtWidgets.QComboBox, "comboBox_3")
        self.comboBox4 = self.findChild(QtWidgets.QComboBox, "comboBox_4")

        for kutu, klasor in (
            (self.comboBox, MODELS_DIR),
            (self.comboBox2, MASKS_DIR),
            (self.comboBox3, VIDEOS_DIR),
            (self.comboBox4, CORRIDORS_DIR),
        ):
            kutu.clear()
            kutu.addItems(klasor_dosyalari(klasor))

        self.pushButton_6.clicked.connect(self.start_pipeline)
        self.pushButton_4.clicked.connect(self.exit_button)
        self.pushButton.clicked.connect(self.paused_button)
        self.pushButton_7.clicked.connect(self.fullscreen_button)  #ŞİMDİLİK ÇALIŞMIYOR
        self.pushButton_8.clicked.connect(self.database_page)


        self.label = GoruntuLabel(main_window=self, parent=self.goruntu)
        self.yol_secici = Yol_Secici()

        self.pushButton_2.clicked.connect(self.save_koridor)
        self.pushButton_3.clicked.connect(self.cizim_sil_button)
        self.pushButton_5.clicked.connect(self.load_corridors_button)

        self.label.setGeometry(0, 0, self.goruntu.width(), self.goruntu.height())
        self.label.setScaledContents(True)

        self.paused = True
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)

    def start_pipeline(self):
        model_path = str(MODELS_DIR / self.comboBox.currentText())
        mask_path = str(MASKS_DIR / self.comboBox2.currentText())
        video_path = str(VIDEOS_DIR / self.comboBox3.currentText())

        detector = ObjectDetector(model_path)
        tracker = DeepSort(max_age=15, n_init=2)
        self.pipeline = Pipeline(model_path, mask_path, video_path, detector, tracker, self.yol_secici,ciz_status=True)
        self.paused = False

        self.pipeline.ihlal_detected_signal.connect(self.update_ihlal_display)

    def fullscreen_button(self):
        if not hasattr(self, "Tam ekran") or self.fullscreen is None or self.fullscreen.isHidden():
            self.fullscreen = FullscreenWindow(self)
            self.fullscreen.show()

    def update_frame(self):
        if not self.paused:
            ret, frame = self.pipeline.read_frame()
            if not ret:
                self.pipeline.release()
                self.close()
                return
            frame= self.pipeline.process_frame(frame)
            self.show_frame(frame)
    global frame

    def save_koridor(self):
        self.yol_secici.save_corridors(str(CORRIDORS_DIR / self.comboBox4.currentText()))

    def show_framee(self, frame):
        self.yol_secici.draw_corridors(frame)
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = frame.shape
        self.current_frame_shape = (w, h)  # Ekle!
        bytes_per_line = ch * w
        qimg = QtGui.QImage(frame.data, w, h, bytes_per_line, QtGui.QImage.Format_RGB888)
        pixmap = QtGui.QPixmap.fromImage(qimg)
        self.label.setPixmap(pixmap)

    def show_frame(self, frame):
        self.yol_secici.draw_corridors(frame)
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = frame.shape
        self.current_frame_shape = (w, h)
        bytes_per_line = ch * w
        qimg = QtGui.QImage(frame.data, w, h, bytes_per_line, QtGui.QImage.Format_RGB888)
        pixmap = QtGui.QPixmap.fromImage(qimg)

        self.label.setPixmap(pixmap)

        if hasattr(self, "fullscreen") and self.fullscreen is not None:
            if not self.fullscreen.isHidden():
                self.fullscreen.label.setPixmap(pixmap)

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
        corridor_path = str(CORRIDORS_DIR / self.comboBox4.currentText())
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
        try:
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
        except:
            pass

class FullscreenWindow(QtWidgets.QMainWindow):
    def __init__(self, main_window):
        super().__init__()
        self.setWindowTitle("Tam Ekran")
        self.main_window = main_window
        self.label = GoruntuLabel(main_window=main_window, parent=self)
        self.setCentralWidget(self.label)
        self.label.setAlignment(QtCore.Qt.AlignCenter)
        self.label.setScaledContents(True)
        self.showFullScreen()

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Escape:
            self.close()


def main():
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    return app.exec_()


if __name__ == "__main__":
    sys.exit(main())


