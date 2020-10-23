import os
from enum import Enum

from PyQt5.QtCore import pyqtSlot, pyqtSignal
from PyQt5.QtGui import QPixmap, QImage, QIcon, QCursor
from PyQt5.QtWidgets import QMainWindow, QFileDialog, QMessageBox, QPushButton, QListWidgetItem

from controller.graphics_view_controller import BRUSH_TYPE_NO_BRUSH, BRUSH_TYPE_RECT_BRUSH, BRUSH_TYPE_CIRCLE_BRUSH
from model.model import Model
from utils.exception_utils import ImageTypeError
from view.main_window_ui import Ui_MainWindow


class MainWindow(QMainWindow, Ui_MainWindow):
    set_cross_bar_signal = pyqtSignal('int', 'int', 'int')
    set_brush_stats_signal = pyqtSignal('int', 'int')

    class OpMode(Enum):
        CURSOR = 1
        BRUSH = 2

    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self.parent = parent
        self.setupUi(self)
        self.model = Model()

        self._focus_point = [0, 0, 0]  # w, h, d or x, y, z
        self._hu_window = [0, 400]
        self._operation_mode = self.OpMode.CURSOR
        self._paint_cursor_pixmap = QPixmap()
        self._paint_cursor = QCursor(self._paint_cursor_pixmap)

        self.clear_views()

    def update_scenes(self, scenes='asc'):
        if not self.model.is_valid():
            return
        if 'a' in scenes:
            self.aGraphicsView.raw_img_item.setPixmap(QPixmap.fromImage(QImage(
                self.model.get_2D_map_in_window('a', self.focus_point[2], 'raw', self.window_bottom, self.window_top),
                self.model.get_size()[1],
                self.model.get_size()[0],
                self.model.get_size()[1] * 1,  # bytesperline = width*channel
                QImage.Format_Grayscale8)))  # x, y
            self.aGraphicsView.anno_img_item.setPixmap(QPixmap.fromImage(QImage(
                self.model.get_2D_map_in_window('a', self.focus_point[2], 'anno', colored_anno=True, alpha=0.5),
                self.model.get_size()[1],
                self.model.get_size()[0],
                self.model.get_size()[1] * 4,  # bytesperline = width*channel
                QImage.Format_RGBA8888)))  # x, y

        if 's' in scenes:
            self.sGraphicsView.raw_img_item.setPixmap(QPixmap.fromImage(QImage(
                self.model.get_2D_map_in_window('s', self.focus_point[0], 'raw', self.window_bottom, self.window_top),
                self.model.get_size()[2],
                self.model.get_size()[1],
                self.model.get_size()[2] * 1,  # bytesperline = width*channel
                QImage.Format_Grayscale8)))
            self.sGraphicsView.anno_img_item.setPixmap(QPixmap.fromImage(QImage(
                self.model.get_2D_map_in_window('s', self.focus_point[0], 'anno', colored_anno=True, alpha=0.5),
                self.model.get_size()[2],
                self.model.get_size()[1],
                self.model.get_size()[2] * 4,  # bytesperline = width*channel
                QImage.Format_RGBA8888)))

        if 'c' in scenes:
            self.cGraphicsView.raw_img_item.setPixmap(QPixmap.fromImage(QImage(
                self.model.get_2D_map_in_window('c', self.focus_point[1], 'raw', self.window_bottom, self.window_top),
                self.model.get_size()[2],
                self.model.get_size()[0],
                self.model.get_size()[2] * 1,  # bytesperline = width*channel
                QImage.Format_Grayscale8)))
            self.cGraphicsView.anno_img_item.setPixmap(QPixmap.fromImage(QImage(
                self.model.get_2D_map_in_window('c', self.focus_point[1], 'anno', colored_anno=True, alpha=0.5),
                self.model.get_size()[2],
                self.model.get_size()[0],
                self.model.get_size()[2] * 4,  # bytesperline = width*channel
                QImage.Format_RGBA8888)))

    def update_anno_targets_list(self):
        self.model.compute_img_stats('anno')
        self.targetList.clear()
        num_labels = self.model.get_anno_num_labels()
        for i_label in range(1, num_labels + 1):
            # create icon
            pixmap = QPixmap(100, 100)
            pixmap.fill(self.model.label_colors[i_label - 1])
            icon = QIcon(pixmap)
            # items
            target_centers = self.model.get_anno_target_centers_for_label(i_label)  # [n, (d, h, w)]
            target_ids = self.model.get_anno_target_ids()
            for i_centers in range(len(target_centers)):
                item = QListWidgetItem('[Label_%d] #%d' % (i_label, i_centers + 1))
                item.setIcon(icon)
                item.target_id = target_ids[i_centers]
                item.target_label = i_label
                self.targetList.addItem(item)

    def init_views(self):
        """after new file loaded"""
        self.update_scenes('asc')
        self.aGraphicsView.init_view()
        self.sGraphicsView.init_view()
        self.cGraphicsView.init_view()
        self.xSpinBox.setMaximum(self.model.get_size()[0])
        self.ySpinBox.setMaximum(self.model.get_size()[1])
        self.zSpinBox.setMaximum(self.model.get_size()[2])
        self.lineEditImageName.setText(self.model.get_img_filepath('raw'))
        self.lineEditAnnotationName.setText(self.model.get_img_filepath('anno'))
        self.lineEditImageSize.setText(
            '(%d, %d, %d)' % (self.model.get_size()[0], self.model.get_size()[1], self.model.get_size()[2]))
        self.valueUnderCursorList.addItem(QListWidgetItem())
        self.valueUnderCursorList.addItem(QListWidgetItem())
        self.update_anno_targets_list()
        self.operation_mode = self.OpMode.CURSOR
        self.opModeTab.setCurrentIndex(0)

    def clear_views(self):
        """welcome page and after clear images"""
        self._focus_point = [0, 0, 0]
        self.aGraphicsView.clear()
        self.sGraphicsView.clear()
        self.cGraphicsView.clear()
        self.xSpinBox.setMaximum(1)
        self.ySpinBox.setMaximum(1)
        self.zSpinBox.setMaximum(1)
        self.lineEditImageName.setText('Null')
        self.lineEditAnnotationName.setText('Null')
        self.lineEditImageSize.setText('(0, 0, 0)')
        for i in range(self.valueUnderCursorList.count()):
            self.valueUnderCursorList.item(0).setText('')
        self.targetList.clear()
        self.operation_mode = self.OpMode.CURSOR
        self.opModeTab.setCurrentIndex(0)
        self.brushSizeSpinBox.setValue(5)

    @property
    def operation_mode(self):
        return self._operation_mode

    @operation_mode.setter
    def operation_mode(self, mode):
        if not isinstance(mode, self.OpMode):
            return
        if mode == self.OpMode.CURSOR:
            self.opModeTab.setCurrentIndex(0)
        if mode == self.OpMode.BRUSH:
            self.opModeTab.setCurrentIndex(1)

        if self._operation_mode != mode:
            if mode == self.OpMode.CURSOR:
                self.set_brush_stats_signal.emit(BRUSH_TYPE_NO_BRUSH, 5)
            if mode == self.OpMode.BRUSH:
                if self.circleRadioButton.isChecked():
                    self.set_brush_stats_signal.emit(BRUSH_TYPE_CIRCLE_BRUSH, self.brushSizeSlider.value())
                elif self.rectRadioButton.isChecked():
                    self.set_brush_stats_signal.emit(BRUSH_TYPE_RECT_BRUSH, self.brushSizeSlider.value())
            self._operation_mode = mode

    @property
    def focus_point(self):
        return self._focus_point.copy()

    @focus_point.setter
    def focus_point(self, new_focus_point):
        if all([new_c == c for new_c, c in zip(new_focus_point, self._focus_point)]):
            return
        scenes = ''
        # check boundary
        if self.model.get_size() is None:
            self._focus_point = [0, 0, 0]
            return
        for i in range(3):
            if new_focus_point[i] < 0:
                new_focus_point[i] = 0
            if new_focus_point[i] > self.model.get_size()[i]:
                new_focus_point[i] = self.model.get_size()[i]

        if new_focus_point[2] != self._focus_point[2]:
            scenes += 'a'
        if new_focus_point[0] != self._focus_point[0]:
            scenes += 's'
        if new_focus_point[1] != self._focus_point[1]:
            scenes += 'c'
        self._focus_point = new_focus_point

        # ui
        for i, spin_box in enumerate([self.xSpinBox, self.ySpinBox, self.zSpinBox]):
            spin_box.setValue(new_focus_point[i] + 1)
        self.valueUnderCursorList.item(0).setText(
            'image:\t\t%d' % self.model.get_voxel_value_at_point(self.focus_point, 'raw'))
        self.valueUnderCursorList.item(1).setText(
            'annotation:\t%d' % self.model.get_voxel_value_at_point(self.focus_point, 'anno'))
        self.set_cross_bar_signal.emit(new_focus_point[0], new_focus_point[1], new_focus_point[2])
        self.update_scenes(scenes)

    @property
    def window_bottom(self):
        return self._hu_window[0]

    @property
    def window_top(self):
        return self._hu_window[1]

    @property
    def window_level(self):
        return (self._hu_window[0] + self._hu_window[1]) // 2

    @property
    def window_width(self):
        return self._hu_window[1] - self._hu_window[0]

    def set_hu_window_ui(self):
        self.windowLevelSpinBox.setValue(self.window_level)
        self.windowWidthSpinBox.setValue(self.window_width)
        self.windowBottomSpinBox.setValue(self.window_bottom)
        self.windowTopspinBox.setValue(self.window_top)

    @window_bottom.setter
    def window_bottom(self, bottom):
        if bottom < self.window_top:
            self._hu_window[0] = bottom
        self.set_hu_window_ui()
        self.update_scenes('asc')

    @window_top.setter
    def window_top(self, top):
        if top > self.window_bottom:
            self._hu_window[1] = top
        self.set_hu_window_ui()
        self.update_scenes('asc')

    @window_level.setter
    def window_level(self, level):
        old_level = self.window_level
        self._hu_window[0] += level - old_level
        self._hu_window[1] += level - old_level
        self.set_hu_window_ui()
        self.update_scenes('asc')

    @window_width.setter
    def window_width(self, width):
        level = self.window_level
        self._hu_window[0] = level - width // 2
        self._hu_window[1] = self._hu_window[0] + width
        self.set_hu_window_ui()
        self.update_scenes('asc')

    @pyqtSlot('float', 'float')
    def scale_all_scenes(self, scale_x, scale_y):
        self.aGraphicsView.scale(scale_x, scale_y)
        self.sGraphicsView.scale(scale_x, scale_y)
        self.cGraphicsView.scale(scale_x, scale_y)

    @pyqtSlot('int', 'int', 'int')
    def move_focus_point(self, delta_x, delta_y, delta_z):
        self.focus_point = [self.focus_point[0] + delta_x, self.focus_point[1] + delta_y, self.focus_point[2] + delta_z]

    @pyqtSlot('int', 'int', 'int')
    def set_focus_point(self, x, y, z):
        new_focus_point = self.focus_point
        for i, item in enumerate([x, y, z]):
            if item < 100000:  # bigger than this value means no change
                new_focus_point[i] = item
        self.focus_point = new_focus_point

    @pyqtSlot()
    def menu_open_triggered(self):
        filename, _ = QFileDialog.getOpenFileName(self, 'select file to open', self.model.last_wd, filter='*.nii.gz')
        if not filename:
            return

        if self.model.is_valid():
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
        else:
            img_type = 'raw'

        try:
            if img_type == 'raw':
                self.clear_views()
                self.model.read_img(filename, img_type)
                self.init_views()
                self.focus_point = [item // 2 for item in self.model.get_size()]
            if img_type == 'anno':
                self.model.read_img(filename, img_type)
                self.init_views()
        except ImageTypeError as e:
            QMessageBox.warning(self, 'Wrong image type!', e.__str__())
            self.clear_views()

    @pyqtSlot()
    def menu_save_triggered(self):
        if not self.model.is_valid():
            return
        if os.path.exists(self.model.get_img_filepath('anno')):
            default_filename = self.model.get_img_filepath('anno')
        else:
            default_filename = os.path.join(self.model.last_wd, os.path.basename(self.model.get_img_filepath('raw')))

        filename, _ = QFileDialog.getSaveFileName(
            self, 'select where to save the annotation file', default_filename, filter='*.nii.gz')
        self.model.save_anno(filename)

    @pyqtSlot()
    def menu_close_triggered(self):
        self.model.clear()
        self.clear_views()

    @pyqtSlot('int')
    def on_x_spin_box_value_changed(self, x):
        for i, spin_box in enumerate([self.xSpinBox, self.ySpinBox, self.zSpinBox]):
            spin_box.blockSignals(True)
        self.set_focus_point(x - 1, 999999, 999999)
        for i, spin_box in enumerate([self.xSpinBox, self.ySpinBox, self.zSpinBox]):
            spin_box.blockSignals(False)

    @pyqtSlot('int')
    def on_y_spin_box_value_changed(self, y):
        for i, spin_box in enumerate([self.xSpinBox, self.ySpinBox, self.zSpinBox]):
            spin_box.blockSignals(True)
        self.set_focus_point(999999, y - 1, 999999)
        for i, spin_box in enumerate([self.xSpinBox, self.ySpinBox, self.zSpinBox]):
            spin_box.blockSignals(False)

    @pyqtSlot('int')
    def on_z_spin_box_value_changed(self, z):
        for spin_box in [self.xSpinBox, self.ySpinBox, self.zSpinBox]:
            spin_box.blockSignals(True)
        self.set_focus_point(999999, 999999, z - 1)
        for spin_box in [self.xSpinBox, self.ySpinBox, self.zSpinBox]:
            spin_box.blockSignals(False)

    @pyqtSlot('int')
    def on_window_level_spin_box_value_changed(self, level):
        for spin_box in [self.windowLevelSpinBox, self.windowWidthSpinBox, self.windowBottomSpinBox,
                         self.windowTopspinBox]:
            spin_box.blockSignals(True)
        self.window_level = level
        for spin_box in [self.windowLevelSpinBox, self.windowWidthSpinBox, self.windowBottomSpinBox,
                         self.windowTopspinBox]:
            spin_box.blockSignals(False)

    @pyqtSlot('int')
    def on_window_width_spin_box_value_changed(self, width):
        for spin_box in [self.windowLevelSpinBox, self.windowWidthSpinBox, self.windowBottomSpinBox,
                         self.windowTopspinBox]:
            spin_box.blockSignals(True)
        self.window_width = width
        for spin_box in [self.windowLevelSpinBox, self.windowWidthSpinBox, self.windowBottomSpinBox,
                         self.windowTopspinBox]:
            spin_box.blockSignals(False)

    @pyqtSlot('int')
    def on_window_bottom_spin_box_value_changed(self, bottom):
        for spin_box in [self.windowLevelSpinBox, self.windowWidthSpinBox, self.windowBottomSpinBox,
                         self.windowTopspinBox]:
            spin_box.blockSignals(True)
        self.window_bottom = bottom
        for spin_box in [self.windowLevelSpinBox, self.windowWidthSpinBox, self.windowBottomSpinBox,
                         self.windowTopspinBox]:
            spin_box.blockSignals(False)

    @pyqtSlot('int')
    def on_window_top_spin_box_value_changed(self, top):
        for spin_box in [self.windowLevelSpinBox, self.windowWidthSpinBox, self.windowBottomSpinBox,
                         self.windowTopspinBox]:
            spin_box.blockSignals(True)
        self.window_top = top
        for spin_box in [self.windowLevelSpinBox, self.windowWidthSpinBox, self.windowBottomSpinBox,
                         self.windowTopspinBox]:
            spin_box.blockSignals(False)

    @pyqtSlot('QListWidgetItem*')
    def on_target_list_item_clicked(self, item):
        target_centers = self.model.get_anno_target_centers_for_label(item.target_label)
        d, h, w = target_centers[item.target_id - 1]
        self.set_focus_point(w, h, d)

    @pyqtSlot('int')
    def on_current_op_mode_tab_changed(self, current_index):
        if current_index == 0:
            self.operation_mode = self.OpMode.CURSOR
        if current_index == 1:
            self.operation_mode = self.OpMode.BRUSH

    @pyqtSlot('int')
    def on_brush_size_changed(self, size):
        if self.operation_mode == self.OpMode.CURSOR:
            return
        if self.circleRadioButton.isChecked():
            self.set_brush_stats_signal.emit(BRUSH_TYPE_CIRCLE_BRUSH, size)
        elif self.rectRadioButton.isChecked():
            self.set_brush_stats_signal.emit(BRUSH_TYPE_RECT_BRUSH, size)

    @pyqtSlot()
    def on_brush_type_clicked(self):
        if self.operation_mode == self.OpMode.CURSOR:
            return
        size = self.brushSizeSlider.value()
        if self.circleRadioButton.isChecked():
            self.set_brush_stats_signal.emit(BRUSH_TYPE_CIRCLE_BRUSH, size)
        elif self.rectRadioButton.isChecked():
            self.set_brush_stats_signal.emit(BRUSH_TYPE_RECT_BRUSH, size)

    @pyqtSlot('int', 'int', 'int', 'int', 'int', 'bool')
    def on_paint_on_point(self, x, y, z, brush_type, brush_size, erase):
        if x > 100000:  # bigger than this value means painting axis
            axis = 'x'
            x = self.focus_point[0]
        if y > 100000:
            axis = 'xy'
            y = self.focus_point[1]
        if z > 100000:
            axis = 'z'
            z = self.focus_point[2]
        label = 1
        self.model.anno_paint(x, y, z, axis, label, brush_type, brush_size, erase)
        self.update_scenes('asc')

    @pyqtSlot()
    def on_refresh_list_button_clicked(self):
        self.update_anno_targets_list()

    @pyqtSlot()
    def on_delete_target_button_clicked(self):
        selected_target = self.targetList.currentItem()
        if selected_target is None:
            return
        target_id = selected_target.target_id
        self.model.delete_target(target_id)
        self.update_scenes('asc')
        self.update_anno_targets_list()
