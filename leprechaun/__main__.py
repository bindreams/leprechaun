import sys
from PySide2.QtWidgets import QApplication
from leprechaun.application import Application

def main():
    qapp = QApplication([])

    app = Application()
    app.start()

    return qapp.exec_()

if __name__ == "__main__":
    sys.exit(main())
