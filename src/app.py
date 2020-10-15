import sys

from PyQt5.QtWidgets import QApplication

from controller.main_window_controller import MainWindow


def main(argv):
    app = QApplication(argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main(sys.argv)
