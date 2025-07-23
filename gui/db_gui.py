from PyQt5.QtWidgets import QWidget, QTableWidgetItem,QLineEdit
from PyQt5 import uic
from database.db_config import get_connection
from gelimis_gui import DBPG
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
    def gelismis(self):
        self.gelismis_page.show()



    def exit_button(self):
        self.close()