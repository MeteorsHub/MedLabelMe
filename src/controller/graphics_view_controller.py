from PyQt5 import QtGui
from PyQt5.QtCore import Qt, pyqtSignal, pyqtSlot
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsPixmapItem, QOpenGLWidget, QGraphicsLineItem


class ASCGraphicsView(QGraphicsView):
    view_scale_signal = pyqtSignal('float', 'float')
    view_set_cursor_signal = pyqtSignal('int', 'int', 'int')
    view_move_cursor_signal = pyqtSignal('int', 'int', 'int')

    def __init__(self, parent=None):
        super(ASCGraphicsView, self).__init__(parent)
        self.scene = QGraphicsScene(self)
        self.raw_img_item = QGraphicsPixmapItem()
        self.cross_bar_v_line_item = QGraphicsLineItem()
        self.cross_bar_h_line_item = QGraphicsLineItem()
        self.scene.addItem(self.raw_img_item)
        self.setScene(self.scene)
        self.setViewport(QOpenGLWidget())

        self._last_button_press = None
        self._last_pos_middle_button = None
        self._last_pos_right_button = None

        self.setResizeAnchor(QGraphicsView.AnchorViewCenter)

    def clear(self):
        """before loading new image"""
        self._last_pos_middle_button = None
        self._last_pos_right_button = None
        self._last_button_press = None
        self.raw_img_item.setPixmap(QPixmap())

    def init_view(self):
        """after loading new image"""
        self.fitInView(self.raw_img_item, Qt.KeepAspectRatio)

    @pyqtSlot('int', 'int', 'int')
    def set_cross_bar(self, x, y, z):
        if self.objectName() == 'aGraphicsView':
            cross_bar_x = x
            cross_bar_y = y
        if self.objectName() == 'sGraphicsView':
            cross_bar_x = y
            cross_bar_y = z
        if self.objectName() == 'cGraphicsView':
            cross_bar_x = x
            cross_bar_y = z
        start_x = self.raw_img_item.boundingRect().topLeft().x()
        start_y = self.raw_img_item.boundingRect().topLeft().y()
        end_x = self.raw_img_item.boundingRect().bottomRight().x()
        end_y = self.raw_img_item.boundingRect().bottomRight().y()
        self.cross_bar_v_line_item.setLine(cross_bar_x, start_y, cross_bar_x, end_y)
        self.cross_bar_h_line_item.setLine(start_x, cross_bar_y, end_x, cross_bar_y)

    def mousePressEvent(self, event: QtGui.QMouseEvent):
        self._last_button_press = event.button()

        if event.button() == Qt.LeftButton:
            pass
        elif event.button() == Qt.MiddleButton:
            self._last_pos_middle_button = event.pos()
            self.setCursor(Qt.ClosedHandCursor)
        elif event.button() == Qt.RightButton:
            self._last_pos_right_button = event.pos()
        else:
            super(ASCGraphicsView, self).mousePressEvent(event)

    def mouseMoveEvent(self, event: QtGui.QMouseEvent):
        if self._last_button_press == Qt.LeftButton:
            pass
        elif self._last_button_press == Qt.MiddleButton:
            delta_x = event.x() - self._last_pos_middle_button.x()
            delta_y = event.y() - self._last_pos_middle_button.y()
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - delta_x)
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() - delta_y)
            self._last_pos_middle_button = event.pos()
        elif self._last_button_press == Qt.RightButton:
            delta = event.pos().y() - self._last_pos_right_button.y()
            scale = 1 - float(delta) / float(self.size().height())
            self.view_scale_signal.emit(scale, scale)
            self._last_pos_right_button = event.pos()
        else:
            super(ASCGraphicsView, self).mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QtGui.QMouseEvent):
        if event.button() == Qt.LeftButton:
            pass
        elif event.button() == Qt.MiddleButton:
            self.setCursor(Qt.ArrowCursor)
        elif event.button() == Qt.RightButton:
            pass
        else:
            super(ASCGraphicsView, self).mouseReleaseEvent(event)

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
