from PyQt5.QtCore import pyqtSlot
from PyQt5.QtGui import QPixmap, QImage, QTransform
from PyQt5.QtWidgets import QMainWindow, QFileDialog, QMessageBox, QPushButton

from model.model import Model
from view.main_window_ui import Ui_MainWindow


class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self.parent = parent
        self.setupUi(self)
        self.model = Model()

        self._cursor = [0, 0, 0]  # w, h, d or x, y, z
        self.window_lower = 0
        self.window_upper = 400

    def update_scenes(self, scenes='asc'):
        if 'a' in scenes:
            self.aGraphicsView.raw_img_item.setPixmap(QPixmap.fromImage(QImage(
                self.model.get_2D_map('a', self.cursor[2], 'raw', self.window_lower, self.window_upper),
                self.model.get_size()[1],
                self.model.get_size()[0],
                self.model.get_size()[1] * 1,  # bytesperline = width*channel
                QImage.Format_Grayscale8)))  # x, y
            self.aGraphicsView.raw_img_item.setTransform(QTransform(0, 1, 0, 1, 0, 0, 0, 0, 1))

        if 's' in scenes:
            self.sGraphicsView.raw_img_item.setPixmap(QPixmap.fromImage(QImage(
                self.model.get_2D_map('s', self.cursor[0], 'raw', self.window_lower, self.window_upper),
                self.model.get_size()[2],
                self.model.get_size()[1],
                self.model.get_size()[2] * 1,  # bytesperline = width*channel
                QImage.Format_Grayscale8)))
            self.sGraphicsView.raw_img_item.setTransform(QTransform(0, -1, 0, 1, 0, 0, 0, 0, 1))

        if 'c' in scenes:
            self.cGraphicsView.raw_img_item.setPixmap(QPixmap.fromImage(QImage(
                self.model.get_2D_map('c', self.cursor[1], 'raw', self.window_lower, self.window_upper),
                self.model.get_size()[2],
                self.model.get_size()[0],
                self.model.get_size()[2] * 1,  # bytesperline = width*channel
                QImage.Format_Grayscale8)))
            self.cGraphicsView.raw_img_item.setTransform(QTransform(0, -1, 0, 1, 0, 0, 0, 0, 1))

    def init_views(self):
        self.update_scenes('asc')
        self.aGraphicsView.init_view()
        self.sGraphicsView.init_view()
        self.cGraphicsView.init_view()

    def clear_views(self):
        self._cursor = [0, 0, 0]
        self.aGraphicsView.clear()
        self.sGraphicsView.clear()
        self.cGraphicsView.clear()

    @property
    def cursor(self):
        return self._cursor

    @cursor.setter
    def cursor(self, new_cursor):
        if all([new_c == c for new_c, c in zip(new_cursor, self._cursor)]):
            return
        scenes = ''
        # check boundary
        if self.model.get_size() is None:
            self._cursor = [0, 0, 0]
            return
        for i in range(3):
            if new_cursor[i] < 0:
                new_cursor[i] = 0
            if new_cursor[i] > self.model.get_size()[i]:
                new_cursor[i] = self.model.get_size()[i]

        if new_cursor[2] != self._cursor[2]:
            scenes += 'a'
        if new_cursor[0] != self._cursor[0]:
            scenes += 's'
        if new_cursor[1] != self._cursor[1]:
            scenes += 'c'
        self._cursor = new_cursor
        self.update_scenes(scenes)

    @pyqtSlot('float', 'float')
    def scale_all_scenes(self, scale_x, scale_y):
        self.aGraphicsView.scale(scale_x, scale_y)
        self.sGraphicsView.scale(scale_x, scale_y)
        self.cGraphicsView.scale(scale_x, scale_y)

    @pyqtSlot('int', 'int', 'int')
    def move_cursor(self, delta_x, delta_y, delta_z):
        self.cursor = [self.cursor[0] + delta_x, self.cursor[1] + delta_y, self.cursor[2] + delta_z]

    @pyqtSlot('int', 'int', 'int')
    def set_cursor(self, x, y, z):
        self.cursor = [x, y, z]

    @pyqtSlot()
    def menu_open_triggered(self):
        filename, _ = QFileDialog.getOpenFileName(self, 'select file to open', self.model.last_wd, filter='*.nii.gz')
        if not filename:
            return

        message_box = QMessageBox(self)
        message_box.setWindowTitle('Image type selection')
        message_box.setText('Which type is the selected image?')
        message_box.setIcon(QMessageBox.Question)
        raw_img_button = QPushButton('raw image', message_box)
        anno_img_button = QPushButton('annotation image', message_box)
        message_box.addButton(raw_img_button, QMessageBox.AcceptRole)
        message_box.addButton(anno_img_button, QMessageBox.AcceptRole)
        message_box.setStandardButtons(QMessageBox.Cancel)
        message_box.exec()

        if message_box.clickedButton() == raw_img_button:
            img_type = 'raw'
        elif message_box.clickedButton() == anno_img_button:
            img_type = 'anno'
        else:
            return

        self.clear_views()
        self.model.read_img(filename, img_type)
        if img_type == 'raw':
            self.cursor = [item // 2 for item in self.model.get_size()]
        self.init_views()
        return
