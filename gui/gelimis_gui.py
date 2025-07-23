from PyQt5.QtWidgets import QWidget, QTableWidgetItem,QLineEdit
from PyQt5 import uic


class DBPG(QWidget):
    def __init__(self):
        super(QWidget,self).__init__()
        uic.loadUi("gelismis_duzenleme.ui",self)


