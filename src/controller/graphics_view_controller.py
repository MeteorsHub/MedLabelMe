from PyQt5 import QtGui
from PyQt5.QtCore import Qt, pyqtSignal, pyqtSlot
from PyQt5.QtGui import QPixmap, QPen, QTransform
from PyQt5.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsPixmapItem, QOpenGLWidget, QGraphicsLineItem

item2scene_transform = {'a': QTransform(0, 1, 0, 1, 0, 0, 0, 0, 1),
                        's': QTransform(0, -1, 0, 1, 0, 0, 0, 0, 1),
                        'c': QTransform(0, -1, 0, 1, 0, 0, 0, 0, 1)}


class ASCGraphicsView(QGraphicsView):
    scale_signal = pyqtSignal('float', 'float')
    set_focus_point_signal = pyqtSignal('int', 'int', 'int')
    move_focus_point_signal = pyqtSignal('int', 'int', 'int')

    def __init__(self, parent=None):
        super(ASCGraphicsView, self).__init__(parent)
        self.scene = QGraphicsScene(self)

        self.raw_img_item = QGraphicsPixmapItem()
        self.raw_img_item.setZValue(0)
        self.anno_img_item = QGraphicsPixmapItem()
        self.anno_img_item.setZValue(1)
        self.cross_bar_v_line_item = QGraphicsLineItem()
        self.cross_bar_h_line_item = QGraphicsLineItem()
        self.cross_bar_v_line_item.setZValue(100)
        self.cross_bar_h_line_item.setZValue(100)
        self.cross_bar_v_line_item.setPen(QPen(Qt.blue, 0, Qt.DotLine, Qt.FlatCap, Qt.RoundJoin))
        self.cross_bar_h_line_item.setPen(QPen(Qt.blue, 0, Qt.DotLine, Qt.FlatCap, Qt.RoundJoin))
        self.scene.addItem(self.raw_img_item)
        self.scene.addItem(self.anno_img_item)
        self.scene.addItem(self.cross_bar_v_line_item)
        self.scene.addItem(self.cross_bar_h_line_item)

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
        self.anno_img_item.setPixmap(QPixmap())

    def init_view(self):
        """after loading new image"""
        trans_mat = item2scene_transform[self.objectName()[0]]
        self.raw_img_item.setTransform(trans_mat)
        self.anno_img_item.setTransform(trans_mat)
        self.cross_bar_v_line_item.setTransform(trans_mat)
        self.cross_bar_h_line_item.setTransform(trans_mat)

        self.fitInView(self.raw_img_item, Qt.KeepAspectRatio)

    @pyqtSlot('int', 'int', 'int')
    def set_cross_bar(self, x, y, z):
        if self.objectName() == 'aGraphicsView':
            cross_bar_x = y
            cross_bar_y = x
        if self.objectName() == 'sGraphicsView':
            cross_bar_x = z
            cross_bar_y = y
        if self.objectName() == 'cGraphicsView':
            cross_bar_x = z
            cross_bar_y = x
        start_x = self.raw_img_item.boundingRect().topLeft().x()
        start_y = self.raw_img_item.boundingRect().topLeft().y()
        end_x = self.raw_img_item.boundingRect().bottomRight().x()
        end_y = self.raw_img_item.boundingRect().bottomRight().y()
        self.cross_bar_v_line_item.setLine(cross_bar_x, start_y, cross_bar_x, end_y)
        self.cross_bar_h_line_item.setLine(start_x, cross_bar_y, end_x, cross_bar_y)

    def mousePressEvent(self, event: QtGui.QMouseEvent):
        self._last_button_press = event.button()

        if event.button() == Qt.LeftButton:
            item_coord_pos = self.raw_img_item.mapFromScene(self.mapToScene(event.pos()))
            if self.objectName() == 'aGraphicsView':
                new_focus_point = [item_coord_pos.y(), item_coord_pos.x(), 999999]
            if self.objectName() == 'sGraphicsView':
                new_focus_point = [999999, item_coord_pos.y(), item_coord_pos.x()]
            if self.objectName() == 'cGraphicsView':
                new_focus_point = [item_coord_pos.y(), 999999, item_coord_pos.x()]
            self.set_focus_point_signal.emit(round(new_focus_point[0]), round(new_focus_point[1]),
                                             round(new_focus_point[2]))
        elif event.button() == Qt.MiddleButton:
            self._last_pos_middle_button = event.pos()
            self.setCursor(Qt.ClosedHandCursor)
        elif event.button() == Qt.RightButton:
            self._last_pos_right_button = event.pos()
        else:
            super(ASCGraphicsView, self).mousePressEvent(event)

    def mouseMoveEvent(self, event: QtGui.QMouseEvent):
        if self._last_button_press == Qt.LeftButton:
            item_coord_pos = self.raw_img_item.mapFromScene(self.mapToScene(event.pos()))
            if self.objectName() == 'aGraphicsView':
                new_focus_point = [item_coord_pos.y(), item_coord_pos.x(), 999999]
            if self.objectName() == 'sGraphicsView':
                new_focus_point = [999999, item_coord_pos.y(), item_coord_pos.x()]
            if self.objectName() == 'cGraphicsView':
                new_focus_point = [item_coord_pos.y(), 999999, item_coord_pos.x()]
            self.set_focus_point_signal.emit(round(new_focus_point[0]), round(new_focus_point[1]),
                                             round(new_focus_point[2]))
        elif self._last_button_press == Qt.MiddleButton:
            delta_x = event.x() - self._last_pos_middle_button.x()
            delta_y = event.y() - self._last_pos_middle_button.y()
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - delta_x)
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() - delta_y)
            self._last_pos_middle_button = event.pos()
        elif self._last_button_press == Qt.RightButton:
            delta = event.pos().y() - self._last_pos_right_button.y()
            scale = 1 - float(delta) / float(self.size().height())
            self.scale_signal.emit(scale, scale)
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
                self.move_focus_point_signal.emit(0, 0, -1)
            elif event.angleDelta().y() < 0:
                self.move_focus_point_signal.emit(0, 0, 1)
        if self.objectName() == 'sGraphicsView':
            if event.angleDelta().y() > 0:
                self.move_focus_point_signal.emit(-1, 0, 0)
            elif event.angleDelta().y() < 0:
                self.move_focus_point_signal.emit(1, 0, 0)
        if self.objectName() == 'cGraphicsView':
            if event.angleDelta().y() > 0:
                self.move_focus_point_signal.emit(0, -1, 0)
            elif event.angleDelta().y() < 0:
                self.move_focus_point_signal.emit(0, 1, 0)
