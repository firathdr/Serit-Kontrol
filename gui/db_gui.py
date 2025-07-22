from PyQt5.QtWidgets import QWidget, QTableWidgetItem,QLineEdit
from PyQt5 import uic
from database.db_config import get_connection

class DBPage(QWidget):
    def __init__(self):
        super().__init__()
        uic.loadUi("secondpage.ui", self)

        self.pushButton_2.clicked.connect(self.tum_gecisler)#tüm durumlar
        self.pushButton_3.clicked.connect(self.ihlal_gecisler)#ihlal
        self.pushButton_4.clicked.connect(self.basarili_gecisler)#basariligecis
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
            cursor.close()
        except Exception as e:
            print(f"Bağlantı hatası: {e}")