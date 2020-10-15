import os
import sys
from utils.python_utils import str2bool


def update_all_ui_files(path, recursive=True):
    if not os.path.exists(path):
        return
    for item in os.listdir(path):
        item_path = os.path.join(path, item)
        if os.path.isdir(item_path):
            if recursive:
                update_all_ui_files(item_path, recursive)
        else:
            if os.path.splitext(item_path)[1] == '.ui':
                new_item_path = item_path.replace('.ui', '_ui.py')
                cmd = 'python -m PyQt5.uic.pyuic %s -o %s' % (item_path, new_item_path)
                os.system(cmd)


if __name__ == '__main__':
    if len(sys.argv) == 1:
        update_all_ui_files(os.getcwd())
    elif len(sys.argv) == 2:
        update_all_ui_files(sys.argv[1])
    elif len(sys.argv) == 3:
        update_all_ui_files(sys.argv[1], str2bool(sys.argv[2]))
    else:
        raise AttributeError('unsupported argv: %s' % sys.argv)
