import os

import SimpleITK as sitk
import numpy as np

from utils.exception_utils import IllegalSizeError


class Model:
    def __init__(self):
        self.raw_img = None
        self.anno_img = None
        self.raw_img_filepath = None
        self.anno_img_filepath = None
        self.last_wd = os.getcwd()

    def read_img(self, filepath, img_type):
        assert img_type in ['raw', 'anno']
        if not os.path.exists(filepath):
            raise FileNotFoundError('%s do not exist' % filepath)
        self.last_wd = os.path.dirname(filepath)
        if img_type == 'raw':
            self.raw_img = sitk.ReadImage(filepath)
            self.raw_img_filepath = filepath
            self.anno_img = None
            self.anno_img_filepath = None
        elif img_type == 'anno':
            self.anno_img = sitk.ReadImage(filepath)
            self.anno_img_filepath = filepath
            if self.anno_img.GetSize() != self.raw_img.GetSize():
                raise IllegalSizeError(self.anno_img.GetSize(), self.raw_img.GetSize())
            self.anno_img = None
            self.anno_img_filepath = None

    def get_2D_map(self, view, index, img_type='raw', low_bound=None, up_bound=None):
        assert view in ['a', 's', 'c']
        assert img_type in ['raw', 'anno']
        if index < 0:
            index = 0
        if img_type == 'raw':
            itk_img = self.raw_img
        if img_type == 'anno':
            itk_img = self.anno_img

        if itk_img is None:
            return None
        value_min, value_max = self.get_voxel_value_bound()
        if low_bound is None or low_bound < value_min:
            low_bound = value_min
        if up_bound is None or up_bound > value_max:
            up_bound = value_max
        img = self.get_raw_img_in_window(low_bound, up_bound, normalization=True)  # x, y, z

        if view == 'a':
            if index >= itk_img.GetSize()[2]:
                index = itk_img.GetSize()[2] - 1
            img_slice = img[:, :, index]

            return img_slice.copy()  # x, y
        if view == 's':
            if index >= itk_img.GetSize()[0]:
                index = itk_img.GetSize()[0] - 1
            img_slice = img[index, :, :]
            # import cv2
            # cv2.imshow('demo', img_slice)
            # cv2.waitKey(0)
            img_slice = np.array(img_slice, np.uint8)
            return img_slice.copy()  # y, z
        if view == 'c':
            if index >= itk_img.GetSize()[1]:
                index = itk_img.GetSize()[1] - 1
            img_slice = img[:, index, :]
            return img_slice.copy()  # x, z

    # @lru_cache(maxsize=2)
    def get_raw_img_in_window(self, low_bound, up_bound, normalization=False):
        if self.raw_img is None:
            return None
        img = sitk.GetArrayFromImage(self.raw_img)
        img = np.transpose(img, (2, 1, 0))  # d, h, w to w, h, d
        assert low_bound >= img.min() and up_bound <= img.max()
        img = np.clip(img, low_bound, up_bound)
        if normalization:
            img = (255 * (img.astype(np.float32) - low_bound) / (up_bound - low_bound)).astype(np.uint8)
        return img

    def get_size(self):
        if self.raw_img is None:
            return None
        return list(self.raw_img.GetSize())

    def get_voxel_value_bound(self):
        if self.raw_img is None:
            return None
        img = sitk.GetArrayFromImage(self.raw_img)
        return img.min(), img.max()
