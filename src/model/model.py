import os
import SimpleITK as sitk
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
