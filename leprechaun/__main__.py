import sys
from PySide2.QtWidgets import QApplication
import leprechaun as le

def main():
    qapp = QApplication([])

    app = le.Application()
    app.start()

    return qapp.exec_()

if __name__ == "__main__":
    sys.exit(main())
