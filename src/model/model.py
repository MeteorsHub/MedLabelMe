import os
from collections import deque

import SimpleITK as sitk
import cc3d
import numpy as np
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor

from controller.graphics_view_controller import BRUSH_TYPE_NO_BRUSH, BRUSH_TYPE_RECT_BRUSH, BRUSH_TYPE_CIRCLE_BRUSH
from utils.exception_utils import IllegalSizeError, ImageTypeError, ChangeNotSavedError


class Model:
    def __init__(self):
        self._raw_img = None
        self._anno_img = None
        self._anno_img_edit = None  # d, h, w
        self._anno_img_edit_undo_stack = deque(maxlen=5)
        self._anno_img_edit_redo_stack = deque(maxlen=5)
        self._raw_img_filepath = None
        self._anno_img_filepath = None
        self.last_read_dir = os.getcwd()
        self.last_save_dir = os.getcwd()

        self.label_colors = [QColor(Qt.red), QColor(Qt.green), QColor(Qt.yellow), QColor(Qt.magenta), QColor(Qt.blue)]

        self._raw_img_stats = {
            'min_val': None,
            'max_val': None
        }
        self._anno_img_stats = {
            'num_positive_labels': None,  # label 0 is background
            'target_ids': None,  # [n_target]. target id in target_id_map
            'target_labels': None,  # [n_targets]. order of target_ids.
            'target_centers': None,  # [n_targets]. order of target_ids.
            'target_id_map': None  # [d, h, w]
        }
        self._anno_img_edit_change_flag = False

    def clear(self):
        self._raw_img = None
        self._anno_img = None
        self._anno_img_edit = None
        self._anno_img_edit_undo_stack.clear()
        self._anno_img_edit_redo_stack.clear()
        self._raw_img_filepath = None
        self._anno_img_filepath = None

        self._raw_img_stats = {
            'min_val': None,
            'max_val': None
        }
        self._anno_img_stats = {
            'num_positive_labels': None,  # label 0 is background
            'target_ids': None,  # [n_target]. target id in target_id_map
            'target_labels': None,  # [n_targets]. order of target_ids.
            'target_centers': None,  # [n_targets]. order of target_ids.
            'target_id_map': None  # [d, h, w]
        }
        self._anno_img_edit_change_flag = False

    def read_img(self, filepath, img_type):
        assert img_type in ['raw', 'anno']
        if not os.path.exists(filepath):
            raise FileNotFoundError('%s do not exist' % filepath)
        self.last_read_dir = os.path.dirname(filepath)
        if img_type == 'raw':
            self._raw_img = sitk.ReadImage(filepath)
            self._raw_img_filepath = filepath
            self.compute_img_stats('raw')
            self._anno_img = sitk.Image(self.get_size(), sitk.sitkInt16)
            self._anno_img.CopyInformation(self._raw_img)
            self._anno_img_edit = sitk.GetArrayFromImage(self._anno_img).astype(np.int8)
            self._anno_img_filepath = '[newly created]'
        elif img_type == 'anno':
            anno_img = sitk.ReadImage(filepath)
            if sitk.GetArrayViewFromImage(anno_img).min() < 0 or sitk.GetArrayViewFromImage(anno_img).max() > 50:
                raise ImageTypeError(img_type='raw image', preferred_img_type='anno image')
            if anno_img.GetSize() != self._raw_img.GetSize():
                raise IllegalSizeError(anno_img.GetSize(), self._raw_img.GetSize())
            else:
                self._anno_img = anno_img
                self._anno_img_edit = sitk.GetArrayFromImage(self._anno_img).astype(np.int8)
                self._anno_img_filepath = filepath
        self.compute_img_stats('anno')
        self._anno_img_edit_undo_stack.clear()
        self._anno_img_edit_redo_stack.clear()

    def save_anno(self, filename):
        self.last_save_dir = os.path.dirname(filename)
        anno_img = sitk.GetImageFromArray(self._anno_img_edit.astype(np.int16))
        anno_img.CopyInformation(self._anno_img)
        self._anno_img = anno_img
        sitk.WriteImage(self._anno_img, filename)

    def compute_img_stats(self, img_type):
        assert img_type in ['raw', 'anno']
        if img_type == 'raw':
            if self._raw_img is None:
                for k in self._raw_img_stats.keys():
                    self._raw_img_stats[k] = None
            else:
                img = sitk.GetArrayViewFromImage(self._raw_img)
                self._raw_img_stats['min_val'] = img.min()
                self._raw_img_stats['max_val'] = img.max()
        if img_type == 'anno':
            if self._anno_img is None:
                for k in self._anno_img_stats.keys():
                    self._anno_img_stats[k] = None
            else:
                self._anno_img_stats['num_positive_labels'] = self._anno_img_edit.max()
                all_targets_map = cc3d.connected_components(self._anno_img_edit, connectivity=26, out_dtype=np.uint16)
                num_all_targets = all_targets_map.max()

                target_centers = []
                target_labels = []
                target_ids = []
                for i_target in range(1, num_all_targets + 1):
                    binary_map = all_targets_map == i_target
                    target_ids.append(i_target)
                    target_centers.append(Model.get_target_center(binary_map))
                    target_labels.append(
                        int(self._anno_img_edit[np.unravel_index(binary_map.argmax(), binary_map.shape)]))
                self._anno_img_stats['target_ids'] = target_ids
                self._anno_img_stats['target_labels'] = target_labels
                self._anno_img_stats['target_centers'] = target_centers
                self._anno_img_stats['target_id_map'] = all_targets_map
            self._anno_img_edit_change_flag = False

    @staticmethod
    def get_target_center(target_binary_map):
        assert target_binary_map.ndim == 3
        target_binary_map = target_binary_map.astype(np.int16)
        center = [-1, -1, -1]
        if target_binary_map.max() < 1:
            return center
        yz = np.sum(target_binary_map, 0)
        xz = np.sum(target_binary_map, 1)
        x = np.sum(xz, 1)
        z = np.sum(xz, 0)
        y = np.sum(yz, 1)
        return [np.argmax(x), np.argmax(y), np.argmax(z)]

    def get_2D_map_in_window(self, view, index, img_type='raw', low_bound=None, up_bound=None, colored_anno=True,
                             alpha=None):
        """colored_anno=True transit anno to RGB map, else grayscale.
        alpha only applied to foreground label(!=0) when colored_anno=True. """
        assert view in ['a', 's', 'c']
        assert img_type in ['raw', 'anno']
        if index < 0:
            index = 0
        if img_type == 'raw':
            itk_img = self._raw_img
        if img_type == 'anno':
            itk_img = self._anno_img

        if itk_img is None:
            return None

        if img_type == 'raw':
            img = sitk.GetArrayViewFromImage(itk_img)
        if img_type == 'anno':
            img = self._anno_img_edit
        img = np.transpose(img, (2, 1, 0))  # d, h, w to w, h, d

        if view == 'a':
            if index >= itk_img.GetSize()[2]:
                index = itk_img.GetSize()[2] - 1
            img_slice = img[:, :, index]  # x, y
        if view == 's':
            if index >= itk_img.GetSize()[0]:
                index = itk_img.GetSize()[0] - 1
            img_slice = img[index, :, :]  # y, z
        if view == 'c':
            if index >= itk_img.GetSize()[1]:
                index = itk_img.GetSize()[1] - 1
            img_slice = img[:, index, :]  # x, z

        value_min, value_max = self.get_voxel_value_bound()
        if img_type == 'anno':
            if colored_anno:
                img_slice = self.color_anno_img(img_slice, alpha)
            return img_slice.copy()
        if img_type == 'raw':
            if low_bound is None or low_bound < value_min:
                low_bound = value_min
            if up_bound is None or up_bound > value_max:
                up_bound = value_max
            img_slice = self.clip_img_in_window(img_slice, low_bound, up_bound, normalization=True)
            return img_slice.copy()

    def get_voxel_value_at_point(self, point, img_type):
        assert img_type in ['raw', 'anno']
        x, y, z = point
        if img_type == 'raw':
            if self._raw_img is None:
                return 0
            else:
                return sitk.GetArrayViewFromImage(self._raw_img)[z, y, x]
        if img_type == 'anno':
            if self._anno_img is None:
                return 0
            else:
                return self._anno_img_edit[z, y, x]

    def clip_img_in_window(self, img, low_bound, up_bound, normalization=False):
        value_min, value_max = self.get_voxel_value_bound()
        assert low_bound >= value_min and up_bound <= value_max
        img = np.clip(img, low_bound, up_bound)
        if normalization:
            img = (255 * (img.astype(np.float32) - low_bound) / (up_bound - low_bound)).astype(np.uint8)
        return img

    def color_anno_img(self, anno_img, alpha):
        anno_img = anno_img.copy().astype(np.int16)
        num_colors = max(min(len(self.label_colors), self._anno_img_stats['num_positive_labels']), 1)
        anno_img = np.where(anno_img == 0, anno_img, ((anno_img - 1) % num_colors + 1))

        # color_img = (255*label2rgb(anno_img, colors=self.label_colors, bg_label=0)).astype(np.uint8)  # too slow
        anno_img_expanded = np.expand_dims(anno_img, -1)
        tiled_anno_img = np.tile(anno_img_expanded, (1, 1, 3))
        bg_img = np.zeros(tiled_anno_img.shape, np.uint8)
        color_img = bg_img
        for i in range(num_colors):
            fg_img = np.ones(tiled_anno_img.shape, np.uint8)
            fg_img[:, :, 0] = self.label_colors[i].red()
            fg_img[:, :, 1] = self.label_colors[i].green()
            fg_img[:, :, 2] = self.label_colors[i].blue()
            color_img = np.where(anno_img_expanded == (i + 1), fg_img, color_img)

        if alpha is None:
            alpha_channel = 255 * np.ones(anno_img_expanded.shape, np.uint8)
        else:
            alpha_channel = np.where(anno_img_expanded == 0,
                                     np.zeros(anno_img_expanded.shape, np.uint8),
                                     round(alpha * 255) * np.ones(anno_img_expanded.shape, np.uint8))
        color_img = np.concatenate([color_img, alpha_channel], -1)
        return color_img

    def get_size(self):
        """return x, y, z"""
        if self._raw_img is None:
            return None
        return list(self._raw_img.GetSize())

    def get_voxel_value_bound(self):
        return self._raw_img_stats['min_val'], self._raw_img_stats['max_val']

    def get_img_filepath(self, img_type):
        assert img_type in ['raw', 'anno']
        if img_type == 'raw':
            return '' if self._raw_img_filepath is None else self._raw_img_filepath
        if img_type == 'anno':
            return '' if self._anno_img_filepath is None else self._anno_img_filepath

    def is_valid(self):
        if self._raw_img is None:
            return False
        return True

    def get_anno_target_ids(self):
        return self._anno_img_stats['target_ids']

    def get_anno_num_labels(self):
        if self._anno_img_stats['num_positive_labels'] is None:
            return 0
        return self._anno_img_stats['num_positive_labels']

    def get_anno_target_centers_for_label(self, label=1):
        if self._anno_img_stats['target_labels'] is None:
            return []
        target_centers = []
        all_target_centers = self._anno_img_stats['target_centers']
        for i, target_label in enumerate(self._anno_img_stats['target_labels']):
            if target_label == label:
                target_centers.append(all_target_centers[i])
        return target_centers

    def anno_paint(self, x, y, z, axis, label, brush_type, brush_size, erase=False, new_step=False):
        if brush_type == BRUSH_TYPE_NO_BRUSH:
            return
        pos = [z, y, x]  # d, h, w
        anno_size = [self.get_size()[2], self.get_size()[1], self.get_size()[0]]
        for i in range(3):
            if pos[i] < 0 or pos[i] > anno_size[i] - 1:
                return
        size = [brush_size, brush_size, brush_size]  # d, h, w
        if axis == 'x':
            size[2] = 1
        if axis == 'y':
            size[1] = 1
        if axis == 'z':
            size[0] = 1
        paint_area_bbox = [[0, 0], [0, 0], [0, 0]]  # d, h, w. closed interval
        pos_in_paint_area = [0, 0, 0]
        for i in range(3):
            paint_area_bbox[i][0] = pos[i] - size[i] // 2
            paint_area_bbox[i][1] = paint_area_bbox[i][0] + size[i] - 1
            pos_in_paint_area[i] = pos[i] - paint_area_bbox[i][0]
            # boundary check
            if paint_area_bbox[i][0] < 0:
                pos_in_paint_area[i] += 0 - paint_area_bbox[i][0]
                paint_area_bbox[i][0] = 0
            if paint_area_bbox[i][1] > anno_size[i] - 1:
                paint_area_bbox[i][1] = anno_size[i] - 1

        paint_area_shape = [paint_area_bbox[0][1] - paint_area_bbox[0][0] + 1,
                            paint_area_bbox[1][1] - paint_area_bbox[1][0] + 1,
                            paint_area_bbox[2][1] - paint_area_bbox[2][0] + 1]
        new_paint_area_anno_img = np.zeros(paint_area_shape, self._anno_img_edit.dtype)
        if brush_type == BRUSH_TYPE_CIRCLE_BRUSH:
            indices_img = np.indices(new_paint_area_anno_img.shape).transpose([1, 2, 3, 0]).astype(np.float32)
            radius_img = np.linalg.norm(indices_img - pos_in_paint_area, axis=-1)
            new_paint_area_anno_img = np.where(2 * radius_img <= brush_size,
                                               label * np.ones(radius_img.shape, new_paint_area_anno_img.dtype),
                                               new_paint_area_anno_img)
        if brush_type == BRUSH_TYPE_RECT_BRUSH:
            new_paint_area_anno_img[:] = label

        paint_area_slice = (slice(paint_area_bbox[0][0], paint_area_bbox[0][1] + 1, 1),
                            slice(paint_area_bbox[1][0], paint_area_bbox[1][1] + 1, 1),
                            slice(paint_area_bbox[2][0], paint_area_bbox[2][1] + 1, 1))

        if new_step:
            self._anno_img_edit_undo_stack.append(self._anno_img_edit.copy())
            self._anno_img_edit_redo_stack.clear()

        if not erase:
            self._anno_img_edit[paint_area_slice] = np.where(new_paint_area_anno_img > 0,
                                                             new_paint_area_anno_img,
                                                             self._anno_img_edit[paint_area_slice]).copy()
        else:
            self._anno_img_edit[paint_area_slice] = np.where(
                np.logical_and(self._anno_img_edit[paint_area_slice] == label, new_paint_area_anno_img > 0),
                np.zeros(new_paint_area_anno_img.shape, self._anno_img_edit.dtype),
                self._anno_img_edit[paint_area_slice])
        self._anno_img_edit_change_flag = True

    def delete_target(self, target_id):
        if self._anno_img_edit_change_flag:
            raise ChangeNotSavedError('You must press the "Refresh" button for the target list before target deletion!')
        self._anno_img_edit_undo_stack.append(self._anno_img_edit.copy())
        self._anno_img_edit_redo_stack.clear()
        self._anno_img_edit = np.where(self._anno_img_stats['target_id_map'] == target_id,
                                       np.zeros(self._anno_img_edit.shape, self._anno_img_edit.dtype),
                                       self._anno_img_edit)

    def undo_paint(self):
        if len(self._anno_img_edit_undo_stack) > 0:
            self._anno_img_edit_redo_stack.append(self._anno_img_edit)
            self._anno_img_edit = self._anno_img_edit_undo_stack.pop()
            self._anno_img_edit_change_flag = True
            return True
        return False

    def redo_paint(self):
        if len(self._anno_img_edit_redo_stack) > 0:
            self._anno_img_edit_undo_stack.append(self._anno_img_edit)
            self._anno_img_edit = self._anno_img_edit_redo_stack.pop()
            self._anno_img_edit_change_flag = True
            return True
        return False
