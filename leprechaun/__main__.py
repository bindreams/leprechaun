import sys
from PySide2.QtGui import QIcon
from PySide2.QtWidgets import QStyleFactory
import leprechaun as package
from leprechaun.application import Application

def main():
    app = Application()
    return app.exec()

if __name__ == "__main__":
    sys.exit(main())
