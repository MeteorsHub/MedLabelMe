class IllegalSizeError(Exception):
    "check the image size"
    def __init__(self, new_size=None, reference_size=None):
        self.new_size = new_size
        self.reference_size = reference_size

    def __str__(self):
        msg = 'Illegal size!'
        if self.new_size is not None:
            msg += '\nnew size: %s' % self.new_size
        if self.reference_size is not None:
            msg += '\nreference size: %s' % self.reference_size
        return msg


class ImageTypeError(Exception):
    "check the image type"

    def __init__(self, img_type=None, preferred_img_type=None):
        self.img_type = img_type
        self.preferred_img_type = preferred_img_type

    def __str__(self):
        msg = 'Wrong image type!'
        if self.img_type is not None:
            msg += '\nimage type may be: %s' % self.img_type
        if self.preferred_img_type is not None:
            msg += '\npreferred image type: %s' % self.preferred_img_type
        return msg


class ChangeNotSavedError(Exception):
    """ check if the changed are saved """

    def __init__(self, description=None):
        if description is None:
            self.description = 'Change not saved!'
        else:
            self.description = description

    def __str__(self):
        return self.description
