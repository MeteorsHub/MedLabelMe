from PyQt5 import QtGui
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsPixmapItem, QOpenGLWidget


class ASCGraphicsView(QGraphicsView):
    view_scale_signal = pyqtSignal('float', 'float')
    view_set_cursor_signal = pyqtSignal('int', 'int', 'int')
    view_move_cursor_signal = pyqtSignal('int', 'int', 'int')

    def __init__(self, parent=None):
        super(ASCGraphicsView, self).__init__(parent)
        self.scene = QGraphicsScene(self)
        self.raw_img_item = QGraphicsPixmapItem()
        self.scene.addItem(self.raw_img_item)
        self.setScene(self.scene)
        self.setViewport(QOpenGLWidget())

        self.last_button_press = None
        self.last_pos_button = None

        self.setResizeAnchor(QGraphicsView.AnchorViewCenter)

    def clear(self):
        """before loading new image"""
        self.last_pos_button = None
        self.last_button_press = None
        self.raw_img_item.setPixmap(QPixmap())

    def init_view(self):
        """after loading new image"""
        self.fitInView(self.raw_img_item, Qt.KeepAspectRatio)

    def mouseMoveEvent(self, event: QtGui.QMouseEvent):
        super(ASCGraphicsView, self).mouseMoveEvent(event)
        if self.last_button_press == Qt.RightButton:
            delta = event.pos().y() - self.last_pos_button.y()
            scale = 1 - float(delta) / float(self.size().height())
            self.view_scale_signal.emit(scale, scale)
            self.last_pos_button = event.pos()

    def mousePressEvent(self, event: QtGui.QMouseEvent):
        super(ASCGraphicsView, self).mousePressEvent(event)
        self.last_button_press = event.button()
        self.last_pos_button = event.pos()
        if event.button() == Qt.LeftButton:
            pass

    def wheelEvent(self, event: QtGui.QWheelEvent):
        # super(ASCGraphicsView, self).wheelEvent(event)
        if self.objectName() == 'aGraphicsView':
            if event.angleDelta().y() > 0:
                self.view_move_cursor_signal.emit(0, 0, -1)
            elif event.angleDelta().y() < 0:
                self.view_move_cursor_signal.emit(0, 0, 1)
        if self.objectName() == 'sGraphicsView':
            if event.angleDelta().y() > 0:
                self.view_move_cursor_signal.emit(-1, 0, 0)
            elif event.angleDelta().y() < 0:
                self.view_move_cursor_signal.emit(1, 0, 0)
        if self.objectName() == 'cGraphicsView':
            if event.angleDelta().y() > 0:
                self.view_move_cursor_signal.emit(0, -1, 0)
            elif event.angleDelta().y() < 0:
                self.view_move_cursor_signal.emit(0, 1, 0)
