import sys
from PySide2.QtWidgets import QApplication
from leprechaun.application import Application

def main():
    """Special entry point from setup.py gui_scripts.

    Launch the GUI with pythonw in the background, thus removing all interaction with the command line.
    For this reason this function does not parse CLI args and redirects all logs to a separate file.
    Equivalent to running `pythonw.exe -m leprechaun -gp`

    See also https://stackoverflow.com/a/30313091/9118363
    """
    qapp = QApplication([])
    app = Application(pipe_log=True)

    app.start()
    return qapp.exec_()


if __name__ == "__main__":
    sys.exit(main())
