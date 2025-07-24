from PyQt5.QtWidgets import QWidget, QTableWidgetItem, QLineEdit, QLabel
from PyQt5 import uic
from sympy.polys.polyconfig import query

from database.db_config import get_connection

class DBPG(QWidget):
    def __init__(self):
        super(QWidget, self).__init__()
        uic.loadUi("gelismis_duzenleme.ui", self)

        self.pushButton_2.clicked.connect(self.kaydi_sil)
        self.pushButton_3.clicked.connect(self.kayit_degisiklik)
        self.pushButton_4.clicked.connect(self.veritabani_sil)
        self.lineEdit.returnPressed.connect(self.where_sorgu)
        self.text_Area = self.findChild(QLabel, 'label')

        self.tableWidget.itemChanged.connect(self.item_changed)

    def where_sorgu(self):
        aracid = self.lineEdit.text()
        try:
            self.connection = get_connection()
            cursor = self.connection.cursor()
            cursor.execute("SELECT * FROM araclar WHERE arac_id = %s", (aracid,))
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

    def kaydi_sil(self):
        aracid = self.lineEdit.text()
        print(aracid)
        try:
            self.connection = get_connection()
            cursor = self.connection.cursor()
            cursor.execute("DELETE FROM araclar WHERE arac_id = %s;", (aracid,))
            self.connection.commit()
            cursor.close()
            self.text_Area.setText(f"{aracid} kodlu araç kaydı başarıyla silindi.")
        except Exception as e:
            print(f"Bağlantı hatası: {e}")

    def kayit_degisiklik(self):
        try:
            self.connection = get_connection()
            cursor = self.connection.cursor()
            for row in range(self.tableWidget.rowCount()):
                arac_id = self.lineEdit.text()
                saat = self.tableWidget.item(row, 0).text()
                serit_id = self.tableWidget.item(row, 1).text()
                ihlal_durumu = self.tableWidget.item(row, 2).text()

                cursor.execute("""
                    UPDATE araclar
                    SET saat = %s, serit_id = %s, ihlal_durumu = %s
                    WHERE arac_id = %s 
                """, (saat, serit_id, ihlal_durumu, arac_id))
            self.connection.commit()
            cursor.close()
            self.text_Area.setText(f"{arac_id} kodlu araç kaydı başarıyla güncellendi.")
        except Exception as e:
            print(f"Bağlantı hatası: {e}")

    def item_changed(self, item):
        try:
            self.connection = get_connection()
            cursor = self.connection.cursor()

            row = item.row()
            column = item.column()
            new_value = item.text()
            arac_id = self.lineEdit.text()
            column_name = self.tableWidget.horizontalHeaderItem(column).text()

            query = f"UPDATE araclar SET {column_name} = %s WHERE arac_id = %s"
            cursor.execute(query, (new_value, arac_id))

            self.connection.commit()
            cursor.close()
            print(f"{column_name} güncellendi: {new_value}")

        except Exception as e:
            print(f"Bağlantı hatası: {e}")
    def veritabani_sil(self):
        try:
            self.connection = get_connection()
            cursor = self.connection.cursor()

            query=["TRUNCATE TABLE araclar","TRUNCATE TABLE arac_goruntu"]
            for q in query:
                cursor.execute(q)
            self.connection.commit()
            cursor.close()
        except Exception as e:
            print(e)
