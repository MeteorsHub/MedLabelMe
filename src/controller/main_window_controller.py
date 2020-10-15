from PyQt5.QtCore import pyqtSlot, QUrl
from PyQt5.QtWidgets import QMainWindow, QFileDialog
from view.main_window_ui import Ui_MainWindow
from model.model import Model


class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self.parent = parent
        self.setupUi(self)
        self.model = Model()

    @pyqtSlot()
    def menu_open_triggered(self):
        filename, _ = QFileDialog.getOpenFileUrl(self, 'select file to open', QUrl(self.model.last_wd), '*.nii.gz')
        self.model.read_img(filename,)
