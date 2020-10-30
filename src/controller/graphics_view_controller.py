import math

from PyQt5 import QtGui, QtCore
from PyQt5.QtCore import Qt, pyqtSignal, pyqtSlot, QRectF
from PyQt5.QtGui import QPixmap, QPen, QTransform, QPolygonF
from PyQt5.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsPixmapItem, QOpenGLWidget, QGraphicsLineItem, \
    QGraphicsEllipseItem, QGraphicsPolygonItem, QScrollBar

item2scene_transform = {'a': QTransform(0, 1, 0, 1, 0, 0, 0, 0, 1),
                        's': QTransform(0, -1, 0, 1, 0, 0, 0, 0, 1),
                        'c': QTransform(0, -1, 0, 1, 0, 0, 0, 0, 1)}

BRUSH_TYPE_NO_BRUSH = 0
BRUSH_TYPE_CIRCLE_BRUSH = 1
BRUSH_TYPE_RECT_BRUSH = 2


class ASCGraphicsView(QGraphicsView):
    scale_signal = pyqtSignal('float', 'float')
    set_focus_point_signal = pyqtSignal('int', 'int', 'int')
    set_focus_point_percent_signal = pyqtSignal('float', 'float', 'float')
    move_focus_point_signal = pyqtSignal('int', 'int', 'int')
    # x, y, z, BRUSH_TYPE, BRUSH_SIZE, ERASE
    paint_anno_on_point_signal = pyqtSignal('int', 'int', 'int', 'int', 'int', 'bool', 'bool')

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

        self.paint_brush_circle_item = QGraphicsEllipseItem()
        self.paint_brush_rect_item = QGraphicsPolygonItem()
        self.paint_brush_circle_item.setZValue(10)
        self.paint_brush_rect_item.setZValue(11)
        self.paint_brush_circle_item.setVisible(False)
        self.paint_brush_rect_item.setVisible(False)
        self.paint_brush_circle_item.setPen(QPen(Qt.red, 0, Qt.DotLine, Qt.FlatCap, Qt.RoundJoin))
        self.paint_brush_rect_item.setPen(QPen(Qt.red, 0, Qt.DotLine, Qt.FlatCap, Qt.RoundJoin))

        self.scene.addItem(self.raw_img_item)
        self.scene.addItem(self.anno_img_item)
        self.scene.addItem(self.cross_bar_v_line_item)
        self.scene.addItem(self.cross_bar_h_line_item)
        self.scene.addItem(self.paint_brush_circle_item)
        self.scene.addItem(self.paint_brush_rect_item)

        self.setScene(self.scene)
        self.setViewport(QOpenGLWidget())

        self._last_button_press = Qt.NoButton
        self._last_pos_middle_button = None
        self._last_pos_right_button = None

        self._brush_stats = {'type': BRUSH_TYPE_NO_BRUSH, 'size': 5}

        self.setResizeAnchor(QGraphicsView.AnchorViewCenter)

        self.slice_scroll_bar = None
        self.image_size = None
        self.is_valid = False

    def clear(self):
        """before loading new image"""
        self._last_pos_middle_button = None
        self._last_pos_right_button = None
        self._last_button_press = Qt.NoButton
        self.raw_img_item.setPixmap(QPixmap())
        self.anno_img_item.setPixmap(QPixmap())
        self.paint_brush_circle_item.setVisible(False)
        self.paint_brush_rect_item.setVisible(False)
        self.image_size = None
        self.is_valid = False

    def init_view(self, image_size):
        """after loading new image"""
        self.is_valid = True
        self.image_size = image_size
        self.slice_scroll_bar = self.parent().findChild(QScrollBar, self.objectName()[0] + 'SliceScrollBar')

        trans_mat = item2scene_transform[self.objectName()[0]]
        self.raw_img_item.setTransform(trans_mat)
        self.anno_img_item.setTransform(trans_mat)
        self.cross_bar_v_line_item.setTransform(trans_mat)
        self.cross_bar_h_line_item.setTransform(trans_mat)
        self.paint_brush_rect_item.setTransform(trans_mat)
        self.paint_brush_circle_item.setTransform(trans_mat)

        self.fitInView(self.raw_img_item, Qt.KeepAspectRatio)
        self.paint_brush_circle_item.setVisible(False)
        self.paint_brush_rect_item.setVisible(False)

    @property
    def brush_stats(self):
        return self._brush_stats

    @brush_stats.setter
    def brush_stats(self, stats_tuple):
        b_type, size = stats_tuple
        if b_type in [BRUSH_TYPE_NO_BRUSH, BRUSH_TYPE_CIRCLE_BRUSH, BRUSH_TYPE_RECT_BRUSH]:
            self._brush_stats['type'] = b_type
            self._brush_stats['size'] = size
        if b_type != BRUSH_TYPE_NO_BRUSH:
            self.setMouseTracking(True)
        else:
            self.setMouseTracking(False)

    def update_brush_preview(self, x, y, out_of_sight=False):
        if not self.is_valid or self.brush_stats['type'] == BRUSH_TYPE_NO_BRUSH or out_of_sight:
            self.paint_brush_rect_item.setVisible(False)
            self.paint_brush_circle_item.setVisible(False)
            return

        center = self.anno_img_item.mapFromScene(self.mapToScene(x, y))

        start_x = self.raw_img_item.boundingRect().topLeft().x()
        start_y = self.raw_img_item.boundingRect().topLeft().y()
        end_x = self.raw_img_item.boundingRect().bottomRight().x()
        end_y = self.raw_img_item.boundingRect().bottomRight().y()
        center.setX(min(max(start_x, center.x()), end_x) + 0.5)
        center.setY(min(max(start_y, center.y()), end_y) + 0.5)
        top_left_x = int(center.x() - self.brush_stats['size'] / 2)
        top_left_y = int(center.y() - self.brush_stats['size'] / 2)
        rect = QRectF(top_left_x, top_left_y, self.brush_stats['size'], self.brush_stats['size'])
        if self.brush_stats['type'] == BRUSH_TYPE_CIRCLE_BRUSH:
            self.paint_brush_rect_item.setVisible(False)
            self.paint_brush_circle_item.setVisible(True)
            self.paint_brush_circle_item.setRect(rect)
        if self.brush_stats['type'] == BRUSH_TYPE_RECT_BRUSH:
            self.paint_brush_rect_item.setVisible(True)
            self.paint_brush_circle_item.setVisible(False)
            self.paint_brush_rect_item.setPolygon(QPolygonF(rect))

    def anno_paint(self, x, y, erase=False, new_step=False):
        pos_on_item = self.raw_img_item.mapFromScene(self.mapToScene(x, y))
        if self.objectName() == 'aGraphicsView':
            paint_point = [pos_on_item.y(), pos_on_item.x(), 999999]
        if self.objectName() == 'sGraphicsView':
            paint_point = [999999, pos_on_item.y(), pos_on_item.x()]
        if self.objectName() == 'cGraphicsView':
            paint_point = [pos_on_item.y(), 999999, pos_on_item.x()]
        self.paint_anno_on_point_signal.emit(
            math.floor(paint_point[0]), math.floor(paint_point[1]), math.floor(paint_point[2]),
            self.brush_stats['type'], self.brush_stats['size'], erase, new_step)

    @pyqtSlot('int')
    def on_slice_scroll_bar_changed(self, value):
        if not self.is_valid:
            return
        ratios = [-1, -1, -1]
        ratio = (value - self.slice_scroll_bar.minimum()) / \
                (self.slice_scroll_bar.maximum() - self.slice_scroll_bar.minimum())
        if self.objectName() == 'aGraphicsView':
            ratios[2] = ratio
        if self.objectName() == 'sGraphicsView':
            ratios[0] = ratio
        if self.objectName() == 'cGraphicsView':
            ratios[1] = ratio
        self.set_focus_point_percent_signal.emit(ratios[0], ratios[1], ratios[2])

    @pyqtSlot('int', 'int')
    def set_brush_stats(self, b_type, size):
        self.brush_stats = [b_type, size]

    @pyqtSlot('int', 'int', 'int')
    def set_cross_bar(self, x, y, z):
        if self.objectName() == 'aGraphicsView':
            cross_bar_x = y
            cross_bar_y = x
            slice_bar_ratio = z / self.image_size[2]
        if self.objectName() == 'sGraphicsView':
            cross_bar_x = z
            cross_bar_y = y
            slice_bar_ratio = x / self.image_size[0]
        if self.objectName() == 'cGraphicsView':
            cross_bar_x = z
            cross_bar_y = x
            slice_bar_ratio = y / self.image_size[1]
        # cross line in voxel center
        cross_bar_x = cross_bar_x + 0.5
        cross_bar_y = cross_bar_y + 0.5
        start_x = self.raw_img_item.boundingRect().topLeft().x()
        start_y = self.raw_img_item.boundingRect().topLeft().y()
        end_x = self.raw_img_item.boundingRect().bottomRight().x()
        end_y = self.raw_img_item.boundingRect().bottomRight().y()
        self.cross_bar_v_line_item.setLine(cross_bar_x, start_y, cross_bar_x, end_y)
        self.cross_bar_h_line_item.setLine(start_x, cross_bar_y, end_x, cross_bar_y)

        slice_bar_value = round(slice_bar_ratio * (self.slice_scroll_bar.maximum() - self.slice_scroll_bar.minimum())) \
                          + self.slice_scroll_bar.minimum()
        self.slice_scroll_bar.setValue(slice_bar_value)

    def mousePressEvent(self, event: QtGui.QMouseEvent):
        self._last_button_press = event.button()

        if self.brush_stats['type'] == BRUSH_TYPE_NO_BRUSH:
            if event.button() == Qt.LeftButton:
                item_coord_pos = self.raw_img_item.mapFromScene(self.mapToScene(event.pos()))
                if self.objectName() == 'aGraphicsView':
                    new_focus_point = [item_coord_pos.y(), item_coord_pos.x(), 999999]
                if self.objectName() == 'sGraphicsView':
                    new_focus_point = [999999, item_coord_pos.y(), item_coord_pos.x()]
                if self.objectName() == 'cGraphicsView':
                    new_focus_point = [item_coord_pos.y(), 999999, item_coord_pos.x()]
                self.set_focus_point_signal.emit(math.floor(new_focus_point[0]), math.floor(new_focus_point[1]),
                                                 math.floor(new_focus_point[2]))
            elif event.button() == Qt.MiddleButton:
                self._last_pos_middle_button = event.pos()
                self.setCursor(Qt.ClosedHandCursor)
            elif event.button() == Qt.RightButton:
                self._last_pos_right_button = event.pos()
            else:
                super(ASCGraphicsView, self).mousePressEvent(event)
        if self.brush_stats['type'] in [BRUSH_TYPE_CIRCLE_BRUSH, BRUSH_TYPE_RECT_BRUSH]:
            if event.button() == Qt.LeftButton:
                self.anno_paint(event.x(), event.y(), erase=False, new_step=True)
            elif event.button() == Qt.MiddleButton:
                self._last_pos_middle_button = event.pos()
                self.setCursor(Qt.ClosedHandCursor)
            elif event.button() == Qt.RightButton:
                self.anno_paint(event.x(), event.y(), erase=True, new_step=True)

    def mouseMoveEvent(self, event: QtGui.QMouseEvent):
        if self.brush_stats['type'] == BRUSH_TYPE_NO_BRUSH:
            if self._last_button_press == Qt.LeftButton:
                item_coord_pos = self.raw_img_item.mapFromScene(self.mapToScene(event.pos()))
                if self.objectName() == 'aGraphicsView':
                    new_focus_point = [item_coord_pos.y(), item_coord_pos.x(), 999999]
                if self.objectName() == 'sGraphicsView':
                    new_focus_point = [999999, item_coord_pos.y(), item_coord_pos.x()]
                if self.objectName() == 'cGraphicsView':
                    new_focus_point = [item_coord_pos.y(), 999999, item_coord_pos.x()]
                self.set_focus_point_signal.emit(math.floor(new_focus_point[0]), math.floor(new_focus_point[1]),
                                                 math.floor(new_focus_point[2]))
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
        if self.brush_stats['type'] in [BRUSH_TYPE_CIRCLE_BRUSH, BRUSH_TYPE_RECT_BRUSH]:
            self.update_brush_preview(event.x(), event.y())
            if self._last_button_press == Qt.LeftButton:
                self.anno_paint(event.x(), event.y(), erase=False, new_step=False)
            elif self._last_button_press == Qt.MiddleButton:
                delta_x = event.x() - self._last_pos_middle_button.x()
                delta_y = event.y() - self._last_pos_middle_button.y()
                self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - delta_x)
                self.verticalScrollBar().setValue(self.verticalScrollBar().value() - delta_y)
                self._last_pos_middle_button = event.pos()
            elif self._last_button_press == Qt.RightButton:
                self.anno_paint(event.x(), event.y(), erase=True, new_step=False)

    def mouseReleaseEvent(self, event: QtGui.QMouseEvent):
        self._last_button_press = Qt.NoButton

        if self.brush_stats['type'] == BRUSH_TYPE_NO_BRUSH:
            if event.button() == Qt.MiddleButton:
                self.setCursor(Qt.ArrowCursor)
        if self.brush_stats['type'] in [BRUSH_TYPE_CIRCLE_BRUSH, BRUSH_TYPE_RECT_BRUSH]:
            if event.button() == Qt.LeftButton:
                pass
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

    def leaveEvent(self, event: QtCore.QEvent):
        self._last_button_press = Qt.NoButton
        if self.brush_stats['type'] == BRUSH_TYPE_NO_BRUSH:
            super(ASCGraphicsView, self).leaveEvent(event)
        else:
            self.update_brush_preview(0, 0, out_of_sight=True)
