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
