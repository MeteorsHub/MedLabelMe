import sys
import traceback

from PyQt5.QtWidgets import QApplication, QMessageBox

from controller.main_window_controller import MainWindow


def main(argv):
    sys.excepthook = error_handler

    app = QApplication(argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec_())


def error_handler(etype, value, tb):
    error_msg = ''.join(traceback.format_exception(etype, value, tb))
    error_msg = 'please capture a screenshot and contact the developer：\n' + error_msg
    QMessageBox.critical(None, 'Error', error_msg)


if __name__ == '__main__':
    main(sys.argv)
