from PyQt5.QtWidgets import QWidget, QTableWidgetItem, QLabel
from PyQt5 import uic, QtCore
from database.db_config import get_connection
from gelimis_gui import DBPG
from gui.video_player import DBVideo
from PyQt5.QtGui import QPixmap
from PIL import Image
import io

class DBPage(QWidget):
    def __init__(self):
        super().__init__()
        uic.loadUi("secondpage.ui", self)
        self.setStyleSheet("""
            QWidget {
                background-color: #384042;
;
            }

            QPushButton {
                background-color: #049DD9;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 15px;
                font-weight: bold;
            }

            QPushButton:hover {
                background-color: #243E73;
            }

            QLineEdit {
                background-color: white;
                color: #021F59;
                border: 2px solid #8BBBD9;
                border-radius: 5px;
                padding: 5px;
            }

            QTableWidget {
                background-color: #F2F2F2;
                gridline-color: #8BBBD9;
                color: #021F59;
                border: 1px solid #021F59;
                selection-background-color: #8BBBD9;
                selection-color: #021F59;
            }

            QHeaderView::section {
                background-color: #021F59;
                color: white;
                padding: 4px;
                border: none;
            }
        """)
        self.gelismis_page=DBPG()
        self.pushButton_2.clicked.connect(self.tum_gecisler)#tüm durumlar
        self.pushButton_3.clicked.connect(self.ihlal_gecisler)#ihlal
        self.pushButton_4.clicked.connect(self.basarili_gecisler)#basariligecis
        self.pushButton_7.clicked.connect(self.gelismis)
        self.pushButton_5.clicked.connect(self.exit_button)
        self.pushButton.clicked.connect(self.where_sorgu)
        self.pushButton_6.clicked.connect(self.izlet)

        self.lineEdit.returnPressed.connect(self.where_sorgu)

    def tum_gecisler(self):
        try:
            self.connection = get_connection()
            cursor = self.connection.cursor()
            cursor.execute("SELECT * FROM araclar")
            rows = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            self.tableWidget.setRowCount(len(rows))
            self.tableWidget.setColumnCount(len(columns))
            self.tableWidget.setHorizontalHeaderLabels(columns)
            for row_idx, row_data in enumerate(rows):
                for col_idx, col_data in enumerate(row_data):
                    item = QTableWidgetItem(str(col_data))
                    self.tableWidget.setItem(row_idx, col_idx, item)
            cursor.close()
        except Exception as e:
            print(f"Bağlantı hatası: {e}")

    def ihlal_gecisler(self):
        self.connection = get_connection()
        cursor = self.connection.cursor()
        cursor.execute("SELECT * FROM araclar where ihlal_durumu = 1")
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        self.tableWidget.setRowCount(len(rows))
        self.tableWidget.setColumnCount(len(columns))
        self.tableWidget.setHorizontalHeaderLabels(columns)
        for row_idx, row_data in enumerate(rows):
            for col_idx, col_data in enumerate(row_data):
                item = QTableWidgetItem(str(col_data))
                self.tableWidget.setItem(row_idx, col_idx, item)
        cursor.close()

    def basarili_gecisler(self):
        self.connection = get_connection()
        cursor = self.connection.cursor()
        cursor.execute("SELECT * FROM araclar where ihlal_durumu = 0")
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        self.tableWidget.setRowCount(len(rows))
        self.tableWidget.setColumnCount(len(columns))
        self.tableWidget.setHorizontalHeaderLabels(columns)
        for row_idx, row_data in enumerate(rows):
            for col_idx, col_data in enumerate(row_data):
                item = QTableWidgetItem(str(col_data))
                self.tableWidget.setItem(row_idx, col_idx, item)
        cursor.close()

    def where_sorgu(self):
        aracid = self.lineEdit.text()
        try:
            self.connection = get_connection()
            cursor = self.connection.cursor()
            cursor.execute("SELECT * FROM araclar WHERE arac_id = %s", (aracid))
            rows = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            self.tableWidget.setRowCount(len(rows))
            self.tableWidget.setColumnCount(len(columns))
            self.tableWidget.setHorizontalHeaderLabels(columns)
            for row_idx, row_data in enumerate(rows):
                for col_idx, col_data in enumerate(row_data):
                    item = QTableWidgetItem(str(col_data))
                    self.tableWidget.setItem(row_idx, col_idx, item)
            cursor.execute(f"SELECT goruntu FROM arac_goruntu WHERE arac_id = %s", (aracid))
            row = cursor.fetchone()
            label = self.findChild(QLabel, "arac_resim")
            label_width = label.width()
            label_height = label.height()
            if row and row[0]:
                image_data = row[0]
                image = Image.open(io.BytesIO(image_data))
                image = image.convert("RGB")
                data = io.BytesIO()
                image.save(data, format="PNG")
                pixmap = QPixmap()
                pixmap.loadFromData(data.getvalue())
                label.setScaledContents(True)
                scaled_pixmap = pixmap.scaled(label_width, label_height, QtCore.Qt.KeepAspectRatio,QtCore.Qt.SmoothTransformation)
                #self.findChild(QLabel, "arac_resim").setPixmap(pixmap)
                label.setPixmap(scaled_pixmap)

            else:
                print("Görüntü bulunamadı.")
            cursor.close()
        except Exception as e:
            print(f"Bağlantı hatası: {e}")

    def gelismis(self):
        self.gelismis_page.show()


    def izlet(self):
        aracid = self.lineEdit.text()
        self.video_oynatici=DBVideo(aracid)
        self.video_oynatici.show()

    def exit_button(self):
        self.close()